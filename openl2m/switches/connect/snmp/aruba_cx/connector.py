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
"""
from switches.models import Log
from switches.constants import *
from switches.connect.classes import *
from switches.connect.connector import *
from switches.connect.snmp.connector import SnmpConnector, oid_in_branch
from switches.connect.snmp.constants import *
from switches.utils import *

from .constants import *


class SnmpConnectorArubaCx(SnmpConnector):
    """
    Aruba AOS-CX specific implementation of the SNMP object,
    for now a derivative of the default SNMP connector.
    """

    def __init__(self, request, group, switch):
        # for now, just call the super class
        dprint("Aruba SnmpConnector __init__")
        super().__init__(request, group, switch)
        self.vendor_name = 'Aruba AOS (HPE)'
        self.switch.read_only = True    # the new Aruba AOS switches are read-only over snmp. Write-access is via REST API.

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
