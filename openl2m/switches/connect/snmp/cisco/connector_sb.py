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
with Cisco-SB specific ways of doing things...
"""

# from django.conf import settings
from django.http.request import HttpRequest

from switches.models import Switch, SwitchGroup
from switches.connect.classes import Interface, Transceiver
from switches.connect.snmp.connector import dot1qPvid
from switches.connect.snmp.connector import oid_in_branch
from switches.utils import dprint

from switches.connect.snmp.connector import SnmpConnector
from .connector import SnmpConnectorCisco

from .constants import (
    SB_VLAN_MODE_GENERAL,
    SB_VLAN_MODE_ACCESS,
    SB_VLAN_MODE_TRUNK,
    sb_vlan_mode,
    vlanPortModeState,
    vlanAccessPortModeVlanId,
    vlanTrunkPortModeNativeVlanId,
    swIfTransceiverType,
    SB_TX_TYPE_COPPER,
    sb_tx_type,
)


class SnmpConnectorCiscoSB(SnmpConnectorCisco):
    """
    CISCO Small Business devices specific implementation of the base SNMP class.
    We override various functions as needed for the Cisco way of doing things.
    """

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        # for now, just call the super class
        dprint("SnmpConnectorCiscoSB().__init__")
        super().__init__(request, group, switch)
        self.description = "Cisco SB SNMP driver"
        self.vendor_name = "Cisco (SB)"

        # capabilities of the Cisco snmp drivers:
        self.can_edit_vlans = False
        self.can_save_config = True  # do we have the ability (or need) to execute a 'save config' or 'write memory' ?
        """
        # capabilities of the Cisco snmp driver are identical to the snmp driver:
        self.can_change_admin_status = True
        self.can_change_vlan = True
        self.can_change_poe_status = True
        self.can_change_description = True
        self.can_reload_all = True      # if true, we can reload all our data (and show a button on screen for this)
        """
        self.can_save_config = False

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

        # go probe the CiscoSB-VLAN mib
        retval = self.get_snmp_branch(branch_name="vlanPortModeState", parser=self._parse_mibs_sb_vlan_port_mode)
        if retval < 0:
            return retval

        # and parse the transceiver type, if any
        retval = self.get_snmp_branch(
            branch_name="swIfTransceiverType", parser=self._parse_mibs_sb_port_transceiver_type
        )
        if retval < 0:
            return retval

        # read and return standard SNMP Q-Bridge mib for vlan data.
        # THIS NEEDS WORK!
        SnmpConnector._get_vlan_data(self=self)

        # and finally read the vlanAccessPortModeVlanId, this reads access mode vlan id's
        retval = self.get_snmp_branch(branch_name="vlanAccessPortModeVlanId", parser=self._parse_mibs_sb_access_vlan)
        if retval < 0:
            return retval

        # and read trunk mode PVID as well:
        retval = self.get_snmp_branch(
            branch_name="vlanTrunkPortModeNativeVlanId", parser=self._parse_mibs_sb_trunk_vlan
        )
        if retval < 0:
            return retval

        # set vlan count
        self.vlan_count = len(self.vlans)

        return self.vlan_count

    def _get_interface_transceiver_types(self) -> int:
        """
        Augment SnmpConnector._get_interface_transceiver_type() to read more transceiver info of a physical port
        from an Cisco-specific MIB called CISCO-STACK-MIB. Mostly in older Catalyst switches.

        Returns 1 on succes, -1 on failure
        """
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
            # we set the vlanAccessPortModeVlanId value:
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
            f"Port mode {sb_vlan_mode[interface.if_vlan_mode]} - Set vlan not implemented for SB devices!"
        )
        self.error.details = "We cannot yet handle SB devices!"
        return False

    def _parse_mibs_sb_vlan_port_mode(self, oid: str, val: str) -> bool:
        """
        Parse CiscoSB-Vlan Port Mode, ie access, trunk, general.
        """
        if_index = oid_in_branch(vlanPortModeState, oid)
        if if_index:
            dprint(f"FOUND: vlanPortModeState for index {if_index} = {val}")
            self.set_interface_attribute_by_key(if_index, "if_vlan_mode", int(val))
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

    def _parse_mibs_sb_access_vlan(self, oid: str, val: str) -> bool:
        """Parse the Access Mode port untagged vlan"""
        if_index = oid_in_branch(vlanAccessPortModeVlanId, oid)
        if if_index:
            dprint(f"FOUND: vlanAccessPortModeVlanId for index {if_index} = {val}")
            # untagged_vlan = int(val)
            # only set if port is in "Access Mode"
            intf = self.get_interface_by_key(key=if_index)
            if intf.if_vlan_mode == SB_VLAN_MODE_ACCESS:
                self.set_interface_attribute_by_key(if_index, "untagged_vlan", int(val))
            return True  # parsed

        return False  # not parsed.

    def _parse_mibs_sb_trunk_vlan(self, oid: str, val: str) -> bool:
        """Parse the Trunk Mode port untagged vlan"""
        if_index = oid_in_branch(vlanTrunkPortModeNativeVlanId, oid)
        if if_index:
            dprint(f"FOUND: vlanTrunkPortModeNativeVlanId for index {if_index} = {val}")
            # untagged_vlan = int(val)
            # only set if port is in "Access Mode"
            intf = self.get_interface_by_key(key=if_index)
            if intf.if_vlan_mode == SB_VLAN_MODE_TRUNK:
                self.set_interface_attribute_by_key(if_index, "untagged_vlan", int(val))
            return True  # parsed

        return False  # not parsed.

    def _can_manage_interface(self, interface: Interface):
        """Called to override if this interface can be managed...
        For Cisco-SB devices, disable TRUNK (802.1q) port management for now.
        since we cannot change the PVID for it yet.

        Params:
            iface (Interface): the Interface() object to check management of.

        Returns:
            (bool): True is management allowed, False if not.

        """
        dprint(f"SnmpConnectorCiscoSB()._can_manage_interface() for interface {interface.name}")
        if interface.if_vlan_mode == SB_VLAN_MODE_TRUNK:
            # we cannot manage this yet, so disable for now:
            interface.manageable = False
            interface.unmanage_reason = "On Cisco SB devices, trunk interface is not manageable yet!"
            return False

        return True
