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
Juniper Networks specific implementation of the SNMP object
This re-implements some methods found in the base SNMP() class
with Juniper specific ways of doing things...
Note: JUNOS devices are Read-Only for SNMP! See the PyEZ driver for R/W capabilities!
"""
from django.http.request import HttpRequest

from switches.models import Switch, SwitchGroup
from switches.constants import LOG_TYPE_ERROR, LOG_PORT_POE_FAULT
from switches.connect.constants import (
    POE_PORT_DETECT_DELIVERING,
    poe_status_name,
    VLAN_STATUS_PERMANENT,
    VLAN_STATUS_DYNAMIC,
    VLAN_STATUS_OTHER,
)
from switches.connect.classes import Interface, Error
from switches.connect.snmp.connector import SnmpConnector, oid_in_branch
from switches.utils import dprint

from .constants import (
    JNX_VLAN_TYPE_STATIC,
    JNX_VLAN_TYPE_DYNAMIC,
    jnxL2aldVlanTag,
    jnxL2aldVlanName,
    jnxL2aldVlanType,
    jnxL2aldVlanFdbId,
)


class SnmpConnectorJuniper(SnmpConnector):
    """
    Juniper Networks specific implementation of the SNMP object
    This re-implements some methods found in the base SNMP() class
    with Juniper specific ways of doing things...
    """

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        # for now, just call the super class
        dprint("Juniper Networks SnmpConnector __init__")
        super().__init__(request=request, group=group, switch=switch)
        # force READ-ONLY. JUNOS devices are Read-Only for SNMP! See the PyEZ driver for R/W capabilities!
        self.read_only = True
        self.vendor_name = "Juniper Networks"
        self.description = "Juniper Networks Read-Only SNMP driver"

        # Netmiko is used for SSH connections. Here are some defaults a class can set.
        #
        # device_type:
        # if set, will be a value that will override (ie. hardcode) values from the
        # "Credentials Profile" (aka the NetmikoProfile() object)
        self.netmiko_device_type = "juniper"
        # no need to override default of netmiko_valid_device_types[]
        #
        # the command that should be sent to disable screen paging
        # let Netmiko decide...
        # self.netmiko_disable_paging_command = "set cli screen-length 0"
        self.add_warning(warning="Note: Juniper SNMP access is Read-Only!", add_log=False)

    def _map_poe_port_entries_to_interface(self):
        """
        This function maps the "pethPsePortEntry" indices that are stored in self.poe_port_entries{}
        to interface ifIndex values, so we can store them with the interface and display as needed.
        It ***appears*** the poe_port index is "power-supply-number.port-number", all 1-based.
        So power entry "1.1" is interface ge-0/0/0, and power entry "1.5" is ge-0/0/4
        """
        dprint("Juniper _map_poe_port_entries_to_interface()")
        for port_entry in self.poe_port_entries.values():
            # we take the ending part of "1.5" as the index
            (module, port) = port_entry.index.split('.')
            module = int(module) - 1  # 0-based!
            port = int(port) - 1  # 0-based!
            # find the matching interface:
            for iface in self.interfaces.values():
                if_name = f"ge-{module}/0/{port}"
                if iface.name == if_name:
                    dprint(f"   PoE Port Map FOUND {iface.name}")
                    iface.poe_entry = port_entry
                    if port_entry.detect_status > POE_PORT_DETECT_DELIVERING:
                        warning = (
                            f"PoE FAULT status ({port_entry.detect_status} = "
                            f"{poe_status_name[port_entry.detect_status]}) on interface {iface.name}"
                        )
                        self.add_warning(warning=warning)
                        self.add_log(type=LOG_TYPE_ERROR, action=LOG_PORT_POE_FAULT, description=warning)
                    break

    def _get_vlan_data(self) -> int:
        """
        Implement an override of vlan parsing to read Junos EX specific MIB
        Return 1 on success, -1 on failure
        """
        dprint("Juniper _get_vlan_data()\n")

        # first, call the standard snmp vlan reader
        super()._get_vlan_data()

        # try the Juniper L2 entries. FIrst the "tag" or index to vlan_id mapping:
        retval = self.get_snmp_branch(branch_name='jnxL2aldVlanTag', parser=self._parse_mibs_juniper_l2ald_vlans)
        if retval < 0:  # error
            return retval
        if retval > 0:  # we found something, read the rest
            retval = self.get_snmp_branch(branch_name='jnxL2aldVlanName', parser=self._parse_mibs_juniper_l2ald_vlans)
            if retval < 0:  # error
                return retval
            retval = self.get_snmp_branch(branch_name='jnxL2aldVlanType', parser=self._parse_mibs_juniper_l2ald_vlans)
            if retval < 0:  # error
                return retval
            retval = self.get_snmp_branch(branch_name='jnxL2aldVlanFdbId', parser=self._parse_mibs_juniper_l2ald_vlans)
            if retval < 0:  # error
                return retval
            return 1
        return 0

    def _parse_mibs_juniper_l2ald_vlans(self, oid: str, val: str) -> bool:
        """
        Parse JNX EX specific VLAN Mibs
        Returns True if parses, False if not.
        """
        dprint("_parse_mibs_juniper_l2ald_vlans()\n")

        """
        # internal vlan tag - frequently NOT returned
        vlan_index = int(oid_in_branch(jnxL2aldVlanID, oid))
        if vlan_index:
            if (int(val) == 1):
                self.vlan_id_by_index[vlan_index] = Vlan(none, vlan_index)
            return True
        """
        # a new vlan tag or index that maps to an actual vlan id on the wire!
        vlan_index = int(oid_in_branch(jnxL2aldVlanTag, oid))
        if vlan_index:
            dprint(f"jnxL2aldVlanTag {vlan_index} = {val}")
            self.vlan_id_by_index[vlan_index] = int(val)
            return True

        # vlan name, indexed by internal vlan index, NOT vlan id!
        vlan_index = int(oid_in_branch(jnxL2aldVlanName, oid))
        if vlan_index:
            dprint(f"jnxL2aldVlanName {vlan_index} = {val}")
            try:
                self.vlans[self.vlan_id_by_index[vlan_index]].name = val
            except KeyError:
                # should not happen!
                self.add_warning(warning=f"Invalid vlan index {vlan_index} (jnxL2aldVlanName)")
            return True

        # vlan type, static or dynamic
        vlan_index = int(oid_in_branch(jnxL2aldVlanType, oid))
        if vlan_index:
            dprint(f"jnxL2aldVlanType {vlan_index} = {val}")
            value = int(val)
            if value == JNX_VLAN_TYPE_STATIC:
                status = VLAN_STATUS_PERMANENT
            elif value == JNX_VLAN_TYPE_DYNAMIC:
                status = VLAN_STATUS_DYNAMIC
            else:  # should not happen!
                status = VLAN_STATUS_OTHER
            try:
                self.vlans[self.vlan_id_by_index[vlan_index]].status = status
            except KeyError:
                # should not happen!
                self.add_warning(warning=f"Invalid vlan index {vlan_index} (jnxL2aldVlanType)")
            return True

        # the filtering database, this maps 'vlan index' (sub-oid) to 'filter db index' (return value)
        vlan_index = int(oid_in_branch(jnxL2aldVlanFdbId, oid))
        if vlan_index:
            fdb_index = int(val)
            try:
                self.vlans[self.vlan_id_by_index[vlan_index]].fdb_index = fdb_index
                self.dot1tp_fdb_to_vlan_index[fdb_index] = vlan_index
                dprint(f"FDB entry:  {fdb_index}  =>  {vlan_index}")
            except KeyError:
                # should not happen!
                self.add_warning(warning=f"Invalid vlan index {vlan_index} (jnxL2aldVlanFdbId)")
            return True
        return False

    def set_interface_admin_status(self, interface: Interface, status: int) -> bool:
        self.error = Error(
            status=True, description="set_interface_admin_status(): JUNOS switches are Read-Only for SNMP!"
        )
        return False

    def set_interface_poe_status(self, nterface: Interface, status: int) -> bool:
        self.error = Error(
            status=True, description="set_interface_poe_status(): JUNOS switches are Read-Only for SNMP!"
        )
        return False

    def set_interface_description(self, interface: Interface, description: str) -> bool:
        self.error = Error(
            status=True, description="set_interface_description(): JUNOS switches are Read-Only for SNMP!"
        )
        return False

    def set_interface_untagged_vlan(self, interface: Interface, new_vlan_id: int) -> bool:
        self.error = Error(
            status=True, description="set_interface_untagged_vlan(): JUNOS switches are Read-Only for SNMP!"
        )
        return False
