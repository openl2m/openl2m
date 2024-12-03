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

from switches.connect.constants import IF_TYPE_ETHERNET
from switches.connect.classes import Interface
from switches.connect.snmp.connector import SnmpConnector, oid_in_branch
from switches.connect.snmp.constants import dot1qPvid
from switches.models import Switch, SwitchGroup
from switches.utils import dprint

from .constants import (
    aristaVrfRoutingStatus,
    aristaVrfRouteDistinguisher,
    # aristaVrfState, - currently not used.
    #    ARISTA_VRF_ACTIVE,
    #    ARISTA_VRF_ROUTING_IPV4_BIT,
    #    ARISTA_VRF_ROUTING_IPV6_BIT,
    aristaVrfIfMembership,
)


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
        # self.switch.read_only = False  # Arista support some mib variables as R/W
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

        # Netmiko is used for SSH connections. Here are some defaults a class can set.
        #
        # device_type:
        # if set, will be a value that will override (ie. hardcode) values from the
        # "Credentials Profile" (aka the NetmikoProfile() object)
        self.netmiko_device_type = "arista_eos"
        # no need to override default of netmiko_valid_device_types[]
        #
        # the command that should be sent to disable screen paging
        # defaults in the netmiko library to "terminal length 0"
        # self.netmiko_disable_paging_command = "terminal length 0"  # by default EOS cli sessions have paging disabled!

    def get_my_basic_info(self) -> bool:
        """
        We override "Get the basic info" to parse the vlans on interfaces.
        Default Arista interface is "switchport" on vlan 1.
        Arista 'routed' interfaces to no have a valid vlan.
        """
        dprint("SnmpConnectorAristaEOS.get_my_basic_info()")
        # first get all normal SNMP info, implemented in the super class:
        if not super().get_my_basic_info():
            return False
        # now run all interfaces and set routed if no valid vlan.
        for key, iface in self.interfaces.items():
            if iface.type == IF_TYPE_ETHERNET and iface.untagged_vlan == -1:
                iface.is_routed = True
        return True

    def set_interface_untagged_vlan(self, interface: Interface, new_vlan_id: int) -> bool:
        """
        Change the VLAN via the Q-BRIDGE MIB
        According to Arista, you only need to write the new vlan id to "dot1qPvid"
        return True on success, False on error and set self.error variables
        """
        dprint(f"arista_eos.set_interface_untagged_vlan(i={interface}, vlan={new_vlan_id})")
        if not interface:
            dprint("  Invalid interface!, returning False")
            return False
        # now check the Q-Bridge PortID
        if interface.port_id < 0:
            dprint(f"  Invalid interface.port_id ({interface.port_id}), returning False")
            return False
        dprint("   valid interface and port_id")
        # old_vlan_id = interface.untagged_vlan
        # set this switch port on the new vlan:
        # Q-BIRDGE mib: VlanIndex = Unsigned32
        dprint("Setting NEW VLAN on port")
        if not self.set(
            oid=f"{dot1qPvid}.{interface.port_id}",
            value=int(new_vlan_id),
            snmp_type='u',
            parser=self._parse_mibs_vlan_related,
        ):
            return False

        interface.untagged_vlan = new_vlan_id
        return True

    def get_my_vrfs(self):
        """Read the VRFs defined on this device.
            This reads 'aristaVrfEntry' items from the 'aristaVrfTable'
            defined in the vendor-specific ARISTA-VRF-MIB

        Args:
            none

        Returns:
            (bool): True on success, False on failure
        """
        dprint("SnmpConnectorAristaEOS.get_my_vrfs()")

        retval = self.get_snmp_branch(branch_name='aristaVrfEntry', parser=self._parse_mib_arista_vrf_entries)
        if retval < 0:
            self.add_warning(warning="Error getting VRF info from the Arista MPLS tables (aristaVrfEntry)")
        if self.vrfs:
            retval = self.get_snmp_branch(
                branch_name='aristaVrfIfMembership', parser=self._parse_mib_arista_vrf_members
            )
        return True

    def _parse_mib_arista_vrf_entries(self, oid: str, val: str) -> bool:
        """
        Parse Arista VRF mib entries. This gets added to self.vrfs

        Params:
            oid (str): the SNMP OID to parse
            val (str): the value of the SNMP OID we are parsing

        Returns:
            (boolean): True if we parse the OID, False if not.
        """
        dprint(f"SnmpConnectorAristaEOS._parse_mib_arista_vrf_entries() {str(oid)}")

        # routing status has bit for IPv4 and IPv6
        sub_oid = oid_in_branch(aristaVrfRoutingStatus, oid)
        if sub_oid:
            vrf_name = self._get_string_from_oid_index(oid_index=sub_oid)
            dprint(f"  VRF NAME = '{vrf_name}'")
            dprint("   VRF ipv4/6 routing")
            vrf = self.get_vrf_by_name(name=vrf_name)
            # parse IPv4 and IPv6 bits here:
            # TBD
            # if int(val) & ARISTA_VRF_ROUTING_IPV4_BIT:
            #     vrf.ipv4 = True
            # if int(val) & ARISTA_VRF_ROUTING_IPV6_BIT:
            #     vrf.ipv6 = True
            vrf.ipv4 = True
            vrf.ipv6 = True
            return True

        # the VRF RD:
        sub_oid = oid_in_branch(aristaVrfRouteDistinguisher, oid)
        if sub_oid:
            vrf_name = self._get_string_from_oid_index(oid_index=sub_oid)
            dprint(f"  VRF NAME = '{vrf_name}'")
            dprint("   VRF RD")
            vrf = self.get_vrf_by_name(name=vrf_name)
            vrf.rd = val
            return True

        # currently NOT used:
        # # state is enabled or disabled
        # sub_oid = oid_in_branch(aristaVrfState, oid)
        # if sub_oid:
        #     vrf_name = self._get_string_from_oid_index(oid_index=sub_oid)
        #     dprint(f"  VRF NAME = '{vrf_name}'")
        #     dprint("   VRF State")
        #     vrf = self.get_vrf_by_name(name=vrf_name)
        #     # set the state, active=True
        #     if int(val) == ARISTA_VRF_ACTIVE:
        #         vrf.state = True
        #     else:
        #         vrf.state = False
        #     return True

        # we did not parse:
        return False

    def _parse_mib_arista_vrf_members(self, oid: str, val: str) -> bool:
        """
        Parse Arista VRF interface membership entries.

        Params:
            oid (str): the SNMP OID to parse
            val (str): the value of the SNMP OID we are parsing

        Returns:
            (boolean): True if we parse the OID, False if not.
        """
        dprint(f"SnmpConnectorAristaEOS._parse_mib_arista_vrf_members() {str(oid)}")

        # aristaVrfIfMembership.<ifIndex> = "VRF-Name"
        sub_oid = oid_in_branch(aristaVrfIfMembership, oid)
        if sub_oid:
            dprint(f"    aristaVrfIfMembership ifIndex={sub_oid}, vrf='{val}'")
            # sub_oid is string representing the ifIndex integer. To get Interface(), we use it as string.
            iface = self.get_interface_by_key(key=sub_oid)
            # validate VRF name, and ifIndex
            if iface and val in self.vrfs:
                # get the interface:
                dprint(f"    interface '{iface.name}'")
                # add to the list of interfaces for this vrf
                if iface.name not in self.vrfs[val].interfaces:
                    self.vrfs[val].interfaces.append(iface.name)
                # assing this vrf name to the interface:
                iface.vrf_name = val
            return True

        # we did not parse:
        return False
