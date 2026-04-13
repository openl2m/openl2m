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

from switches.constants import LOG_TYPE_ERROR, LOG_SAVE_SWITCH
from switches.connect.constants import IF_TYPE_ETHERNET, LACP_IF_TYPE_AGGREGATOR, LACP_IF_TYPE_MEMBER
from switches.connect.classes import Interface
from switches.connect.snmp.connector import SnmpConnector, oid_in_branch
from switches.connect.snmp.constants import active, createAndGo, dot1qPvid, dot3adAggPortActorAdminKey
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
    aristaConfigCopyName,
    aristaConfigCopyId,
    aristaConfigCopySourceUri,
    aristaConfigCopyDestUri,
    aristaConfigCopyRowStatus,
    # default_job_id,
    save_job_id,
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
        self.description = "Arista Networks EOS SNMP driver"
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
        self.can_edit_tags = False  # False until we can test. True if this driver can edit 802.1q tagged vlans on interfaces

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

        # we recommend using the Arista eAPI driver, tell the user so:
        self.add_warning(
            warning="We recommend using the Arista eAPI driver for this device. Please contact your OpenL2M administrator!",
            add_log=False,
        )

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
        for iface in self.interfaces.values():
            if iface.type == IF_TYPE_ETHERNET and iface.untagged_vlan == -1:
                iface.is_routed = True
        return True

    def _get_lacp_data(self) -> bool:
        """
        Read the IEEE LACP mib (IEEE8023-LAG-MIB) for "port-channel" interfaces.
        Note: Arista implements this incorrectly, so we have to override the standard function in SnmpConnector() !
        Returns True on success, False on failure
        """

        # Get the admin key or "index" for aggregate interfaces - same as standard.
        retval = self.get_snmp_branch(branch_name="dot3adAggActorAdminKey", parser=self._parse_mibs_lacp_admin_key)
        if retval < 0:
            self.add_warning("Error getting 'LACP-Aggregate-Admin-Key' (dot3adAggActorAdminKey)")
            return False

        # If there are aggregate interfaces, then get the admin key or "index" for physical member interfaces
        # Normally (ie standard SNMP), this maps back to the logical or actor aggregates above in dot3adAggActorAdminKey
        # for Arista versions we tested (4.33.4M), this gives the port-channel number, eg. for "port-channel9", returns 9

        if retval > 0:
            retval = self.get_snmp_branch(
                branch_name="dot3adAggPortActorAdminKey", parser=self._parse_mibs_lacp_member_port_arista
            )
            if retval < 0:
                self.add_warning("Error getting 'LACP-Port-Admin-Key' (dot3adAggPortActorAdminKey)")
                return False

        #
        # # this is a shortcut to find aggregates and members all in one, but does not work for every device.
        # retval = self.get_snmp_branch(branch_name='dot3adAggPortAttachedAggID', parser=self._parse_mibs_lacp)
        # if retval < 0:
        #     self.add_warning("Error getting 'LACP-Port-AttachedAggID' (dot3adAggPortAttachedAggID)")
        #     return False
        #

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
            snmp_type="u",
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

        retval = self.get_snmp_branch(branch_name="aristaVrfEntry", parser=self._parse_mib_arista_vrf_entries)
        if retval < 0:
            self.add_warning(warning="Error getting VRF info from the Arista MPLS tables (aristaVrfEntry)")
        if self.vrfs:
            retval = self.get_snmp_branch(
                branch_name="aristaVrfIfMembership", parser=self._parse_mib_arista_vrf_members
            )
            # see if we can get router IP addresses in these VRFs:
            for vrf_name in self.vrfs:
                dprint(f"Getting IP addresses in VRF '{vrf_name}'")
                self._set_snmp_session(com_or_ctx=vrf_name)
                self._get_my_ip_addresses()
            # reset to default for the next call
            self._set_snmp_session()
        return True

    #
    # THIS DOES NOT APPEAR TO WORK with either default_job_id, or save_job_id
    #
    def save_running_config(self):
        """ Save the current config to startup.

        Returns:
            (bool) - True if this succeeds, False on failure. self.error() will be set in that case
        """
        dprint("SnmpConnectorAristaEOS().save_running_config()")

        """
        To save the running-configuration to the startup-configuration on an Arista switch via SNMP,
        use a set request (SNMP SET) to activate the copy command MIB.

            Source OID: 1.3.6.1.4.1.30065.3.7.1.1.3.7.100.101.102.97.117.108.116.0 (OctetString: "running-config")
            Destination OID: 1.3.6.1.4.1.30065.3.7.1.1.4.7.100.101.102.97.117.108.116.0 (OctetString: "startup-config")
            Status OID (Action): 1.3.6.1.4.1.30065.3.7.1.1.11.7.100.101.102.97.117.108.116.0 (Integer32: 1 to execute)

        See Arista Config-COPY mib at
            https://www.arista.com/assets/data/docs/MIBS/ARISTA-CONFIG-COPY-MIB.txt
            https://mibs.observium.org/mib/ARISTA-CONFIG-COPY-MIB/
        Also look at https://www.reddit.com/r/Arista/comments/v6tfs9/save_config_via_snmp/
        """
        # we're sending the commands using the 'default' job as an atomic group of set()
        try:
            # this creates a new row
            # THIS DOES NOT APPEAR TO WORK with either default_job_id, or save_job_id
            self.set(oid=f"{aristaConfigCopyRowStatus}.{save_job_id}.0", value=createAndGo, snmp_type="i")

            self.set(oid=f"{aristaConfigCopyName}.{save_job_id}.0", value="openl2m-save", snmp_type="s")
            self.set(oid=f"{aristaConfigCopyId}.{save_job_id}.0", value=23, snmp_type="i")

            # set source entry in new row
            self.set(oid=f"{aristaConfigCopySourceUri}.{save_job_id}.0", value="running-config", snmp_type="s")
            # set dest entry in new row
            self.set(oid=f"{aristaConfigCopyDestUri}.{save_job_id}.0", value="startup-config", snmp_type="s")
            # activate the new row
            self.set(oid=f"{aristaConfigCopyRowStatus}.{save_job_id}.0", value=active, snmp_type="i")

            # all OK
            return True

        except Exception as err:
            dprint(f"ERROR in set: {err}")

        # oid_values = [
        #     (f"{aristaConfigCopyRowStatus}.{save_job_id}.0", createAndGo, "i"),     # this creates a new row
        #     #(f"{aristaConfigCopyName}.{save_job_id}.0", "openl2m-save", "s"),
        #     #(f"{aristaConfigCopyId}.{save_job_id}.0", 23, "i"),
        #     (f"{aristaConfigCopySourceUri}.{save_job_id}.0", "running-config", "s"),    # set source entry in new row
        #     (f"{aristaConfigCopyDestUri}.{save_job_id}.0", "startup-config", "s"),      # set dest entry in new row
        #     (f"{aristaConfigCopyRowStatus}.{save_job_id}.0", active, "i"),              # activate the new row
        # ]
        # # go execute the set of actions:
        # if self.set_multiple(oid_values=oid_values):
        #     # thiss schedules a job. We do NOT check return at later time, we just assume this worked!
        #     return True
        #
        # dprint("ERROR Caught in set_multiple()!")

        self.error.description = "Save running-config returned error!"
        self.add_log(
            type=LOG_TYPE_ERROR, action=LOG_SAVE_SWITCH, description=f"{self.error.description} - {self.error.details}"
        )
        return False

    def _parse_mibs_lacp_member_port_arista(self, oid: str, val: str) -> bool:
        """
        Parse a single OID with data returned from the LACP MIBs.
        Note: this is NON-standard. This parses the 'port-channel' that a specific ifIndex is a member of!

        SNMP data parsed:   <dot3adAggPortActorAdminKey>.<member-if-index> = <val>
        (where oid = dot3adAggPortActorAdminKey.member-if-index)

        Params:
            oid (str): the SNMP OID to parse
            val (str): the value of the SNMP OID we are parsing

        Returns:
            (boolean): True if we parse the OID, False if not.
        """
        dprint(f"_parse_mibs_lacp_member_port_arista() {str(oid)}, len = {len(val)}, type = {str(type(val))}")

        # this gets the port-channel number for a LACP member interface ifIndex. Note this is NON-standard!
        member_if_index = oid_in_branch(dot3adAggPortActorAdminKey, oid)
        # note that member_if_index is an integer according to MIB, but oid_in_branc() parsing
        # returns a string value. This is used as the interfaces{} dictionary key!!!
        # 'val' is the po-channel number, eg. '9' = port-channel9
        # port-channel number is always > 0 !
        if member_if_index and int(val) > 0:
            # this interface is an lacp member!
            member = self.get_interface_by_key(key=member_if_index)
            if member:
                # can we find an aggregate with this key value ?
                po_name = f"Port-Channel{val}"
                dprint(f"LACP = {po_name}, member: {member.name}")
                port_channel = self.get_interface_by_name(name=po_name)
                if port_channel:
                    if port_channel.lacp_type == LACP_IF_TYPE_AGGREGATOR:
                        dprint(f"LACP interface found: {port_channel.name}")
                        # the current interface is a member of this aggregate iface !
                        member.lacp_type = LACP_IF_TYPE_MEMBER
                        member.lacp_master_index = int(val)
                        member.lacp_master_name = port_channel.name
                        # add our name to the member list of the aggregate interface
                        port_channel.lacp_members[member_if_index] = member.name
                else:
                    dprint(f"ERROR: {po_name} Interface() NOT FOUND!!! (huh?)")
            return True

        # we did not parse the OID.
        return False

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
