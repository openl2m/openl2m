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
Aruba-AOS-CX (new style) specific implementation of the SNMP object
Note that the SNMP implementation in AOS-CX switches is read-only.
We will implement many features via the REST API of the product, See
https://developer.arubanetworks.com/aruba-aoscx/docs/python-getting-started
This will be done as part of the 'Aruba-AOS' configuration type, coded in
/switches/connect/aruba_aoscx/

Update June 2022:
per https://www.arubanetworks.com/techdocs/AOS-CX/10.08/PDF/snmp_mib.pdf
on pg. 46, OIDs that support SNMP write, write is supported to
ifAdminStatus (ie interface up/down), and pethPsePortAdminEnable (ie. PoE enable/disable)
"""
from switches.connect.classes import Vlan
from switches.connect.snmp.connector import SnmpConnector, oid_in_branch
from switches.connect.snmp.constants import ieee8021QBridgeVlanStaticName, ieee8021QBridgePortVlanEntry
from switches.utils import dprint

from .constants import arubaWiredPoePethPsePortPowerDrawn, arubaWiredVsfv2MemberProductName


class SnmpConnectorArubaCx(SnmpConnector):
    """
    Aruba AOS-CX specific implementation of the SNMP object,
    for now a derivative of the default SNMP connector.
    """

    def __init__(self, request, group, switch):
        # for now, just call the super class
        dprint("Aruba SnmpConnector __init__")
        super().__init__(request, group, switch)
        self.description = 'Aruba AOS-CX SNMP (R/O) driver'
        self.switch.read_only = False    # the new Aruba AOS switches are read-only over snmp. Write-access is via REST API.

        # we cannot implement some the following capabilities due to limitations of the SNMP code in AOS-CX:
        self.can_change_admin_status = True
        self.can_change_vlan = False
        self.can_change_poe_status = True
        self.can_change_description = False
        self.can_save_config = False    # do we have the ability (or need) to execute a 'save config' or 'write memory' ?
        self.can_reload_all = True      # if true, we can reload all our data (and show a button on screen for this)

    def _parse_oid(self, oid, val):
        """
        Parse a single OID with data returned from a switch through some "get" function
        THIS NEEDS WORK TO IMPROVE PERFORMANCE !!!
        Returns True if we parse the OID and we should cache it!
        """
        dprint(f"Aruba AOS-CX _parse_oid() {oid}")

        """
        ieee8021QBridge used for vlan and port pvid info
        """
        if self._parse_mibs_aruba_ieee_qbridge(oid, val):
            return True
        if self._parse_mibs_aruba_poe(oid, val):
            return True
        # if not Aruba specific, call the generic parser
        return super()._parse_oid(oid, val)

    def _parse_mibs_aruba_ieee_qbridge(self, oid, val):
        """
        Parse Aruba's ieee 802.1q bridge Mibs
        """
        retval = oid_in_branch(ieee8021QBridgeVlanStaticName, oid)
        if retval:
            vlan_id = int(retval)
            # dprint(f"Aruba VLAN {vlan_id} name '{val}'")
            v = Vlan(id=vlan_id, name=val)
            self.add_vlan(v)
            return True

        retval = oid_in_branch(ieee8021QBridgePortVlanEntry, oid)
        if retval:
            # retval is in format 1.1.1, for name 1/1/1
            name = retval.replace('.', '/')
            # dprint(f"Aruba Port {name} untagged vlan {val}")
            # however, the key to the interface is the ifIndex, not name!
            iface = self.get_interface_by_name(name)
            if iface:
                # dprint("   Port found !")
                untagged_vlan = int(val)
                if not iface.is_tagged and untagged_vlan in self.vlans.keys():
                    iface.untagged_vlan = untagged_vlan
                    iface.untagged_vlan_name = self.vlans[untagged_vlan].name
            else:
                # AOS-CX appears to report all interfaces for all possible stack members.
                # even when less then max-stack-members are actualy present!
                # so we are ignoring this warning for now...
                # self.add_warning(f"IEEE802.1QBridgePortVlanEntry found, but interface {name} NOT found!")
                dprint(f"IEEE802.1QBridgePortVlanEntry found, but interface {name} NOT found!")
            return True

        return False

    def _parse_mibs_aruba_poe(self, oid, val):
        """
        Parse Aruba's ARUBAWIRED-POE Mibs
        """
        pe_index = oid_in_branch(arubaWiredPoePethPsePortPowerDrawn, oid)
        if pe_index:
            dprint(f"Found branch arubaWiredPoePethPsePortPowerDrawn, pe_index = {pe_index}")
            if pe_index in self.poe_port_entries.keys():
                self.poe_port_entries[pe_index].power_consumption_supported = True
                self.poe_port_entries[pe_index].power_consumed = int(val)
            return True

        return False

    def _parse_mibs_aruba_vsf2(self, oid, val):
        """
        Parse ARUBAWIRED-VSFv2 mibs.
        """
        dev_index = int(oid_in_branch(arubaWiredVsfv2MemberProductName, oid))
        if dev_index:
            dprint(f"Found branch arubaWiredVsfv2MemberProductName, device index = {dev_index}, val = {val}")
            # add to device/stacking info area:
            dprint(f"Device {dev_index}: {val}")
            # save this info!
            if dev_index in self.stack_members.keys():
                # save this info!
                self.stack_members[dev_index].info = val
            else:
                # should not happen:
                dprint(" ERROR: Device Index NOT found in StackMembers!")
            return True

        return False

    def _get_poe_data(self):
        """
        Aruba(HP) used both the standard PoE MIB, and their own ARUBAWIRED-POE mib.
        """
        # get standard data first, this loads PoE status, etc.
        super()._get_poe_data()
        # if we found power supplies, get Aruba specific info about power usage from ARUBAWIRED-POE mib
        if self.poe_capable:
            retval = self.get_snmp_branch('arubaWiredPoePethPsePortPowerDrawn', self._parse_mibs_aruba_poe)
            if retval < 0:
                self.add_warning("Error getting 'PoE-Port-Actual-Power' (arubaWiredPoePethPsePortPowerDrawn)")

        return 1

    def _get_vlan_data(self):
        """
        Implement an override of vlan parsing to read Cisco specific MIB
        Get all neccesary vlan info (names, id, ports on vlans, etc.) from the switch.
        Returns -1 on error, or number to indicate vlans found.
        """
        dprint("_get_vlan_data(ArubaAosCx)\n")
        # get the generic vlan data:
        super()._get_vlan_data()

        # first, Aruba vlan names
        retval = self.get_snmp_branch('ieee8021QBridgeVlanStaticName', self._parse_mibs_aruba_ieee_qbridge)
        if retval < 0:
            return retval
        # port PVID untagged vlan
        retval = self.get_snmp_branch('ieee8021QBridgePortVlanEntry', self._parse_mibs_aruba_ieee_qbridge)
        if retval < 0:
            return retval
        # set vlan count
        self.vlan_count = len(self.vlans)
        return self.vlan_count

    def get_my_hardware_details(self):
        """
        Load hardware details from the VSF v2 mib (Virtual Switch Fabric)
        then call the generic SNMP hardware details.
        """
        super().get_my_hardware_details()

        # now read AOS-CX specific data:
        retval = self.get_snmp_branch('arubaWiredVsfv2MemberProductName', self._parse_mibs_aruba_vsf2)
        if retval < 0:
            self.add_warning("Error getting 'Aruba Vsf Product name' ('arubaWiredVsfv2MemberProductName')")
            return False
        return True
