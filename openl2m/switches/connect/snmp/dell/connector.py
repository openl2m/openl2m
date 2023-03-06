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
from switches.constants import *
from switches.connect.classes import *
from switches.connect.connector import *
from switches.connect.snmp.connector import SnmpConnector
from switches.connect.snmp.constants import *
from switches.utils import *

from .constants import *

"""
Work in Progress
"""


class SnmpConnectorDell(SnmpConnector):
    """
    Dell Networks specific implementation of the SNMP object
    This re-implements some methods found in the base SNMP() class
    with Dell specific ways of doing things...
    TDB
    """

    def __init__(self, request, group, switch):
        # for now, just call the super class
        dprint("Dell SnmpConnector __init__")
        super().__init__(request, group, switch)
        self.description = 'Dell SNMP driver'
        self.can_save_config = True
        # force READ-ONLY for now! We have not implemented changing settings.
        self.switch.read_only = True

    def _parse_oid(self, oid, val):
        """
        Parse a single OID with data returned from a switch through some "get" function
        THIS NEEDS WORK TO IMPROVE PERFORMANCE !!!
        Returns True if we parse the OID and we should cache it!
        """
        dprint(f"Dell Parsing OID {oid}")

        """
        if self._parse_mibs_dell_vlans(oid, val):
            return True
        """

        # if not Dell specific, call the generic parser
        return super()._parse_oid(oid, val)

    def set_interface_untagged_vlan(self, interface, new_vlan_id):
        """
        Change the VLAN via the Q-BRIDGE MIB (ie generic)
        return True on success, False on error and set self.error variables
        """
        dprint("set_interface_untagged_vlan(Dell)")

        if interface and new_vlan > -1:
            # old_vlan_id = interface.untagged_vlan
            # set this switch port on the new vlan:
            # Q-BIRDGE mib: VlanIndex = Unsigned32
            if interface.is_tagged:
                dprint("  Tagged port")
                if not self.set(f"{agentPortNativeVlanID}.{interface.port_id}", int(new_vlan_id), 'i'):
                    return False
            else:
                dprint("  Untagged port")
                if not self.set(f"{agentPortAccessVlanID}.{interface.port_id}", int(new_vlan_id), 'i'):
                    return False
            # update interface() for view and caching
            interface.untagged_vlan = int(new_vlan_id)
        return True

    def save_running_config(self):
        """
        Dell interface to save the current config to startup via SNMP
        Returns True is this succeeds, False on failure. self.error() will be set in that case
        """
        dprint("save_running_config(Dell)")

        retval = self.set(f"{agentSaveConfig}.0", DELL_SAVE_ENABLE, 'i')
        if retval < 0:
            dprint(f"return = {ret_val}")
            self.add_warning("Error saving via SNMP (agentSaveConfig)")
            return False
        dprint("All OK")
        return True
