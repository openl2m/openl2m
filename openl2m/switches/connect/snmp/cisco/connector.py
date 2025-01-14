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
Cisco specific implementation of the SNMP Connection object.
This augments/re-implements some methods found in the base SNMP() class
with Cisco specific ways of doing things...
"""
import datetime
import random
import time
from django.conf import settings
from django.http.request import HttpRequest
from typing import Dict

from switches.models import Switch, SwitchGroup
from switches.constants import LOG_TYPE_ERROR, LOG_SAVE_SWITCH, LOG_PORT_POE_FAULT, SNMP_VERSION_2C
from switches.connect.classes import Interface, SyslogMsg
from switches.connect.constants import poe_status_name, POE_PORT_DETECT_FAULT, VLAN_TYPE_NORMAL
from switches.connect.snmp.connector import SnmpConnector, oid_in_branch
from switches.utils import dprint

from .constants import (
    portIfIndex,
    vmVlan,
    vmVoiceVlanId,
    cL2L3IfModeOper,
    cpeExtPsePortPwrConsumption,
    cpeExtPsePortPwrAvailable,
    cpeExtPsePortMaxPwrDrawn,
    vtpVlanState,
    vtpVlanType,
    vtpVlanName,
    vlanTrunkPortDynamicState,
    vlanTrunkPortNativeVlan,
    vlanTrunkPortVlansEnabled,
    vlanTrunkPortVlansEnabled2k,
    vlanTrunkPortVlansEnabled3k,
    vlanTrunkPortVlansEnabled4k,
    ccmHistoryRunningLastChanged,
    ccmHistoryRunningLastSaved,
    ccmHistoryStartupLastChanged,
    clogHistTableMaxLength,
    clogHistIndex,
    clogHistFacility,
    clogHistSeverity,
    clogHistMsgName,
    clogHistMsgText,
    clogHistTimestamp,
    ciscoWriteMem,
    ccCopySourceFileType,
    ccCopyDestFileType,
    ccCopyEntryRowStatus,
    ccCopyState,
    rowStatusActive,
    copyStateSuccess,
    copyStateRunning,
    copyStateWaiting,
    copyStateFailed,
    runningConfig,
    startupConfig,
    CISCO_VLAN_TYPE_NORMAL,
    VTP_TRUNK_STATE_ON,
    CISCO_ROUTE_MODE,
)


class SnmpConnectorCisco(SnmpConnector):
    """
    CISCO specific implementation of the base SNMP class.
    We override various functions as needed for the Cisco way of doing things.
    """

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        # for now, just call the super class
        dprint("CISCO SnmpConnector __init__")
        super().__init__(request, group, switch)
        self.description = 'Cisco SNMP driver'
        self.vendor_name = "Cisco"
        """
        # capabilities of the Cisco snmp driver are identical to the snmp driver:
        self.can_change_admin_status = True
        self.can_change_vlan = True
        self.can_change_poe_status = True
        self.can_change_description = True
        self.can_save_config = True    # do we have the ability (or need) to execute a 'save config' or 'write memory' ?
        self.can_reload_all = True      # if true, we can reload all our data (and show a button on screen for this)
        """
        self.stack_port_to_if_index: Dict[int, int] = {}  # maps (Cisco) stacking port to ifIndex values

        # Netmiko is used for SSH connections. Here are some defaults a class can set.
        #
        # device_type:
        # if set, will be a value that will override (ie. hardcode) values from the
        # "Credentials Profile" (aka the NetmikoProfile() object)
        self.netmiko_device_type = ""
        # if netmiko_device_type is not set, the netmiko_valid_device_types is a  list()
        # with the valid device_type choices a driver should allow in the
        # "Credentials Profile". Any other value will trigger an error, and fail the SSH connection.
        self.netmiko_valid_device_types = ['cisco_asa', 'cisco_ios', 'cisco_nxos', 'cisco_xe', 'cisco_xr']
        # the command that should be sent to disable screen paging
        # let Netmiko decide this...
        # self.netmiko_disable_paging_command = "terminal length 0"

    def _get_interface_data(self) -> bool:
        """
        Implement an override of the interface parsing routine,
        so we can add Cisco specific interface MIBs
        """
        # first call the base class to populate interfaces:
        super()._get_interface_data()

        # now add Cisco data, and cache it:
        if self.get_snmp_branch(branch_name='cL2L3IfModeOper', parser=self._parse_mibs_cisco_if_opermode) < 0:
            dprint("Cisco cL2L3IfModeOper returned error!")
            return False

        return True

    def _get_vlan_data(self) -> int:
        """
        Implement an override of vlan parsing to read Cisco specific MIB
        Get all neccesary vlan info (names, id, ports on vlans, etc.) from the switch.
        Returns -1 on error, or number to indicate vlans found.
        """
        dprint("_get_vlan_data(Cisco)\n")
        # first, read existing vlan id's
        retval = self.get_snmp_branch(branch_name='vtpVlanState', parser=self._parse_mibs_cisco_vtp)
        if retval < 0:
            return retval
        # vlan types are next
        retval = self.get_snmp_branch(branch_name='vtpVlanType', parser=self._parse_mibs_cisco_vtp)
        if retval < 0:
            return retval
        # next, read vlan names
        retval = self.get_snmp_branch(branch_name='vtpVlanName', parser=self._parse_mibs_cisco_vtp)
        if retval < 0:
            return retval
        # find out if a port is configured as trunk or not, read port trunk(802.1q tagged) status
        retval = self.get_snmp_branch('vlanTrunkPortDynamicState', self._parse_mibs_cisco_vtp)
        if retval < 0:
            return retval
        # now, find out if interfaces are access or trunk (tagged) mode
        # this is the actual status, not what is configured; ie NOT trunk if interface is down!!!
        # retval = self.get_snmp_branch(branch_name=vlanTrunkPortDynamicStatus):  # read port trunk(802.1q tagged) status
        #    dprint("Cisco PORT TRUNK STATUS data FALSE")
        #    return False
        # and read the native vlan for trunked ports
        retval = self.get_snmp_branch(branch_name='vlanTrunkPortNativeVlan', parser=self._parse_mibs_cisco_vtp)
        if retval < 0:
            return retval
        # also read the vlans on all trunk interfaces:
        retval = self.get_snmp_branch(branch_name='vlanTrunkPortVlansEnabled', parser=self._parse_mibs_cisco_vtp)
        if retval < 0:
            return retval
        # now read 2k, 3k and 4k vlans as well:
        retval = self.get_snmp_branch(branch_name='vlanTrunkPortVlansEnabled2k', parser=self._parse_mibs_cisco_vtp)
        if retval < 0:
            return retval
        # if the 2k vlan mibs exist, then also read 3k & 4k vlans
        elif retval > 0:
            retval = self.get_snmp_branch(branch_name='vlanTrunkPortVlansEnabled3k', parser=self._parse_mibs_cisco_vtp)
            if retval > 0:
                retval = self.get_snmp_branch(
                    branch_name='vlanTrunkPortVlansEnabled4k', parser=self._parse_mibs_cisco_vtp
                )

        # finally, if not trunked, read untagged interfaces vlan membership
        retval = self.get_snmp_branch(branch_name='vmVlan', parser=self._parse_mibs_cisco_vlan)
        if retval < 0:
            return retval
        # and just for giggles, read Voice vlan
        retval = self.get_snmp_branch(branch_name='vmVoiceVlanId', parser=self._parse_mibs_cisco_voice_vlan)
        if retval < 0:
            return retval
        # set vlan count
        self.vlan_count = len(self.vlans)
        return self.vlan_count

    def _get_known_ethernet_addresses(self) -> bool:
        """
        Read the Bridge-MIB for known ethernet address on the switch.
        On Cisco switches, you have to append the vlan ID after the v1/2c community,
        eg. public@13 for vlan 13
        Return True on success (0 or more found), False on errors
        """
        dprint("_get_known_ethernet_addresses(Cisco)\n")
        for vlan_id in self.vlans.keys():
            # little hack for Cisco devices, to see various vlan-specific tables:
            self.vlan_id_context = int(vlan_id)
            com_or_ctx = ''
            if self.switch.snmp_profile.version == SNMP_VERSION_2C:
                # for v2, set community string to "Cisco format"
                com_or_ctx = f"{self.switch.snmp_profile.community}@{vlan_id}"
            else:
                # v3, set context to "Cisco format":
                com_or_ctx = f"vlan-{vlan_id}"
            self._set_snmp_session(com_or_ctx)
            # first map Q-Bridge ports to ifIndexes:
            retval = self.get_snmp_branch(branch_name='dot1dBasePortIfIndex', parser=self._parse_mibs_vlan_related)
            if retval < 0:
                # probably an error, stop here!
                return False
            # next, read the known ethernet addresses, and add to the Interfaces
            retval = self.get_snmp_branch(branch_name='dot1dTpFdbPort', parser=self._parse_mibs_dot1d_bridge_eth)
            if retval < 0:
                # probably an error, stop here!
                return False
        # reset the snmp session back!
        self.vlan_id_context = 0
        self._set_snmp_session()
        return True

    def _get_poe_data(self) -> int:
        """
        Implement reading Cisco-specific PoE mib.
        Returns 1 on success, -1 on failure
        """
        dprint("_get_poe_data(Cisco)\n")

        # get Cisco Stack MIB port to ifIndex map first
        # this may be used to find the POE port index
        retval = self.get_snmp_branch(branch_name='portIfIndex', parser=self._parse_mibs_cisco_poe)
        if retval < 0:
            return retval

        # check to see if standard PoE MIB is supported
        retval = super()._get_poe_data()
        if retval < 0:
            return retval

        # probe Cisco specific Extended POE mibs to add data
        # this is what is shown via "show power inline" command:
        retval = self.get_snmp_branch(branch_name='cpeExtPsePortPwrAvailable', parser=self._parse_mibs_cisco_poe)
        if retval < 0:
            return retval
        # this is the consumed power, shown in 'show power inline <name> detail'
        retval = self.get_snmp_branch(branch_name='cpeExtPsePortPwrConsumption', parser=self._parse_mibs_cisco_poe)
        if retval < 0:
            return retval
        # max power consumed since interface power reset
        retval = self.get_snmp_branch(branch_name='cpeExtPsePortMaxPwrDrawn', parser=self._parse_mibs_cisco_poe)
        return retval

    def _get_syslog_msgs(self):
        """
        Read the CISCO-SYSLOG-MSG-MIB
        """
        retval = self.get_snmp_branch(branch_name='ciscoSyslogMIBObjects', parser=self._parse_mibs_cisco_syslog_msg)
        if retval < 0:
            # something bad happened
            self.add_warning(warning="Error getting Cisco Syslog Messages (ciscoSyslogMIBObjects)")
            self.log_error()

    def _map_poe_port_entries_to_interface(self):
        """
        This function maps the "pethPsePortEntry" indices that are stored in self.poe_port_entries{}
        to interface ifIndex values, so we can store them with the interface and display as needed.
        If we have found the Cisco-Stack-Mib 'portIfIndex' table, we use it to map to ifIndexes.
        If not, we use the generic approach, as it appears the port entry is in the format "modules.port"
        In general, you can generate the interface ending "x/y" from the index by substituting "." for "/"
        E.g. "5.12" from the index becomes "5/12", and you then search for an interface with matching ending
        e.g. GigabitEthernet5/12
        """
        for pe_index, port_entry in self.poe_port_entries.items():
            if len(self.stack_port_to_if_index) > 0:
                if pe_index in self.stack_port_to_if_index.keys():
                    if_index = str(self.stack_port_to_if_index[pe_index])
                    iface = self.get_interface_by_key(if_index)
                    if iface:
                        iface.poe_entry = port_entry
                        if port_entry.detect_status == POE_PORT_DETECT_FAULT:
                            warning = (
                                f"PoE FAULT status ({port_entry.detect_status} = "
                                f"{poe_status_name[port_entry.detect_status]}) on interface {iface.name}"
                            )
                            self.add_warning(warning=warning)
                            self.add_log(type=LOG_TYPE_ERROR, action=LOG_PORT_POE_FAULT, description=warning)

            else:
                # map "mod.port" to "mod/port"
                end = port_entry.index.replace('.', '/')
                count = len(end)
                for if_index, iface in self.interfaces.items():
                    if iface.name[-count:] == end:
                        iface.poe_entry = port_entry
                        if port_entry.detect_status == POE_PORT_DETECT_FAULT:
                            warning = (
                                f"PoE FAULT status ({port_entry.detect_status} = "
                                f"{poe_status_name[port_entry.detect_status]}) "
                                f"on interface {iface.name}"
                            )
                            self.add_warning(warning=warning)
                            self.add_log(type=LOG_TYPE_ERROR, action=LOG_PORT_POE_FAULT, description=warning)
                        break

    def set_interface_untagged_vlan(self, interface: Interface, new_vlan_id: int) -> bool:
        """
        Override the VLAN change, this is done Cisco specific using the VTP MIB
        Returns True or False
        """
        dprint("set_interface_untagged_vlan(Cisco)")
        if interface:
            if interface.is_tagged:
                # set the TRUNK_NATIVE_VLAN OID:
                retval = self.set(
                    oid=f"{vlanTrunkPortNativeVlan}.{interface.index}",
                    value=int(new_vlan_id),
                    snmp_type="i",
                    parser=self._parse_mibs_cisco_vtp,
                )
            else:
                # regular access mode port:
                retval = self.set(
                    oid=f"{vmVlan}.{interface.index}",
                    value=int(new_vlan_id),
                    snmp_type="i",
                    parser=self._parse_mibs_cisco_vlan,
                )
                if retval < 0:
                    # some Cisco devices want unsigned integer value:
                    retval = self.set(
                        oid=f"{vmVlan}.{interface.index}",
                        value=int(new_vlan_id),
                        snmp_type="u",
                        parser=self._parse_mibs_cisco_vlan,
                    )
            if retval == -1:
                return False
            else:
                # set the interface class attribute for proper 'viewing' and caching:
                interface.untagged_vlan = int(new_vlan_id)
                return True
        # interface not found:
        return False

    def get_my_hardware_details(self) -> bool:
        """
        Implement the get_my_hardware_details() function called from the base object get_hardware_details().
        Does not return anything.
        """
        dprint("get_my_hardware_details(Cisco)")
        super().get_my_hardware_details()

        # now read Cisco specific data:
        retval = self.get_snmp_branch(branch_name='ccmHistory', parser=self._parse_mibs_cisco_config)
        if retval < 0:
            self.add_warning(warning="Error getting Cisco log details ('ccmHistory')")
            return False
        return True

    def _parse_mibs_cisco_if_opermode(self, oid: str, val: str) -> bool:
        """
        Parse Cisco specific Interface Config MIB for operational mode
        """
        if_index = oid_in_branch(cL2L3IfModeOper, oid)
        if if_index:
            dprint(f"Cisco Interface Operation mode if_index {if_index} mode {val}")
            if int(val) == CISCO_ROUTE_MODE:
                self.set_interface_attribute_by_key(if_index, "is_routed", True)
            return True
        return False

    def _parse_mibs_cisco_poe(self, oid: str, val: str) -> bool:
        """
        Parse Cisco POE Extension MIB database
        """

        """
        Stack-MIB PortId to ifIndex mapping
        """
        stack_port_id = oid_in_branch(portIfIndex, oid)
        if stack_port_id:
            self.stack_port_to_if_index[stack_port_id] = int(val)
            return True

        # the actual consumed power, shown in 'show power inline <name> detail'
        pe_index = oid_in_branch(cpeExtPsePortPwrConsumption, oid)
        if pe_index:
            if pe_index in self.poe_port_entries.keys():
                self.poe_port_entries[pe_index].power_consumption_supported = True
                self.poe_port_entries[pe_index].power_consumed = int(val)
            return True

        # this is what is shown via 'show power inline interface X' command:
        pe_index = oid_in_branch(cpeExtPsePortPwrAvailable, oid)
        if pe_index:
            if pe_index in self.poe_port_entries.keys():
                self.poe_port_entries[pe_index].power_consumption_supported = True
                self.poe_port_entries[pe_index].power_available = int(val)
            return True

        pe_index = oid_in_branch(cpeExtPsePortMaxPwrDrawn, oid)
        if pe_index:
            if pe_index in self.poe_port_entries.keys():
                self.poe_port_entries[pe_index].power_consumption_supported = True
                self.poe_port_entries[pe_index].max_power_consumed = int(val)
            return True

        return False

    def _parse_mibs_cisco_vtp(self, oid: str, val: str) -> bool:
        """
        Parse Cisco specific VTP MIB
        """
        # vlan id
        vlan_id = int(oid_in_branch(vtpVlanState, oid))
        if vlan_id:
            if int(val) == 1:
                self.add_vlan_by_id(vlan_id)
            return True

        # vlan type
        vlan_id = int(oid_in_branch(vtpVlanType, oid))
        if vlan_id:
            type = int(val)
            if vlan_id in self.vlans.keys():
                if type == CISCO_VLAN_TYPE_NORMAL:
                    self.vlans[vlan_id].type = VLAN_TYPE_NORMAL
                else:
                    self.vlans[vlan_id].type = type
            return True

        # vlan name
        vlan_id = int(oid_in_branch(vtpVlanName, oid))
        if vlan_id:
            if vlan_id in self.vlans.keys():
                self.vlans[vlan_id].name = str(val)
            return True

        # access or trunk mode configured?
        if_index = oid_in_branch(vlanTrunkPortDynamicState, oid)
        if if_index:
            if int(val) == VTP_TRUNK_STATE_ON:
                # trunk/tagged port
                self.set_interface_attribute_by_key(if_index, "is_tagged", True)
            return True

        # access or trunk mode actual status?
        # this is the actual status, not what is configured; ie NOT trunk if interface is down!!!
        # if_index = oid_in_branch(vlanTrunkPortDynamicStatus, oid)
        # if if_index:
        #    dprint(f"Cisco PORT TRUNK STATUS ifIndex {if_index} = {val}")
        #    if (int(val) == VTP_PORT_TRUNK_ENABLED):
        #        # trunk/tagged port
        #        dprint("  TRUNKED!")
        #        self.set_interface_attribute_by_key(if_index, "is_tagged", True)
        #    return True

        # if trunk, what is the native mode?
        if_index = oid_in_branch(vlanTrunkPortNativeVlan, oid)
        if if_index:
            # trunk/tagged port native vlan
            iface = self.get_interface_by_key(if_index)
            if iface:
                # make sure this is a trunked interface and vlan is valid
                if iface.is_tagged and int(val) in self.vlans.keys():
                    iface.untagged_vlan = int(val)
                else:
                    dprint("  TRUNK NATIVE found, but NOT TRUNK PORT")
            return True
        # if trunk, what vlans are on the trunk?
        if_index = oid_in_branch(vlanTrunkPortVlansEnabled, oid)
        if if_index:
            # trunk/tagged port native vlan
            dprint(f"TRUNK PORT {if_index} HAS VLANS:")
            iface = self.get_interface_by_key(if_index)
            if iface:
                dprint(f"   INTERFACE = {iface.name}")
                if iface.is_tagged:
                    # now parse the bitmap. Note the bit place values are vlan indexes, NOT vlan ID!!!
                    dprint("   BITMAP to parse here!")
                    self._cisco_parse_vlan_bitmap(val, 0, iface)
                else:
                    dprint("     IGNORING, NOT TRUNK PORT")

            return True
        if_index = oid_in_branch(vlanTrunkPortVlansEnabled2k, oid)
        if if_index:
            # trunk/tagged port native vlan
            dprint(f"TRUNK PORT {if_index} HAS 2k VLANS:")
            iface = self.get_interface_by_key(if_index)
            if iface:
                dprint(f"   INTERFACE = {iface.name}")
                if iface.is_tagged:
                    # now parse the bitmap. Note the bit place values are vlan indexes, NOT vlan ID!!!
                    dprint("   BITMAP to parse here!")
                    self._cisco_parse_vlan_bitmap(val, 1024, iface)
                else:
                    dprint("     IGNORING, NOT TRUNK PORT")

            return True
        if_index = oid_in_branch(vlanTrunkPortVlansEnabled3k, oid)
        if if_index:
            # trunk/tagged port native vlan
            dprint(f"TRUNK PORT {if_index} HAS 3k VLANS:")
            iface = self.get_interface_by_key(if_index)
            if iface:
                dprint(f"   INTERFACE = {iface.name}")
                if iface.is_tagged:
                    # now parse the bitmap. Note the bit place values are vlan indexes, NOT vlan ID!!!
                    dprint("   BITMAP to parse here!")
                    self._cisco_parse_vlan_bitmap(val, 2048, iface)
                else:
                    dprint("     IGNORING, NOT TRUNK PORT")

            return True
        if_index = oid_in_branch(vlanTrunkPortVlansEnabled4k, oid)
        if if_index:
            # trunk/tagged port native vlan
            dprint(f"TRUNK PORT {if_index} HAS 4k VLANS:")
            iface = self.get_interface_by_key(if_index)
            if iface:
                dprint(f"   INTERFACE = {iface.name}")
                if iface.is_tagged:
                    # now parse the bitmap. Note the bit place values are vlan indexes, NOT vlan ID!!!
                    dprint("   BITMAP to parse here!")
                    self._cisco_parse_vlan_bitmap(val, 3072, iface)
                else:
                    dprint("     IGNORING, NOT TRUNK PORT")

            return True

        return False

    def _parse_mibs_cisco_vlan(self, oid: str, val: str) -> bool:
        """
        Parse Cisco specific Vlan related mib entries.
        """
        if_index = oid_in_branch(vmVlan, oid)
        if if_index:
            iface = self.get_interface_by_key(if_index)
            if iface:
                untagged_vlan = int(val)
                if not iface.is_tagged and untagged_vlan in self.vlans.keys():
                    iface.untagged_vlan = untagged_vlan
                    iface.untagged_vlan_name = self.vlans[untagged_vlan].name
            else:
                dprint("   UNTAGGED VLAN for invalid trunk port")
            return True

        return False

    def _parse_mibs_cisco_voice_vlan(self, oid: str, val: str) -> bool:
        """
        Parse Cisco specific Voice-Vlan related mib entries.
        """
        if_index = oid_in_branch(vmVoiceVlanId, oid)
        if if_index:
            voiceVlanId = int(val)
            iface = self.get_interface_by_key(if_index)
            if iface and voiceVlanId in self.vlans.keys():
                iface.voice_vlan = voiceVlanId
                # mark vlan as voice:
                self.vlans[voiceVlanId].voice = True
            return True

        return False

    def _cisco_parse_vlan_bitmap(self, val: str, vlan_base: int, iface: Interface):
        """
        Parse the 128 byte vlan bitmap entry from vlanTrunkPortVlansEnabled* entries
        to find the vlans on a trunk interface.
        val - the snmp return value for the vlanTrunkPortVlansEnabled* mib value.
        vlan_base - 0, 1024, 2048 or 3072, for the 0, 2k, 3k, or 4k versions
        iface -  the interface these vlans belong to.
        return -1 on error, 0 otherwize
        """
        offset = 0  # bit-offset in the byte
        for byte in val:
            byte = ord(byte)
            # which bits are set? A hack but it works!
            # note that the bits are actually in system order,
            # ie. bit 1 is first bit in stream, i.e. HIGH order bit!
            if byte & 128:
                vlan_id = (offset * 8) + vlan_base
                self.add_vlan_to_interface(iface, vlan_id)
            if byte & 64:
                vlan_id = (offset * 8) + 1 + vlan_base
                self.add_vlan_to_interface(iface, vlan_id)
            if byte & 32:
                vlan_id = (offset * 8) + 2 + vlan_base
                self.add_vlan_to_interface(iface, vlan_id)
            if byte & 16:
                vlan_id = (offset * 8) + 3 + vlan_base
                self.add_vlan_to_interface(iface, vlan_id)
            if byte & 8:
                vlan_id = (offset * 8) + 4 + vlan_base
                self.add_vlan_to_interface(iface, vlan_id)
            if byte & 4:
                vlan_id = (offset * 8) + 5 + vlan_base
                self.add_vlan_to_interface(iface, vlan_id)
            if byte & 2:
                vlan_id = (offset * 8) + 6 + vlan_base
                self.add_vlan_to_interface(iface, vlan_id)
            if byte & 1:
                vlan_id = (offset * 8) + 7 + vlan_base
                self.add_vlan_to_interface(iface, vlan_id)
            offset += 1
        return True

    def _parse_mibs_cisco_config(self, oid: str, val: str) -> bool:
        """
        Parse Cisco specific ConfigMan MIBs for running-config info
        This gets added to the Information tab!
        """
        sub_oid = oid_in_branch(ccmHistoryRunningLastChanged, oid)
        if sub_oid:
            # ticks in 1/100th of a second
            ago = str(datetime.timedelta(seconds=(int(val) / 100)))
            self.add_more_info("Configuration", "Running Last Modified", ago)
            return True

        sub_oid = oid_in_branch(ccmHistoryRunningLastSaved, oid)
        if sub_oid:
            # ticks in 1/100th of a second
            ago = str(datetime.timedelta(seconds=(int(val) / 100)))
            self.add_more_info("Configuration", "Running Last Saved", ago)
            return True

        sub_oid = oid_in_branch(ccmHistoryStartupLastChanged, oid)
        if sub_oid:
            # ticks in 1/100th of a second
            ago = str(datetime.timedelta(seconds=(int(val) / 100)))
            self.add_more_info("Configuration", "Startup Last Changed", ago)
            return True
        return False

    def _parse_mibs_cisco_syslog_msg(self, oid: str, val: str) -> bool:
        """
        Parse Cisco specific Syslog MIB to read syslog messages stored.
        """
        sub_oid = oid_in_branch(clogHistTableMaxLength, oid)
        if sub_oid:
            # this is the max number of syslog messages stored.
            self.syslog_max_msgs = int(val)
            return True

        sub_oid = oid_in_branch(clogHistIndex, oid)
        if sub_oid:
            # this is the index, create a new object.
            # note that not all implementation return this value, as it is implied in the other entries!
            index = int(sub_oid)
            self.syslog_msgs[index] = SyslogMsg(index)
            return True

        sub_oid = oid_in_branch(clogHistFacility, oid)
        if sub_oid:
            # verify we have an object for this index
            index = int(sub_oid)
            if index in self.syslog_msgs.keys():
                self.syslog_msgs[index].facility = val
            else:
                msg = SyslogMsg(index)
                msg.facility = val
                self.syslog_msgs[index] = msg
            return True

        # from this point on we "should" have the object created!
        sub_oid = oid_in_branch(clogHistSeverity, oid)
        if sub_oid:
            # verify we have an object for this index
            index = int(sub_oid)
            if index in self.syslog_msgs.keys():
                self.syslog_msgs[index].severity = int(val)
            else:
                # be save, create; "should" never happen
                msg = SyslogMsg(index)
                msg.severity = int(val)
                self.syslog_msgs[index] = msg
            return True

        sub_oid = oid_in_branch(clogHistMsgName, oid)
        if sub_oid:
            # verify we have an object for this index
            index = int(sub_oid)
            if index in self.syslog_msgs.keys():
                self.syslog_msgs[index].name = val
            else:
                # be save, create; "should" never happen
                msg = SyslogMsg(index)
                msg.name = val
                self.syslog_msgs[index] = msg
            return True

        sub_oid = oid_in_branch(clogHistMsgText, oid)
        if sub_oid:
            # verify we have an object for this index
            index = int(sub_oid)
            if index in self.syslog_msgs.keys():
                self.syslog_msgs[index].message = val
            else:
                # be save, create; "should" never happen
                msg = SyslogMsg(index)
                msg.message = val
                self.syslog_msgs[index] = msg
            return True

        sub_oid = oid_in_branch(clogHistTimestamp, oid)
        if sub_oid:
            # verify we have an object for this index
            index = int(sub_oid)
            # val is sysUpTime value when message was generated, ie. timetick!
            timetick = int(val)
            if index in self.syslog_msgs.keys():
                # approximate / calculate the datetime value:
                # msg timestamp = time when sysUpTime was read minus seconds between sysUptime and msg timetick
                dprint(f"TIMES ARE: {self.sys_uptime_timestamp}  {self.sys_uptime}  {timetick}")
                self.syslog_msgs[index].datetime = datetime.datetime.fromtimestamp(
                    self.sys_uptime_timestamp - int((self.sys_uptime - timetick) / 100)
                )
            else:
                # be save, create; "should" never happen
                msg = SyslogMsg(index)
                # approximate / calculate the datetime value:
                # msg time = time when sysUpTime was read minus seconds between sysUptime and msg timetick
                msg.datetime = datetime.datetime.fromtimestamp(
                    self.sys_uptime_timestamp - int((self.sys_uptime - timetick) / 100)
                )
                self.syslog_msgs[index] = msg
            return True

        return False

    def save_running_config(self) -> bool:
        """
        Cisco interface to save the current config to startup
        Returns True is this succeeds, False on failure. self.error() will be set in that case
        """
        dprint("\nCISCO save_running_config()\n")
        # first try old method, prios to IOS 12. This work on older 29xx and similar switches
        # set this OID, but do not update local cache.
        if self.set(oid=ciscoWriteMem, value=int(1), snmp_type='i', parser=self._parse_mibs_cisco_vlan) == 1:
            # the original old-style write-mem worked.
            return True

        # error occured, most likely not supported call. Try Cisco-CONFIG-COPY mib
        dprint("   Trying CONFIG-COPY method")
        some_number = random.randint(1, 254)
        # first, set source to running config
        self.set(oid=f"{ccCopySourceFileType}.{some_number}", value=int(runningConfig), snmp_type='i', parser=False)
        # next, set destination to startup co -=nfig
        self.set(oid=f"{ccCopyDestFileType}.{some_number}", value=int(startupConfig), snmp_type='i', parseer=False)
        # and then activate the copy:
        self.set(oid=f"{ccCopyEntryRowStatus}.{some_number}", value=int(rowStatusActive), snmp_type='i', parser=False)
        # now wait for this row to return success or fail:
        waittime = settings.CISCO_WRITE_MEM_MAX_WAIT
        while waittime:
            time.sleep(1)
            (error_status, snmp_ret) = self.get(oid=f"{ccCopyState}.{some_number}", parser=False)
            if error_status:
                break
            if int(snmp_ret.value) == copyStateSuccess:
                # write completed, so we are done!
                return True
            if int(snmp_ret.value) == copyStateFailed:
                break
            waittime -= 1

        # we timed-out, or errored-out
        self.error.status = True
        if error_status:
            self.error.description = "SNMP get copy-status returned error! (no idea why?)"
        elif snmp_ret.value == copyStateFailed:
            self.error.description = "Copy running to startup failed!"
        elif snmp_ret.value == copyStateRunning:
            self.error.description = "Copy running to startup not completed yet! (huh?)"
        elif snmp_ret.value == copyStateWaiting:
            self.error.description = "Copy running to startup still waiting! (for what?)"
        self.add_log(type=LOG_TYPE_ERROR, action=LOG_SAVE_SWITCH, description=self.error.description)
        # return error status
        return False
