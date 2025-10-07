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
from django.http.request import HttpRequest

from switches.connect.connector import Connector
from switches.models import Switch, SwitchGroup
from switches.utils import dprint


class AristaApiConnector(Connector):
    """
    This implements an Arista eAPI connector object.
    """

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        # call the super class
        dprint("AristaApiConnector __init__")
        super().__init__(request, group, switch)
        self.description = 'Arista eAPI driver'
        self.vendor_name = "Arista"
        # force READ-ONLY for now
        self.read_only = True
        if switch.description:
            self.add_more_info('System', 'Description', switch.description)
        self.show_interfaces = False  # for now, do NOT show interfaces, vlans etc...

    def get_my_basic_info(self) -> bool:
        """
        placeholder, to be implemented.
        """
        dprint("AristaApiConnector get_my_basic_info()")
        self.hostname = self.switch.hostname
        return True
