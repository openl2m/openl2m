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

# from switches.connect.classes import PortList
from switches.connect.classes import Interface
from switches.connect.snmp.connector import SnmpConnector, oid_in_branch
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
