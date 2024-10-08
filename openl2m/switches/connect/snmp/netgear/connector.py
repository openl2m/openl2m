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
Dell specific implementation of the SNMP object
This re-implements some methods found in the base SNMP() class
with Dell specific ways of doing things...
"""
from django.http.request import HttpRequest

from switches.connect.classes import Interface
from switches.connect.snmp.connector import SnmpConnector
from switches.models import Switch, SwitchGroup
from switches.utils import dprint

# from .constants import xxx

"""
Work in Progress
"""


class SnmpConnectorNetgear(SnmpConnector):
    """
    Netgear specific implementation of the SNMP object
    This re-implements some methods found in the base SNMP() class
    with Netgear specific ways of doing things...

    Mostly to read the Netgear private PoE MIB
    """

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        # for now, just call the super class
        dprint("Netgear SnmpConnector __init__")
        super().__init__(request, group, switch)
        self.description = 'Netgear SNMP driver'
        self.can_save_config = False
        # force READ-ONLY for now! We have not implemented changing settings.
        self.switch.read_only = True
        self.vendor_name = ""

        # Netmiko is used for SSH connections. Here are some defaults a class can set.
        #
        # device_type:
        # if set, will be a value that will override (ie. hardcode) values from the
        # "Credentials Profile" (aka the NetmikoProfile() object)
        self.netmiko_device_type = "netgear"
        # self.netmiko_valid_device_types = False
        # the command that should be sent to disable screen paging
        # (defaults in the netmiko library to "terminal length 0", setting this to "" does NOT send a command.
        # self.netmiko_disable_paging_command = "terminal length 0"
