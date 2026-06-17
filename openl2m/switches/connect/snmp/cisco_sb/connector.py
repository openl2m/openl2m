#
# This file is part of Open Layer 2 Management (OpenL2M).
#
# OpenL2M is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with OpenL2M. If not, see <http://www.gnu.org/licenses/>.
#
"""
Cisco Small Business (SB) devices specific implementation of the SNMP Connection object.
This augments/re-implements some methods found in the Cisco SNMP() class
located in switches/connect/snmp/cisco/connector.py
with Cisco-SB specific ways of doing things...
"""

import traceback

# from django.conf import settings
from django.http.request import HttpRequest

from pysnmp.proto.rfc1902 import Integer, OctetString

from switches.constants import LOG_TYPE_ERROR, LOG_SAVE_SWITCH
from switches.models import Switch, SwitchGroup
from switches.connect.classes import Interface, PortList, Transceiver
from switches.connect.constants import IF_TYPE_ETHERNET
from switches.connect.connector import Connector
from switches.connect.snmp.connector import pysnmpHelper, SnmpConnector, oid_in_branch, dot1qPvid
from switches.connect.snmp.constants import dot1qVlanStaticName, dot1qVlanStaticRowStatus, vlan_createAndGo

# from switches.connect.snmp.constants import dot1qVlanStaticEgressPorts, dot1qVlanStaticUntaggedPorts, dot1qVlanForbiddenEgressPorts
from switches.connect.snmp.cisco.connector import SnmpConnectorCisco
from switches.utils import dprint

from .constants import (
    vlanPortModeState,
    vlanAccessPortModeVlanId,
    vlanTrunkPortModeNativeVlanId,
    vlanTrunkModeList1to1024,
    vlanTrunkModeList1025to2048,
    vlanTrunkModeList2049to3072,
    vlanTrunkModeList3073to4094,
    swIfTransceiverType,
    SB_VLAN_MODE_GENERAL,
    SB_VLAN_MODE_ACCESS,
    SB_VLAN_MODE_TRUNK,
    SB_TX_TYPE_COPPER,
    sb_tx_type,
    createAndGo,
    rlCopyRowStatus,
    local,
    rlCopySourceLocation,
    runningConfig,
    rlCopySourceFileType,
    rlCopyDestinationLocation,
    startupConfig,
    rlCopyDestinationFileType,
)

from .utils import get_if_mode_name


