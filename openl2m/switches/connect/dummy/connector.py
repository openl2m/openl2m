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
from django.http.request import HttpRequest

from switches.connect.constants import IF_TYPE_ETHERNET
from switches.connect.classes import Interface, NeighborDevice
from switches.connect.connector import Connector
from switches.models import Switch, SwitchGroup
from switches.utils import dprint
from switches.connect.constants import LLDP_CAPABILITIES_WLAN, LLDP_CAPABILITIES_ROUTER, LLDP_CAPABILITIES_PHONE


class DummyConnector(Connector):
    """
    This implements a "Dummy" connector object.
    All activity here is simulated, no actual network device calls are made.
    This is purely for testing and to show how to implement a new device interface.
    """

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        # for now, just call the super class
        dprint("Dummy Connector __init__")
        super().__init__(request, group, switch)
        self.description = 'Dummy Test driver'
        self.vendor_name = "Dummy Test Device"
        self.hostname = "dummy.example.org"
        # We allow write, this will call base class bookkeeping functions in Connector()
        # self.read_only = False
        self.add_more_info('System', 'Type', "Software Dummy Switch")
        self.add_more_info("System", "Hostname", self.hostname)

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
        eth = self.add_learned_ethernet_address(
            if_name="eth0/0/0",
            eth_address="00:11:22:33:44:55",
            vlan_id=10,
            ip4_address="192.168.0.100",
            ip6_address="FE80::0001/64",
        )
        # "fc00::/7"  is a private range for IPv6
        eth.add_ip6_address("fc00::0001/64")
        eth = self.add_learned_ethernet_address(
            if_name="eth0/0/1",
            eth_address="0000.1111.2222",
            vlan_id=5,
            ip4_address="192.168.1.222",
            ip6_address="FE80::00F0/64",
        )
        eth.add_ip6_address("fc00::0001:0010/64")
        self.add_learned_ethernet_address(
            if_name="eth2",
            eth_address="aa-bb-cc-dd-ee-ff",
            vlan_id=15,
            ip4_address="192.168.2.56",
            ip6_address="FE80::00E5/64",
        )

        neighbor = NeighborDevice("0000.aabb.1111")
        neighbor.sys_name = "Simulated Remote Device"
        neighbor.sys_descr = "LLDP Simulation"
        neighbor.port_name = "remote-eth0"
        neighbor.port_descr = "simulated remote port"
        neighbor.set_capability(LLDP_CAPABILITIES_WLAN)
        neighbor.set_capability(LLDP_CAPABILITIES_ROUTER)
        neighbor.set_capability(LLDP_CAPABILITIES_PHONE)

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
        Dummy driver cannot run 'cli command'
        """
        return False
