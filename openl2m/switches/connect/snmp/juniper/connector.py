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
"""
from switches.models import Log
from switches.constants import *
from switches.connect.classes import *
from switches.connect.connector import *
from switches.connect.snmp.connector import SnmpConnector, oid_in_branch
from switches.connect.snmp.constants import *
from switches.utils import *

from .constants import *


class SnmpConnectorJuniper(SnmpConnector):
    """
    Juniper Networks specific implementation of the SNMP object
    This re-implements some methods found in the base SNMP() class
    with Juniper specific ways of doing things...
    """

    def __init__(self, request, group, switch):
        # for now, just call the super class
        dprint("Juniper Networks SnmpConnector __init__")
        super().__init__(request, group, switch)
        self.vendor_name = 'Juniper Networks'
        # force READ-ONLY for now! We have not implemented changing settings.
        self.switch.read_only = True

    def _parse_oid(self, oid, val):
        """
        Parse a single OID with data returned from a switch through some "get" function
        THIS NEEDS WORK TO IMPROVE PERFORMANCE !!!
        Returns True if we parse the OID and we should cache it!
        """
        dprint(f"Juniper _parse_oid() {oid}")

        if self._parse_mibs_juniper_l2ald_vlans(oid, val):
            return True

        # if not Juniper specific, call the generic parser
        return super()._parse_oid(oid, val)

    def _map_poe_port_entries_to_interface(self):
        """
        This function maps the "pethPsePortEntry" indices that are stored in self.poe_port_entries{}
        to interface ifIndex values, so we can store them with the interface and display as needed.
        It ***appears*** the poe_port index is "power-supply-number.port-number", all 1-based.
        So power entry "1.1" is interface ge-0/0/0, and power entry "1.5" is ge-0/0/4
        """
        dprint("Juniper _map_poe_port_entries_to_interface()")
        for (pe_index, port_entry) in self.poe_port_entries.items():
            # we take the ending part of "1.5" as the index
            (module, port) = port_entry.index.split('.')
            module = int(module) - 1    # 0-based!
            port = int(port) - 1        # 0-based!
            # find the matching interface:
            for (if_index, iface) in self.interfaces.items():
                if_name = f"ge-{module}/0/{port}"
                if iface.name == if_name:
                    dprint(f"   PoE Port Map FOUND {iface.name}")
                    iface.poe_entry = port_entry
                    if port_entry.detect_status > POE_PORT_DETECT_DELIVERING:
                        warning = f"PoE FAULT status ({port_entry.detect_status} = " \
                                  f"{poe_status_name[port_entry.detect_status]}) on interface {iface.name}"
                        self.add_warning(warning)
                        # log my activity
                        log = Log(user=self.request.user,
                                  type=LOG_TYPE_ERROR,
                                  ip_address=get_remote_ip(self.request),
                                  action=LOG_PORT_POE_FAULT,
                                  description=warning)
                        log.save()
                    break

    def _get_vlan_data(self):
        """
        Implement an override of vlan parsing to read Junos EX specific MIB
        Return 1 on success, -1 on failure
        """
        dprint("Juniper _get_vlan_data()\n")

        # first, call the standard snmp vlan reader
        super()._get_vlan_data()

        # try the Juniper L2 entries. FIrst the "tag" or index to vlan_id mapping:
        retval = self.get_snmp_branch('jnxL2aldVlanTag', self._parse_mibs_juniper_l2ald_vlans)
        if retval < 0:  # error
            return retval
        if retval > 0:  # we found something, read the rest
            retval = self.get_snmp_branch('jnxL2aldVlanName', self._parse_mibs_juniper_l2ald_vlans)
            if retval < 0:  # error
                return retval
            retval = self.get_snmp_branch('jnxL2aldVlanType', self._parse_mibs_juniper_l2ald_vlans)
            if retval < 0:  # error
                return retval
            retval = self.get_snmp_branch('jnxL2aldVlanFdbId', self._parse_mibs_juniper_l2ald_vlans)
            if retval < 0:  # error
                return retval
            return 1
        return 0

    def _parse_mibs_juniper_l2ald_vlans(self, oid, val):
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
                self.add_warning(f"Invalid vlan index {vlan_index} (jnxL2aldVlanName)")
            return True

        # vlan type, static or dynamic
        vlan_index = int(oid_in_branch(jnxL2aldVlanType, oid))
        if vlan_index:
            dprint(f"jnxL2aldVlanType {vlan_index} = {val}")
            val = int(val)
            if val == JNX_VLAN_TYPE_STATIC:
                status = VLAN_STATUS_PERMANENT
            elif val == JNX_VLAN_TYPE_DYNAMIC:
                status = VLAN_STATUS_DYNAMIC
            else:   # should not happen!
                status = VLAN_STATUS_OTHER
            try:
                self.vlans[self.vlan_id_by_index[vlan_index]].status = status
            except KeyError:
                # should not happen!
                self.add_warning(f"Invalid vlan index {vlan_index} (jnxL2aldVlanType)")
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
                self.add_warning(f"Invalid vlan index {vlan_index} (jnxL2aldVlanFdbId)")
            return True
        return False

    def set_interface_admin_status(self, interface=False, status=-1):
        self.error = Error(status=True,
                           description=f"set_interface_admin_status(): Not implemented yet!")
        return False

    def set_interface_poe_status(self, interface=False, status=-1):
        self.error = Error(status=True,
                           description=f"set_interface_poe_status(): Not implemented yet!")
        return False

    def set_interface_description(self, interface=False, description=""):
        self.error = Error(status=True,
                           description=f"set_interface_description(): Not implemented yet!")
        return False

    def set_interface_untagged_vlan(self, interface, old_vlan_id, new_vlan_id):
        self.error = Error(status=True,
                           description=f"set_interface_untagged_vlan(): Not implemented yet!")
        return False