class SnmpConnectorCiscoSB(SnmpConnectorCisco):
    """
    CISCO Small Business devices specific implementation of the base SNMP class.
    We override various functions as needed for the Cisco way of doing things.
    """

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        # for now, just call the super class
        dprint("SnmpConnectorCiscoSB().__init__()")
        super().__init__(request, group, switch)
        self.description = "Cisco SB SNMP driver"
        self.vendor_name = "Cisco (SB)"

        # capabilities of the Cisco-SB snmp drivers:
        self.can_edit_vlans = False  # only rename and delete are support, so False for now...
        self.can_edit_tags = True  # this driver can edit 802.1q tagged vlans on interfaces
        self.can_save_config = True  # do we have the ability (or need) to execute a 'save config' or 'write memory' ?
        """
        # capabilities of the Cisco snmp driver are identical to the snmp driver:
        self.can_change_admin_status = True
        self.can_change_vlan = True
        self.can_change_poe_status = True
        self.can_change_description = True
        self.can_reload_all = True      # if true, we can reload all our data (and show a button on screen for this)
        """

        # Netmiko is used for SSH connections. Here are some defaults a class can set.
        #
        # device_type:
        # if set, will be a value that will override (ie. hardcode) values from the
        # "Credentials Profile" (aka the NetmikoProfile() object)
        self.netmiko_device_type = "cisco_ios"
        # if netmiko_device_type is not set, the netmiko_valid_device_types is a  list()
        # with the valid device_type choices a driver should allow in the
        # "Credentials Profile". Any other value will trigger an error, and fail the SSH connection.
        self.netmiko_valid_device_types = ["cisco_ios"]
        # the command that should be sent to disable screen paging
        # let Netmiko decide this...
        # self.netmiko_disable_paging_command = "terminal length 0"

        # Small Business devices (newer style) use the 'standard' Q-Bridge mibs. We will use this when we read vlan data.
        # see self._get_vlan_data() below.
        self.add_more_info(category="System", name="Hw Type", value="Cisco Small Business")

    def _get_interface_data(self) -> bool:
        """
        Implement an override of the interface parsing routine,
        so we can add Cisco specific interface MIBs
        """
        dprint("SnmpConnectorCiscoSB()._get_interface_data()")
        # first call the base class to populate interfaces:
        super()._get_interface_data()

        # now add Cisco data, and cache it:
        if self.get_snmp_branch(branch_name="cL2L3IfModeOper", parser=self._parse_mibs_cisco_if_opermode) < 0:
            dprint("Cisco cL2L3IfModeOper returned error!")
            return False

        return True

    def _get_vlan_data(self) -> int:
        """
        Read the CiscoSB-Vlan MIB to get all neccesary vlan info (names, id, ports on vlans, etc.) from the switch.
        Returns -1 on error, or number to indicate vlans found.
        """
        dprint("SnmpConnectorCiscoSB()._get_vlan_data()")

        # first read standard SNMP Q-Bridge mib for vlan data.
        # pylint: disable=protected-access
        SnmpConnector._get_vlan_data(self=self)

        # we could probe "vlanNameTable" as well...

        # go probe the CiscoSB-VLAN mib for the port mode, ie access or trunk
        self.get_snmp_branch(branch_name="vlanPortModeState", parser=self._parse_mibs_sb_vlan_port_mode)

        # and then read the vlanAccessPortModeVlanId, this reads access mode vlan id's
        self.get_snmp_branch(branch_name="vlanAccessPortModeVlanId", parser=self._parse_mibs_sb_access_vlan)

        # and finally read trunk mode PVID and tagged vlans as well:
        self.get_snmp_branch(branch_name="vlanTrunkPortModeEntry", parser=self._parse_mibs_sb_trunk_vlan)

        # and parse the transceiver type, if any
        self.get_snmp_branch(branch_name="swIfTransceiverType", parser=self._parse_mibs_sb_port_transceiver_type)

        # set vlan count
        self.vlan_count = len(self.vlans)

        return self.vlan_count

    def _get_interface_transceiver_types(self) -> int:
        """
        Augment SnmpConnector._get_interface_transceiver_type() to read more transceiver info of a physical port
        from an Cisco-specific MIB called CISCO-STACK-MIB. Mostly in older Catalyst switches.

        Returns 1 on succes, -1 on failure
        """
        dprint("SnmpConnectorCiscoSB()._get_interface_transceiver_types()")
        super()._get_interface_transceiver_types()
        # note: we have already read 'portIfIndex' in _get_poe_data().
        # this maps stack-id's to ifIndex.
        # only load portType if we found stack-id mappings.
        if len(self.stack_port_to_if_index) > 0:
            # now read Cisco data, first the "portType" branch to find interesting types by 'stack id'
            retval = self.get_snmp_branch(branch_name="ciscoPortType", parser=self._parse_mibs_cisco_port_type)
            if retval < 0:
                self.add_warning("Error getting Transceiver data (ciscoPortType)'")
                return retval
        return 1

    def _get_known_ethernet_addresses(self) -> bool:
        """
        Read known ethernet address on the switch. SB devices are 'standard' snmp,
        so call that connector (ie. Skip the SnmpConnectorCisco() object)

        Return True on success (0 or more found), False on errors
        """
        dprint("SnmpConnectorCiscoSB()._get_known_ethernet_addresses()")
        # pylint: disable=protected-access
        return SnmpConnector._get_known_ethernet_addresses(self=self)

    def set_interface_untagged_vlan(self, interface: Interface, new_vlan_id: int) -> bool:
        """
        Implement VLAN change for new style Cisco SB devices. Method depends on interface mode.

        Returns True or False
        """
        dprint("SnmpConnectorCiscoSB().set_interface_untagged_vlan()")

        if not interface:
            # interface not found (should not happen!)
            self.error.status = True
            self.error.description = "interface not found!"
            self.error.details = "Invalid call to set_interface_untagged_vlan(): interface parameter not set!"
            return False

        if interface.if_vlan_mode == SB_VLAN_MODE_GENERAL:
            # we set the dot1qPvid value:
            dprint("  SB_VLAN_MODE_GENERAL - setting with dot1qPvid:")
            if not self.set(
                oid=f"{dot1qPvid}.{interface.port_id}",
                value=int(new_vlan_id),
                snmp_type="u",
                parser=self._parse_mibs_vlan_related,
            ):
                return False
            return True

        if interface.if_vlan_mode == SB_VLAN_MODE_ACCESS:
            # we set the vlanAccessPortModeVlanId value:
            dprint("  SB_VLAN_MODE_ACCESS - setting with vlanAccessPortModeVlanId:")
            if not self.set(
                oid=f"{vlanAccessPortModeVlanId}.{interface.port_id}",
                value=int(new_vlan_id),
                snmp_type="u",
                parser=self._parse_mibs_sb_access_vlan,
            ):
                interface.untagged_vlan = new_vlan_id
                return False
            return True

        if interface.if_vlan_mode == SB_VLAN_MODE_TRUNK:
            dprint("  SB_VLAN_MODE_TRUNK")
            # we set the vlanTrunkPortModeNativeVlanId value:
            dprint("  SB_VLAN_MODE_TRUNK - setting with vlanTrunkPortModeNativeVlanId:")
            if not self.set(
                oid=f"{vlanTrunkPortModeNativeVlanId}.{interface.port_id}",
                value=int(new_vlan_id),
                snmp_type="u",
                parser=self._parse_mibs_sb_trunk_vlan,
            ):
                interface.untagged_vlan = new_vlan_id
                return False
            return True

        # for now error out
        self.error.status = True
        self.error.description = (
            f"Port mode '{get_if_mode_name(mode=interface.if_vlan_mode)}' - Set vlan not implemented for SB devices!"
        )
        self.error.details = "We cannot yet handle SB devices!"
        return False

    def set_interface_vlans(
        self, interface: Interface, untagged_vlan: int, tagged_vlans: list[int], allow_all: bool = False
    ) -> bool:
        """
        Set the interface to the untagged and tagged vlans. This is done the 'normal' SNMP way.
        So call the SnmpConnector(), bypassing the SnmpConnectorCisco()

        Args:
            interface = Interface() object for the requested port
            untagged_vlan = an integer with the requested untagged vlan
            tagged_vlans = a List() of integer vlan id's that should be allowed as 802.1q tagged vlans.

        Returns:
            True on success, False on error and set self.error variables
        """
        dprint(
            f"SnmpConnectorCiscoSB().set_interface_vlans() for {interface.name} to untagged {untagged_vlan}, tagged {tagged_vlans}, allow_all={allow_all}"
        )
        if allow_all or len(tagged_vlans):
            dprint(" TAGGED MODE!")
            # set trunk mode
            success = self._set_if_mode(interface=interface, mode=SB_VLAN_MODE_TRUNK)
            if success:
                # set untagged vlan
                success = self.set_interface_untagged_vlan(interface=interface, new_vlan_id=untagged_vlan)
                if success:
                    dprint(" PVID set OK")
                    # now add tagged vlans
                    # as Cisco-SB maps interface to vlan list, we need 4 PortList() objects to represent the Vlan bitmaps
                    # a bit for each of the 1024 vlans per entry, ie 1024 / 8 = 128 bytes!
                    vlans1to1024 = PortList()
                    vlans1to1024.from_byte_count(128)  # initialize with "00" bytes, ie NO vlan set as tagged!
                    vlans1025to2048 = PortList()
                    vlans1025to2048.from_byte_count(128)
                    vlans2049to3072 = PortList()
                    vlans2049to3072.from_byte_count(128)
                    vlans3073to4094 = PortList()
                    vlans3073to4094.from_byte_count(128)
                    # now set bit to 1 for each vlan on this interface
                    for vlan_id in self.vlans:
                        if allow_all or vlan_id in tagged_vlans:
                            dprint(f"  VLAN {vlan_id}: ADD as tagged")
                            if vlan_id < 1025:
                                # Note: bit 0 is vlan 1, but PortList() already offsets by -1, so offset by +1
                                vlans1to1024[vlan_id] = 1
                            elif vlan_id < 2049:
                                # subtract base to get to vlan offset in range 1025-2048
                                vlans1025to2048[vlan_id - 1024] = 1
                            elif vlan_id < 3073:
                                # subtract base to get to vlan offset in range 2049-3072
                                vlans2049to3072[vlan_id - 2048] = 1
                            else:
                                # subtract base to get to vlan offset in range 3073-4094
                                vlans3073to4094[vlan_id - 3073] = 1
                        else:
                            dprint(f"  VLAN {vlan_id} REMOVED as tagged")

                    # prepare into OctetString objects for writing snmp:
                    oid1 = (
                        f"{vlanTrunkModeList1to1024}.{interface.index}",
                        OctetString(hexValue=vlans1to1024.to_hex_string()),
                    )
                    oid2 = (
                        f"{vlanTrunkModeList1025to2048}.{interface.index}",
                        OctetString(hexValue=vlans1025to2048.to_hex_string()),
                    )
                    oid3 = (
                        f"{vlanTrunkModeList2049to3072}.{interface.index}",
                        OctetString(hexValue=vlans2049to3072.to_hex_string()),
                    )
                    oid4 = (
                        f"{vlanTrunkModeList3073to4094}.{interface.index}",
                        OctetString(hexValue=vlans3073to4094.to_hex_string()),
                    )

                    # now write these to the device:
                    try:
                        pysnmp = pysnmpHelper(self.switch)
                    except Exception as err:
                        self.error.status = True
                        self.error.description = "Error getting snmp connection object (pysnmpHelper()) for set_access_mode_vlan on '{interface.name}'"
                        self.error.details = f"Caught Error: {repr(err)} ({str(type(err))})\n{traceback.format_exc()}"
                        return False

                    dprint("Setting via pysnmpHelper()")
                    if not pysnmp.set_multiple([oid1, oid2, oid3, oid4]):
                        self.error.status = True
                        self.error.description = f"Error setting vlans on tagged port '{interface.name}'!"
                        # copy over the error details from the call:
                        self.error.details = pysnmp.error.details
                        # we leave self.error.details as is!
                        return False

                    # # call the SnmpConnector() to handle regular Q-Bridge port vlan setting:
                    # This should be used for GENERAL-MODE interface, which we at present don't support.
                    #
                    # success = self.set_interface_tagged_vlans(interface=interface, tagged_vlans=tagged_vlans, allow_all=allow_all)
                    # if success:
                    #     # do the bookkeeping
                    #     return Connector.set_interface_vlans(
                    #         self=self,
                    #         interface=interface,
                    #         untagged_vlan=untagged_vlan,
                    #         tagged_vlans=tagged_vlans,
                    #         allow_all=allow_all,
                    #     )

                    # all vlan sets succeeded! Do the bookkeeping
                    return Connector.set_interface_vlans(
                        self=self,
                        interface=interface,
                        untagged_vlan=untagged_vlan,
                        tagged_vlans=tagged_vlans,
                        allow_all=allow_all,
                    )

        else:
            dprint("  ACCESS MODE!")
            # set access mode
            success = self._set_if_mode(interface=interface, mode=SB_VLAN_MODE_ACCESS)
            if success:
                # set the untagged vlan
                success = self.set_interface_untagged_vlan(interface=interface, new_vlan_id=untagged_vlan)
                if success:
                    # do the bookkeeping
                    return Connector.set_interface_vlans(
                        self=self,
                        interface=interface,
                        untagged_vlan=untagged_vlan,
                        tagged_vlans=tagged_vlans,
                        allow_all=allow_all,
                    )

        # we are now in an unknown state!
        return False

    def save_running_config(self) -> bool:
        """
        Cisco-SB save the current config to startup. Method is mostly identical to 'regular' Cisco,
        but uses different SNMP OIDs.
        Returns True is this succeeds, False on failure. self.error() will be set in that case
        """
        dprint("SnmpConnectorCiscoSB().save_running_config()")

        # we use the CISCOSB-COPY-MIB for this
        # https://github.com/librenms/librenms/blob/master/mibs/cisco/CISCOSB-MIB
        # this is described at
        # https://www.cisco.com/c/en/us/support/docs/smb/switches/Catalyst-switches/kmgmt3810-triggering-configuration-file-copies-to-tftp-server-via-snmp.html
        # and
        # https://community.cisco.com/t5/switches-small-business/how-to-save-config-through-snmp/td-p/1667917
        # (the latter has old pre-Cisco OIDs !)

        # this needs to be an "atomic" set of actions
        oid_values = [
            (f"{rlCopyRowStatus}.1", createAndGo, "i"),  # create new "config row"
            (f"{rlCopySourceLocation}.1", local, "i"),  # set source of copy to local running-config
            (f"{rlCopySourceFileType}.1", runningConfig, "i"),
            (f"{rlCopyDestinationLocation}.1", local, "i"),  # set destination to local startup-config
            (f"{rlCopyDestinationFileType}.1", startupConfig, "i"),
        ]
        # go execute the set of actions:
        if self.set_multiple(oid_values=oid_values):
            return True

        dprint("ERROR Caught in set_multiple()!")
        self.error.description = "Save running-config returned error!"
        self.add_log(
            type=LOG_TYPE_ERROR, action=LOG_SAVE_SWITCH, description=f"{self.error.description} - {self.error.details}"
        )
        return False

    def _set_if_mode(self, interface: Interface, mode: int):
        """Set an interface to a specific mode (ie ACCESS, TRUNK)
           We use the vlanPortModeState entry in the CISCOSB-vlan-MIB to manipulate the port mode

        Params:
            interface: the Interface() object to modify
            mode: the mode to set

        Returns:
            (bool): True on success, False on error. Will set self.error() as needed.
        """
        dprint(f"SnmpConnectorCiscoSB()._set_if_mode() for {interface.name} to mode {mode}")
        success = self.set(f"{vlanPortModeState}.{interface.index}", value=mode, snmp_type="i")
        if success:
            dprint("  Mode set OK")
            interface.if_vlan_mode = mode
            return True
        return False

    def _parse_mibs_sb_vlan_port_mode(self, oid: str, val: str) -> bool:
        """
        Parse CiscoSB-Vlan Port Mode, ie access, trunk, general.
        """
        if_index = oid_in_branch(vlanPortModeState, oid)
        if if_index:
            dprint(f"FOUND: vlanPortModeState for index {if_index} = {val} ({get_if_mode_name(mode=int(val))})")
            iface = self.get_interface_by_key(key=if_index)
            if iface:
                mode = int(val)
                iface.if_vlan_mode = mode
                # if ACCESS mode, clear out any vlans we have found from Q-Bridge,as they are not valid.
                if mode == SB_VLAN_MODE_ACCESS:
                    iface.is_tagged = False
                    iface.vlans = []
                elif mode == SB_VLAN_MODE_TRUNK:
                    iface.is_tagged = True
                    iface.vlans = []  # clear out from Q-Bridge, as we are about to read vlanTrunkModeList1to1024, etc.
                else:
                    dprint(f"  WARNING: cannot handle mode {mode} !")
            return True  # parsed

        return False  # not parsed.

    def _parse_mibs_sb_access_vlan(self, oid: str, val: str) -> bool:
        """Parse the Access Mode port untagged vlan"""
        if_index = oid_in_branch(vlanAccessPortModeVlanId, oid)
        if if_index:
            dprint(f"FOUND: vlanAccessPortModeVlanId for index {if_index} = {val}")
            # untagged_vlan = int(val)
            # only set if port is in "Access Mode"
            iface = self.get_interface_by_key(key=if_index)
            if iface.if_vlan_mode == SB_VLAN_MODE_ACCESS:
                iface.untagged_vlan = int(val)
            return True  # parsed

        return False  # not parsed.

    def _parse_mibs_sb_trunk_vlan(self, oid: str, val: str) -> bool:
        """Parse the Trunk Mode port untagged vlan"""
        if_index = oid_in_branch(vlanTrunkPortModeNativeVlanId, oid)
        if if_index:
            dprint(f"FOUND: vlanTrunkPortModeNativeVlanId for index {if_index} = {val}")
            # untagged_vlan = int(val)
            # only set if port is in "Access Mode"
            iface = self.get_interface_by_key(key=if_index)
            if iface.if_vlan_mode == SB_VLAN_MODE_TRUNK:
                iface.untagged_vlan = int(val)
            return True  # parsed

        if_index = oid_in_branch(vlanTrunkModeList1to1024, oid)
        if if_index:
            dprint(f"FOUND: vlanTrunkModeList1to1024 for index {if_index} = {val}")
            iface = self.get_interface_by_key(key=if_index)
            if iface.if_vlan_mode == SB_VLAN_MODE_TRUNK:
                # data is only valid in trunk mode!
                # now parse the bitmap. Note the bit place values are vlan indexes, NOT vlan ID!!!
                dprint("   BITMAP to parse here!")
                # note this is offset by 1 to count valid vlan id's
                self._cisco_parse_vlan_bitmap(val=val, vlan_base=1, iface=iface)
            return True  # parsed

        if_index = oid_in_branch(vlanTrunkModeList1025to2048, oid)
        if if_index:
            dprint(f"FOUND: vlanTrunkModeList1025to2048 for index {if_index} = {val}")
            iface = self.get_interface_by_key(key=if_index)
            if iface.if_vlan_mode == SB_VLAN_MODE_TRUNK:
                # data is only valid in trunk mode!
                # now parse the bitmap. Note the bit place values are vlan indexes, NOT vlan ID!!!
                dprint("   BITMAP to parse here!")
                # note this is offset by 1 to count valid vlan id's
                self._cisco_parse_vlan_bitmap(val=val, vlan_base=1025, iface=iface)
            return True  # parsed

        if_index = oid_in_branch(vlanTrunkModeList2049to3072, oid)
        if if_index:
            dprint(f"FOUND: vlanTrunkModeList2049to3072 for index {if_index} = {val}")
            iface = self.get_interface_by_key(key=if_index)
            if iface.if_vlan_mode == SB_VLAN_MODE_TRUNK:
                # data is only valid in trunk mode!
                # now parse the bitmap. Note the bit place values are vlan indexes, NOT vlan ID!!!
                dprint("   BITMAP to parse here!")
                # note this is offset by 1 to count valid vlan id's
                self._cisco_parse_vlan_bitmap(val=val, vlan_base=2049, iface=iface)
            return True  # parsed

        if_index = oid_in_branch(vlanTrunkModeList3073to4094, oid)
        if if_index:
            dprint(f"FOUND: vlanTrunkModeList3073to4094 for index {if_index} = {val}")
            iface = self.get_interface_by_key(key=if_index)
            if iface.if_vlan_mode == SB_VLAN_MODE_TRUNK:
                # data is only valid in trunk mode!
                # now parse the bitmap. Note the bit place values are vlan indexes, NOT vlan ID!!!
                dprint("   BITMAP to parse here!")
                # note this is offset by 1 to count valid vlan id's
                self._cisco_parse_vlan_bitmap(val=val, vlan_base=3073, iface=iface)
            return True  # parsed

        return False  # not parsed.

    def _parse_mibs_sb_port_transceiver_type(self, oid: str, val: str) -> bool:
        """
        Parse CiscoSB-rlInterfaces Port transceiver type
        """

        if_index = oid_in_branch(swIfTransceiverType, oid)
        if if_index:
            dprint(f"FOUND: swIfTransceiverType for index {if_index} = {val}")
            # only set data for optical or combo transceiver ports:
            if int(val) != SB_TX_TYPE_COPPER:
                iface = self.get_interface_by_key(key=if_index)
                if iface:
                    if not iface.transceiver:
                        iface.transceiver = Transceiver()
                    iface.transceiver.type = sb_tx_type[int(val)]
            return True  # parsed

        return False  # not parsed.

    def _can_manage_interface(self, interface: Interface):
        """Called to override if this interface can be managed...
        For Cisco-SB devices, we can now handle untagged and 802.1q interfaces,
        but we're not sure what to do with other modes...

        Params:
            iface (Interface): the Interface() object to check management of.

        Returns:
            (bool): True is management allowed, False if not.

        """
        dprint(f"SnmpConnectorCiscoSB()._can_manage_interface() for interface {interface.name}")
        if interface.type == IF_TYPE_ETHERNET and interface.if_vlan_mode not in (
            SB_VLAN_MODE_ACCESS,
            SB_VLAN_MODE_TRUNK,
        ):
            # we cannot manage this yet, so disable for now:
            dprint("  -> NO!")
            interface.manageable = False
            interface.unmanage_reason = f"On Cisco SB devices, mode '{get_if_mode_name(mode=interface.if_vlan_mode)}' interface is not manageable!"
            return False

        return True

    #
    # NOT FUNCTIONAL YET !
    #
    # This is custom implementation, as the generic SnmpConnector.vlan_create() fails.
    #
    def vlan_create(self, vlan_id: int, vlan_name: str) -> bool:
        """
        Create a new vlan on this device. Upon success, this then needs to call the base class for book keeping!

        Note: this uses SNMP dot1qVlanStaticRowStatus set to createAndGo(4). This should work on most devices
        that implement the Q-Bridge MIB. However, some devices may need to set createAndWait(5). If your device
        needs a different sequency, please override this function in your device driver!

        Args:
            vlan_id (int): the vlan id
            vlan_name (str): the name of the vlan

        Returns:
            True on success, False on error and set self.error variables.
        """
        dprint(f"SnmpConnectorCiscoSB().vlan_create() for {vlan_id} = '{vlan_name}'")

        # # this is atomic multi-set action. Full tuples with (OID, value, type) calling ezsnmp
        # # Cisco_SB switches appear to want the full 'matrix' or array of entries when creating a new vlan:
        oid1 = (f"{dot1qVlanStaticRowStatus}.{vlan_id}", vlan_createAndGo, "i")
        oid2 = (f"{dot1qVlanStaticName}.{vlan_id}", vlan_name, "s")
        # oid3 = (f"{dot1qVlanStaticEgressPorts}.{vlan_id}", OctetString(), ""
        # oid4 = (f"{dot1qVlanForbiddenEgressPorts}.{vlan_id}",
        # oid5 = (f"{dot1qVlanStaticUntaggedPorts}.{vlan_id}",

        # if not self.set_multiple(oid_values=[oid1, oid2, oid3, oid4, oid5]):
        # # if not self.set_multiple(oid_values=[oid1]):
        # # if not self.set(oid=f"{dot1qVlanStaticRowStatus}.{vlan_id}", value=5, snmp_type="i"):
        #     # we leave self.error.details as is!
        #     return False

        oid1 = (f"{dot1qVlanStaticRowStatus}.{vlan_id}", Integer(vlan_createAndGo))
        oid2 = (f"{dot1qVlanStaticName}.{vlan_id}", str(vlan_name))
        # oid3 = (f"{dot1qVlanStaticEgressPorts}.{vlan_id}", OctetString())
        # oid4 = (f"{dot1qVlanForbiddenEgressPorts}.{vlan_id}", OctetString())
        # oid5 = (f"{dot1qVlanStaticUntaggedPorts}.{vlan_id}", OctetString())

        # now write these to the device:
        try:
            pysnmp = pysnmpHelper(self.switch)
        except Exception as err:
            self.error.status = True
            self.error.description = "Error getting snmp connection object (pysnmpHelper()) for vlan_create()"
            self.error.details = f"Caught Error: {repr(err)} ({str(type(err))})\n{traceback.format_exc()}"
            return False

        dprint("Setting via pysnmpHelper()")
        try:
            # if not pysnmp.set_multiple([oid1, oid2, oid3, oid4, oid5]):
            if not pysnmp.set_multiple([oid1, oid2]):
                self.error.status = True
                self.error.description = "Error creating vlan!"
                # copy over the error details from the call:
                self.error.details = pysnmp.error.details
                # we leave self.error.details as is!
                return False
        except Exception as err:
            dprint(f"ERROR in pysnmp: {err}")
            self.error.status = True
            self.error.description = err
            self.error.details = ""
            return False

        # all OK, now do the book keeping
        return Connector.vlan_create(self=self, vlan_id=vlan_id, vlan_name=vlan_name)

    #
    # This works!
    # This is handled by the standard SnmpConnector() implementation, bypassing SnmpConnectorCiso()
    #
    def vlan_edit(self, vlan_id: int, vlan_name: str) -> bool:
        """
        Edit the vlan name. Upon success, this then needs to call the base class for book keeping!

        Args:
            vlan_id (int): the vlan id to edit
            vlan_name (str): the new name of the vlan

        Returns:
            True on success, False on error and set self.error variables.
        """
        return SnmpConnector.vlan_edit(self=self, vlan_id=vlan_id, vlan_name=vlan_name)

    #
    # This works!
    # This is handled by the standard SnmpConnector() implementation, bypassing SnmpConnectorCiso()
    #
    def vlan_delete(self, vlan_id: int) -> bool:
        """
        Deletel the vlan. Upon success, this then needs to call the base class for book keeping!

        Args:
            vlan_id (int): the vlan id to edit

        Returns:
            True on success, False on error and set self.error variables.
        """
        return SnmpConnector.vlan_delete(self=self, vlan_id=vlan_id)
