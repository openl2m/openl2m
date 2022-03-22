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
Commands-Only Connector: this implements an SSH connection to the devices
that is used for excuting commands only!
"""
from switches.models import Log
from switches.constants import *
from switches.connect.classes import *
from switches.connect.connector import *
from switches.connect.snmp.constants import *
from switches.utils import *

from .constants import *


class CommandsOnlyConnector(Connector):
    """
    This implements a "Dummy" connector object.
    All activity here is simulated, no actual network device calls are made.
    This is purely for testing and to show how to implement a new device interface.
    """

    def __init__(self, request, group, switch):
        # for now, just call the super class
        dprint("Commands-Only Connector __init__")
        super().__init__(request, group, switch)
        self.vendor_name = 'Commands-Only'
        # force READ-ONLY for now! We have not implemented changing settings.
        self.switch.read_only = True
        self.add_more_info('System', 'Type', "SSH-only connected device!")
        if switch.description:
            self.add_more_info('System', 'Description', switch.description)
        self.show_interfaces = False    # do NOT show interfaces, vlans etc...

    def get_my_basic_info(self):
        """
        placeholder, we are not actually gathering information here
        Implemented to surpress the warning if not implemented.
        """
        dprint("Commands-Only Connector get_my_basic_info()")
        return True

    def can_run_commands(self):
        """
        Does the device have the ability to execute a 'cli command'
        Returns True or False
        """
        if self.switch.primary_ip4 and self.switch.netmiko_profile:
            return True
        return False
