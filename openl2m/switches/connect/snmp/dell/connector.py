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

from .constants import agentPortNativeVlanID, agentPortAccessVlanID, agentSaveConfig, DELL_SAVE_ENABLE

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

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        # for now, just call the super class
        dprint("Dell SnmpConnector __init__")
        super().__init__(request, group, switch)
        self.can_save_config = True
        # force READ-ONLY for now! We have not implemented changing settings.
        self.read_only = True
        self.vendor_name = "Dell Computing"
        self.description = "Dell Computing SNMP driver"

        # Netmiko is used for SSH connections. Here are some defaults a class can set.
        #
        # device_type:
        # if set, will be a value that will override (ie. hardcode) values from the
        # "Credentials Profile" (aka the NetmikoProfile() object)
        self.netmiko_device_type = ""
        self.netmiko_valid_device_types = ['dell_force10', 'dell_os9', 'dell_os10']
        # the command that should be sent to disable screen paging
        # let Netmiko decide...
        # self.netmiko_disable_paging_command = "terminal length 0"

    def set_interface_untagged_vlan(self, interface: Interface, new_vlan_id: int) -> bool:
        """
        Change the VLAN via the Q-BRIDGE MIB (ie generic)
        return True on success, False on error and set self.error variables
        """
        dprint("set_interface_untagged_vlan(Dell)")

        if interface and new_vlan_id > -1:
            # old_vlan_id = interface.untagged_vlan
            # set this switch port on the new vlan:
            # Q-BIRDGE mib: VlanIndex = Unsigned32
            if interface.is_tagged:
                dprint("  Tagged port")
                if not self.set(
                    oid=f"{agentPortNativeVlanID}.{interface.port_id}",
                    value=int(new_vlan_id),
                    snmp_type='i',
                    parser=False,
                ):
                    return False
            else:
                dprint("  Untagged port")
                if not self.set(
                    oid=f"{agentPortAccessVlanID}.{interface.port_id}",
                    value=int(new_vlan_id),
                    snmp_type='i',
                    parser=False,
                ):
                    return False
            # update interface() for view and caching
            interface.untagged_vlan = int(new_vlan_id)
        return True

    def save_running_config(self) -> bool:
        """
        Dell interface to save the current config to startup via SNMP
        Returns True is this succeeds, False on failure. self.error() will be set in that case
        """
        dprint("save_running_config(Dell)")

        retval = self.set(oid=f"{agentSaveConfig}.0", value=DELL_SAVE_ENABLE, snmp_type='i', parser=False)
        if retval < 0:
            dprint(f"return = {retval}")
            self.add_warning("Error saving via SNMP (agentSaveConfig)")
            return False
        dprint("All OK")
        return True
