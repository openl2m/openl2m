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
from switches.connect.constants import *
from switches.connect.classes import *
from switches.connect.connector import *
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

        self.add_vlan(1, "Default!")
        self.add_vlan(5, "Vlan Five")
        self.add_vlan(15, "Vlan Fifteen")
        self.add_vlan(20, "Twenty")

        # simulate getting switch data by hardcoding!
        # "load" some basic interface info...
        iface = Interface("eth0/0/0")
        iface.name = "eth0/0/0"
        iface.type = IF_TYPE_ETHERNET
        iface.admin_status = IF_ADMIN_STATUS_UP
        iface.oper_status = IF_OPER_STATUS_UP
        iface.speed = 10
        iface.alias = "Interface eth0/0/0"
        iface.untagged_vlan = 10
        self.add_interface(iface)

        iface = Interface("eth0/0/1")
        iface.name = "eth0/0/1"
        iface.type = IF_TYPE_ETHERNET
        iface.admin_status = IF_ADMIN_STATUS_UP
        iface.oper_status = IF_OPER_STATUS_DOWN
        iface.speed = 10
        iface.alias = "Interface eth0/0/1"
        iface.untagged_vlan = 5
        self.add_interface(iface)

        iface = Interface("eth2")
        iface.name = "ethernet2"
        iface.type = IF_TYPE_ETHERNET
        iface.admin_status = IF_ADMIN_STATUS_UP
        iface.oper_status = IF_OPER_STATUS_UP
        iface.speed = 100
        iface.alias = "Interface eth2"
        iface.untagged_vlan = 15
        self.add_interface(iface)
        self.set_interface_poe_available(iface, 15000)
        self.set_interface_poe_consumed(iface, 4500)

        iface = Interface("eth3")
        iface.name = "eth3"
        iface.type = IF_TYPE_ETHERNET
        iface.admin_status = IF_ADMIN_STATUS_DOWN
        iface.oper_status = IF_OPER_STATUS_DOWN
        iface.speed = 10
        iface.alias = "Interface eth3"
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
        e = EthernetAddress()

        self.interfaces["eth0/0/0"].eth = e

        dprint("Dummy Connector get_my_client_data()")
        # add some simulated data:

        return True

    def get_my_hardware_details(self):
        """
        placeholder for class-specific implementation to read things like:
            stacking info, serial #, and whatever you want to add.
        """
        dprint("Dummy Connector get_my_hardware_details()")
        return True

    def get_more_info(self):

        dprint("Dummy Connector get_more_info()")

        self.add_more_info('Dummy Heading', 'Element 1', 'Value 1')
        self.add_more_info('Dummy Heading', 'Element 2', 'Value 2')
        self.add_more_info('Dummy Heading', 'Element 3', 'Value 3')
        self.add_more_info('Dummy Heading', 'Element 4', 'Value 4')
        self.add_more_info('Some Other Heading', 'Element 1', 'Value 1')

    def can_run_commands(self):
        """
        Does the switch have the ability to execute a 'cli command'
        Returns True or False
        """
        return False
