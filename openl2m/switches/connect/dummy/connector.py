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
Dummy Connector
"""
from switches.models import Log
from switches.constants import *
from switches.connect.classes import *
from switches.connect.connector import *
from switches.connect.snmp.constants import *
from switches.utils import *

from .constants import *


class DummyConnector(Connector):
    """
    This implements a "Dummy" connector object.
    All activity here is simulated, no actual network device calls are made.
    This is purely for testing and to show how to implement a new device interface.
    """

    def __init__(self, request, group, switch):
        # for now, just call the super class
        dprint("Dummy Connector __init__")
        super().__init__(request, group, switch)
        self.vendor_name = 'Dummy'
        # force READ-ONLY for now! We have not implemented changing settings.
        self.switch.read_only = False
        self.add_more_info('System', 'Type', "Software Dummy Switch")

    def get_my_basic_info(self):
        dprint("Dummy Connector get_my_basic_info()")

        self.add_poe_powersupply(1, 45)  # simulate a 45W power supply

        self.add_vlan_by_id(1, "Default!")
        self.add_vlan_by_id(5, "Vlan Five")
        self.add_vlan_by_id(15, "Vlan Fifteen")
        self.add_vlan_by_id(20, "Twenty")

        # simulate getting switch data by hardcoding!
        # "load" some basic interface info...
        iface = Interface("eth0/0/0")
        iface.name = "eth0/0/0"
        iface.type = IF_TYPE_ETHERNET
        iface.admin_status = True
        iface.oper_status = True
        iface.speed = 10
        iface.description = "Interface eth0/0/0"
        iface.untagged_vlan = 10
        self.add_interface(iface)

        iface = Interface("eth0/0/1")
        iface.name = "eth0/0/1"
        iface.type = IF_TYPE_ETHERNET
        iface.admin_status = True
        iface.oper_status = False
        iface.speed = 10
        iface.description = "Interface eth0/0/1"
        iface.untagged_vlan = 5
        self.add_interface(iface)

        iface = Interface("eth2")
        iface.name = "ethernet2"
        iface.type = IF_TYPE_ETHERNET
        iface.admin_status = True
        iface.oper_status = True
        iface.speed = 100
        iface.description = "Interface eth2"
        iface.untagged_vlan = 15
        self.add_interface(iface)
        self.set_interface_poe_available(iface, 15000)
        self.set_interface_poe_consumed(iface, 4500)

        iface = Interface("eth3")
        iface.name = "eth3"
        iface.type = IF_TYPE_ETHERNET
        iface.admin_status = False
        iface.oper_status = False
        iface.speed = 10
        iface.description = "Interface eth3"
        iface.untagged_vlan = 5
        self.add_interface(iface)

        return True

    def get_my_client_data(self):
        """
        placeholder for class-specific implementation to read things like:
            self.get_known_ethernet_addresses()
            self.get_arp_data()
            self.get_lldp_data()
        """
        dprint("Dummy Connector get_my_client_data()")
        # add some simulated data:
        self.add_learned_ethernet_address("eth0/0/0", "00:11:22:33:44:55")
        self.add_learned_ethernet_address("eth0/0/1", "0000.1111.2222")
        self.add_learned_ethernet_address("eth2", "aa-bb-cc-dd-ee-ff")

        neighbor = NeighborDevice("0000.aabb.1111")
        neighbor.sys_name = "Simulated Remote Device"
        neighbor.sys_descr = "LLDP Simulation"
        neighbor.port_name = "remote-eth0"
        neighbor.port_descr = "simulated remote port"
        neighbor.caps += LLDP_CAPABILITIES_WLAN
        neighbor.caps += LLDP_CAPABILITIES_ROUTER
        neighbor.caps += LLDP_CAPABILITIES_PHONE

        self.add_neighbor_object("eth2", neighbor)

        return True

    def get_my_hardware_details(self):
        """
        placeholder for class-specific implementation to read things like:
            stacking info, serial #, and whatever you want to add.
        """
        dprint("Dummy Connector get_my_hardware_details()")

        self.add_more_info('Dummy Heading', 'Element 1', 'Value 1')
        self.add_more_info('Dummy Heading', 'Element 2', 'Value 2')
        self.add_more_info('Dummy Heading', 'Element 3', 'Value 3')
        self.add_more_info('Dummy Heading', 'Element 4', 'Value 4')
        self.add_more_info('Some Other Heading', 'Element 1', 'Value 1')
        return True

    def can_run_commands(self):
        """
        Does the switch have the ability to execute a 'cli command'
        Returns True or False
        """
        if self.switch.primary_ip4 and self.switch.netmiko_profile:
            return True
        return False
