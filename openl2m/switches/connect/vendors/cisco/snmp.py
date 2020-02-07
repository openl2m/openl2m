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
from switches.models import Log
from switches.constants import SNMP_VERSION_2C
from switches.connect.classes import *
from switches.connect.snmp import SnmpConnector, oid_in_branch
from switches.utils import *

from .constants import *


class SnmpConnectorCisco(SnmpConnector):
    """
    CISCO specific implementation of the base SNMP class.
    We override various functions as needed for the Cisco way of doing things.
    """

    def __init__(self, request, group, switch):
        # for now, just call the super class
        dprint("CISCO SnmpConnector __init__")
        super().__init__(request, group, switch)
        self.name = "Cisco SnmpConnector"  # what type of class is running!
        self.vendor_name = "Cisco"

    def _parse_oid(self, oid, val):
        """
        Parse a single OID with data returned from a switch through some "get" function
        THIS NEEDS WORK TO IMPROVE PERFORMANCE !!!
        Returns True if we parse the OID and we should cache it!
        """
        dprint("CISCO Parsing OID %s" % oid)

        """
        VTP RELATED
        """
        # vlan id
        vlanId = int(oid_in_branch(VTP_VLAN_STATE, oid))
        if vlanId:
            if (int(val) == 1):
                self.vlans[vlanId] = Vlan(vlanId)
            return True

        # vlan type
        vlanId = int(oid_in_branch(VTP_VLAN_TYPE, oid))
        if vlanId:
            val = int(val)
            if vlanId in self.vlans.keys():
                self.vlans[vlanId].type = val
            return True

        # vlan name
        vlanId = int(oid_in_branch(VTP_VLAN_NAME, oid))
        if vlanId:
            if vlanId in self.vlans.keys():
                self.vlans[vlanId].name = str(val)
            return True

        # access or trunk mode configured?
        if_index = int(oid_in_branch(VTP_PORT_TRUNK_DYNAMIC_STATE, oid))
        if if_index:
            if(int(val) == VTP_TRUNK_STATE_ON):
                # trunk/tagged port
                if if_index in self.interfaces.keys():
                    self.interfaces[if_index].is_tagged = True
            return True

        # access or trunk mode actual status?
        # this is the actual status, not what is configured; ie NOT trunk if interface is down!!!
        # if_index = int(oid_in_branch(VTP_PORT_TRUNK_DYNAMIC_STATUS, oid))
        # if if_index:
        #    dprint("Cisco PORT TRUNK STATUS ifIndex %d = %s" % (if_index, val))
        #    if(int(val) == VTP_PORT_TRUNK_ENABLED):
        #        # trunk/tagged port
        #        if if_index in self.interfaces.keys():
        #            dprint("  TRUNKED!")
        #            self.interfaces[if_index].is_tagged = True
        #    return True

        # if trunk, what is the native mode?
        if_index = int(oid_in_branch(VTP_PORT_TRUNK_NATIVE_VLAN, oid))
        if if_index:
            # trunk/tagged port native vlan
            if if_index in self.interfaces.keys():
                # make sure this is a trunked interface and vlan is valid
                if self.interfaces[if_index].is_tagged and int(val) in self.vlans.keys():
                    self.interfaces[if_index].untagged_vlan = int(val)
                else:
                    dprint("  TRUNK NATIVE found, but NOT TRUNK PORT")
            return True

        if_index = int(oid_in_branch(VTP_UNTAGGED_MEMBERSHIP_VLAN, oid))
        if if_index:
            untagged_vlan = int(val)
            if (if_index in self.interfaces.keys()
                    and not self.interfaces[if_index].is_tagged
                    and untagged_vlan in self.vlans.keys()):
                self.interfaces[if_index].untagged_vlan = untagged_vlan
                self.interfaces[if_index].untagged_vlan_name = self.vlans[untagged_vlan].name
            else:
                dprint("   UNTAGGED VLAN for invalid trunk port")
            return True

        if_index = int(oid_in_branch(CISCO_VOICE_VLAN, oid))
        if if_index:
            voiceVlanId = int(val)
            if if_index in self.interfaces.keys() and voiceVlanId in self.vlans.keys():
                self.interfaces[if_index].voice_vlan = voiceVlanId
            return True

        """
        Stack-MIB PortId to ifIndex mapping
        """
        stack_port_id = oid_in_branch(CISCO_PORT_IF_INDEX, oid)
        if stack_port_id:
            self.stack_port_to_if_index[stack_port_id] = int(val)
            return True

        """
        Cisco POE Extension MIB database
        """
        # the actual consumed power, shown in 'show power inline <name> detail'
        pe_index = oid_in_branch(CISCO_POE_PORT_POWER_CONSUMED, oid)
        if pe_index:
            if pe_index in self.poe_port_entries.keys():
                self.poe_port_entries[pe_index].power_consumption_supported = True
                self.poe_port_entries[pe_index].power_consumed = int(val)
            return True

        #
        # this is what is shown via 'show power inline interface X' command:
        pe_index = oid_in_branch(CISCO_POE_PORT_POWER_AVAILABLE, oid)
        if pe_index:
            if pe_index in self.poe_port_entries.keys():
                self.poe_port_entries[pe_index].power_consumption_supported = True
                self.poe_port_entries[pe_index].power_available = int(val)
            return True

        pe_index = oid_in_branch(CISCO_POE_PORT_MAX_POWER_CONSUMED, oid)
        if pe_index:
            if pe_index in self.poe_port_entries.keys():
                self.poe_port_entries[pe_index].power_consumption_supported = True
                self.poe_port_entries[pe_index].max_power_consumed = int(val)
            return True

        # if not Cisco specific, call the generic parser
        return super()._parse_oid(oid, val)

    def _get_vlan_data(self):
        """
        Implement an override of vlan parsing to read Cisco specific MIB
        Return 1 on success, -1 on failure
        """
        dprint("_get_vlan_data(Cisco)\n")
        # first, read existing vlan id's
        retval = self._get_branch_by_name('vtpVlanState')
        if retval < 0:
            return retval
        # vlan types are next
        retval = self._get_branch_by_name('vtpVlanType')
        if retval < 0:
            return retval
        # next, read vlan names
        retval = self._get_branch_by_name('vtpVlanName')
        if retval < 0:
            return False
        # find out if a port is configured as trunk or not, read port trunk(802.1q tagged) status
        retval = self._get_branch_by_name('vlanTrunkPortDynamicState')
        if retval < 0:
            return False
        # now, find out if interfaces are access or trunk (tagged) mode
        # this is the actual status, not what is configured; ie NOT trunk if interface is down!!!
        # retval = self._get_branch(VTP_PORT_TRUNK_DYNAMIC_STATUS):  # read port trunk(802.1q tagged) status
        #    dprint("Cisco PORT TRUNK STATUS data FALSE")
        #    return False
        # and read the native vlan for trunked ports
        retval = self._get_branch_by_name('vlanTrunkPortNativeVlan')  # read trunk native vlan membership
        if retval < 0:
            return False
        # finally, if not trunked, read untagged interfaces vlan membership
        retval = self._get_branch_by_name('vmVlan')
        if retval < 0:
            return False
        # and just for giggles, read Voice vlan
        retval = self._get_branch_by_name('vmVoiceVlanId')
        if retval < 0:
            return False

        return 1

    def _get_known_ethernet_addresses(self):
        """
        Read the Bridge-MIB for known ethernet address on the switch.
        On Cisco switches, you have to append the vlan ID after the v1/2c community,
        eg. public@13 for vlan 13
        Return 1 on success, -1 on failure
        """
        dprint("_get_known_ethernet_addresses(Cisco)\n")
        for vlan_id in self.vlans.keys():
            # little hack for Cisco devices, to see various vlan-specific tables:
            com_or_ctx = ''
            if self.switch.snmp_profile.version == SNMP_VERSION_2C:
                # for v2, set community string to "Cisco format"
                com_or_ctx = "%s@%s" % (self.switch.snmp_profile.community, vlan_id)
            else:
                # v3, set context to "Cisco format":
                com_or_ctx = "vlan-%s" % vlan_id
            self._set_snmp_session(com_or_ctx)
            # first map Q-Bridge ports to ifIndexes:
            retval = self._get_branch_by_name('dot1dBasePortIfIndex')
            if retval < 0:
                return retval
            # next, read the known ethernet addresses, and add to the Interfaces
            retval = self._get_branch_by_name('dot1dTpFdbPort', False, self._parse_mibs_bridge_eth)
            if retval < 0:
                return False
        # reset the snmp session back!
        self._set_snmp_session()
        return True

    def _get_poe_data(self):
        """
        Implement reading Cisco-specific PoE mib.
        Returns 1 on success, -1 on failure
        """
        dprint("_get_poe_data(Cisco)\n")

        # get Cisco Stack MIB port to ifIndex map first
        # this may be used to find the POE port index
        retval = self._get_branch_by_name('portIfIndex')
        if retval < 0:
            return retval

        # check to see if standard PoE MIB is supported
        retval = super()._get_poe_data()
        if retval < 0:
            return retval

        # probe Cisco specific Extended POE mibs to add data
        # this is what is shown via "show power inline" command:
        retval = self._get_branch_by_name('cpeExtPsePortPwrAvailable')
        if retval < 0:
            return retval
        # this is the consumed power, shown in 'show power inline <name> detail'
        retval = self._get_branch_by_name('cpeExtPsePortPwrConsumption')
        if retval < 0:
            return retval
        # max power consumed since interface power reset
        retval = self._get_branch_by_name('cpeExtPsePortMaxPwrDrawn')
        return retval

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
        for (pe_index, port_entry) in self.poe_port_entries.items():
            if len(self.stack_port_to_if_index) > 0:
                if pe_index in self.stack_port_to_if_index.keys():
                    if_index = self.stack_port_to_if_index[pe_index]
                    if if_index in self.interfaces.keys():
                        self.interfaces[if_index].poe_entry = port_entry
                        if port_entry.detect_status == POE_PORT_DETECT_FAULT:
                            warning = "PoE FAULT status (%s) on interface %s" % (port_entry.status_name, iface.name)
                            self._add_warning(warning)
                            # log my activity
                            log = Log()
                            log.user = self.request.user
                            log.type = LOG_TYPE_ERROR
                            log.ip_address = get_remote_ip(request)
                            log.action = LOG_PORT_POE_FAULT
                            log.description = warning
                            log.save()

            else:
                # map "mod.port" to "mod/port"
                end = port_entry.index.replace('.', '/')
                count = len(end)
                for (if_index, iface) in self.interfaces.items():
                    if iface.name[-count:] == end:
                        iface.poe_entry = port_entry
                        if port_entry.detect_status == POE_PORT_DETECT_FAULT:
                            warning = "PoE FAULT status (%s) on interface %s" % (port_entry.status_name, iface.name)
                            self._add_warning(warning)
                            # log my activity
                            log = Log()
                            log.user = self.request.user
                            log.type = LOG_TYPE_ERROR
                            log.ip_address = get_remote_ip(request)
                            log.action = LOG_PORT_POE_FAULTPOE_F
                            log.description = warning
                            log.save()
                        break

    def set_interface_untagged_vlan(self, if_index, old_vlan_id, new_vlan_id):
        """
        Override the VLAN change, this is done Cisco specific using the VTP MIB
        Returns True or False
        """
        dprint("set_interface_untagged_vlan(Cisco)")
        iface = self.get_interface_by_index(if_index)
        if iface:
            if iface.is_tagged:
                # set the TRUNK_NATIVE_VLAN OID:
                return self._set(VTP_PORT_TRUNK_NATIVE_VLAN + "." + str(if_index), int(new_vlan_id), 'i')
            else:
                # regular access mode port:
                return self._set(VTP_UNTAGGED_MEMBERSHIP_VLAN + "." + str(if_index), int(new_vlan_id), 'i')
        # interface not found, return False!
        return False

    def _get_vendor_data(self):
        """
        Implement the get_vendor_data() class from the base object
        """
        dprint("_get_vendor_data(Cisco)")
        self._get_branch_by_name('ccmHistory', True, self._parse_mibs_cisco_config)

    def _parse_mibs_cisco_config(self, oid, val):
        """
        Parse Cisco specific ConfigMan MIBs for running-config info
        This gets added to the Information tab!
        """
        sub_oid = oid_in_branch(ccmHistoryRunningLastChanged, oid)
        if sub_oid:
            # ticks in 1/100th of a second
            ago = str(datetime.timedelta(seconds=(int(val) / 100)))
            self.add_vendor_data("Configuration", "Running Last Modified", ago)
            return True

        sub_oid = oid_in_branch(ccmHistoryRunningLastSaved, oid)
        if sub_oid:
            # ticks in 1/100th of a second
            ago = str(datetime.timedelta(seconds=(int(val) / 100)))
            self.add_vendor_data("Configuration", "Running Last Saved", ago)
            return True

        sub_oid = oid_in_branch(ccmHistoryStartupLastChanged, oid)
        if sub_oid:
            # ticks in 1/100th of a second
            ago = str(datetime.timedelta(seconds=(int(val) / 100)))
            self.add_vendor_data("Configuration", "Startup Last Changed", ago)
            return True
        return False

    def can_save_config(self):
        """
        If True, this instance can save the running config to startup
        Ie. "write mem" is implemented via an SNMP interfaces
        """
        return True

    def save_running_config(self):
        """
        Cisco interface to save the current config to startup
        Returns 0 is this succeeds, -1 on failure. self.error() will be set in that case
        """
        dprint("\nCISCO save_running_config()\n")
        # set this OID, but do not update local cache.
        return self._set(CISCO_WRITE_MEM, int(1), 'i', False)
