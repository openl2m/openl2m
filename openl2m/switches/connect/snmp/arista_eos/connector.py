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
Arista Networks specific implementation of the SNMP object
See Mibs, etc. at
  https://www.arista.com/en/support/product-documentation/arista-snmp-mibs
General Arista SNMP config information is at:
  https://www.arista.com/en/um-eos/eos-snmp
"""
from django.http.request import HttpRequest

from switches.connect.constants import IF_TYPE_ETHERNET
from switches.connect.classes import Interface
from switches.connect.snmp.connector import SnmpConnector
from switches.connect.snmp.constants import dot1qPvid
from switches.models import Switch, SwitchGroup
from switches.utils import dprint


class SnmpConnectorAristaEOS(SnmpConnector):
    """
    Arista Networks specific implementation of the SNMP object,
    for now a derivative of the default SNMP connector.
    """

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        # for now, just call the super class
        dprint("Arista Networks SnmpConnector __init__")
        super().__init__(request, group, switch)
        self.description = 'Arista Networks EOS SNMP driver'
        self.vendor_name = "Arista Networks (EOS)"
        self.switch.read_only = False  # Arista support some mib variables as R/W
        self.can_reload_all = True  # if true, we can reload all our data (and show a button on screen for this)
        # all firmware versions support admin-status, description, vlan change via snmp:
        self.can_change_admin_status = True
        self.can_change_description = True
        self.can_change_vlan = True
        # no support for PoE in mibs:
        self.can_change_poe_status = False
        # Save is possible, but not implemented yet:
        self.can_save_config = False
        # vlan create/edit not supported:
        self.can_edit_vlans = False
        self.can_set_vlan_name = False  # vlan create/delete allowed over snmp, but cannot set name!

    def get_my_basic_info(self) -> bool:
        """
        We override "Get the basic info" to parse the vlans on interfaces.
        Default Arista interface is "switchport" on vlan 1.
        Arista 'routed' interfaces to no have a valid vlan.
        """
        dprint("SnmpConnectorAristaEOS.get_my_basic_info()")
        # first get all normal SNMP info, implemented in the super class:
        if not super().get_my_basic_info():
            return False
        # now run all interfaces and set routed if no valid vlan.
        for key, iface in self.interfaces.items():
            if iface.type == IF_TYPE_ETHERNET and iface.untagged_vlan == -1:
                iface.is_routed = True
        return True

    def set_interface_untagged_vlan(self, interface: Interface, new_vlan_id: int) -> bool:
        """
        Change the VLAN via the Q-BRIDGE MIB
        According to Arista, you only need to write the new vlan id to "dot1qPvid"
        return True on success, False on error and set self.error variables
        """
        dprint(f"arista_eos.set_interface_untagged_vlan(i={interface}, vlan={new_vlan_id})")
        if not interface:
            dprint("  Invalid interface!, returning False")
            return False
        # now check the Q-Bridge PortID
        if interface.port_id < 0:
            dprint(f"  Invalid interface.port_id ({interface.port_id}), returning False")
            return False
        dprint("   valid interface and port_id")
        # old_vlan_id = interface.untagged_vlan
        # set this switch port on the new vlan:
        # Q-BIRDGE mib: VlanIndex = Unsigned32
        dprint("Setting NEW VLAN on port")
        if not self.set(f"{dot1qPvid}.{interface.port_id}", int(new_vlan_id), 'u'):
            return False

        interface.untagged_vlan = new_vlan_id
        return True
