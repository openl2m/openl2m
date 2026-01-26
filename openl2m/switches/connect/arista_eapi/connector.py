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
import json
from rangeparser import RangeParser
import requests

# used to disable unknown SSL cert warnings:
import urllib3
import traceback

from switches.connect.classes import Interface, NeighborDevice, Transceiver, Vlan
from switches.connect.connector import Connector
from switches.connect.constants import (
    VLAN_ADMIN_DISABLED,
    #    POE_PORT_ADMIN_DISABLED,
    #    POE_PORT_ADMIN_ENABLED,
    IF_DUPLEX_HALF,
    IF_DUPLEX_FULL,
    IF_TYPE_OTHER,
    IF_TYPE_LOOPBACK,
    #    IF_TYPE_VIRTUAL,
    IF_TYPE_ETHERNET,
    IF_TYPE_LAGG,
    LACP_IF_TYPE_MEMBER,
    LACP_IF_TYPE_AGGREGATOR,
    LLDP_CHASSIC_TYPE_ETH_ADDR,
    LLDP_CAPABILITIES_BRIDGE,
    LLDP_CAPABILITIES_ROUTER,
    #    LLDP_CAPABILITIES_WLAN,
    #    LLDP_CAPABILITIES_PHONE,
    #    IANA_TYPE_OTHER,
    #    IANA_TYPE_IPV4,
    #    IANA_TYPE_IPV6,
)
from switches.connect.arista_eapi.utils import get_vlan_and_interface_from_string
from switches.models import Switch, SwitchGroup
from switches.utils import time_duration, dprint

#
# you can explore the eAPI used by going to the following URL on an Arista device:
# https://<ip-address/eapi/
# No creds needed to look around
#


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
        # can edit (most) entries
        self.read_only = False
        if switch.description:
            self.add_more_info('System', 'Description', switch.description)
        # capabilities supported by this eAPI driver:
        self.can_change_admin_status = True
        self.can_change_vlan = True
        self.can_edit_vlans = True  # if true, this driver can edit (create/delete) vlans on the device!
        self.can_set_vlan_name = True  # set to False if vlan create/delete cannot set/change vlan name!
        # self.can_change_poe_status = False - we do not have a test switch with PoE !
        self.can_change_description = True
        self.can_save_config = True  # do we have the ability (or need) to execute a 'save config' or 'write memory' ?
        self.can_reload_all = True  # if true, we can reload all our data (and show a button on screen for this)

    def get_my_basic_info(self) -> bool:
        """
        placeholder, to be implemented.
        """
        dprint("AristaApiConnector.get_my_basic_info()")
        self.hostname = self.switch.hostname

        if not self._open_device():
            return False  # self.error already set!

        try:
            # the Arista eAPI allows to bundle many commands into a single request through sending them as a list.
            # You can then parse the responses in a list, in order of the commands given.
            command_list = []
            command_list.append("show version")  # offset 0
            command_list.append("show vlan")  # offset 1
            command_list.append("show interfaces")  # offset 2
            # command_list.append("show interfaces vlans")    # offset 3
            command_list.append("show interfaces switchport")  # offset 3
            command_list.append("show interfaces transceiver properties")  # offset 4
            command_list.append("show port-channel")  # offset 5
            command_list.append("show vrf")  # offset 6

            # run the commands:
            json_data = self._eapi_run_command(command=command_list)
            # The 'result' key will contain a list of command outputs, in order of commands given.

            #
            # get device version
            #
            # command = "show version"
            data = json_data.get('result')[0]
            self.add_more_info('System', 'Model', data['modelName'])
            self.add_more_info('System', 'Serial', data['serialNumber'])
            self.add_more_info('System', 'OS Version', data['version'])
            self.add_more_info('System', 'Uptime', time_duration(int(data['uptime'])))

            #
            # get vlan info
            #
            # command = "show vlan"
            data = json_data.get('result')[1]['vlans']
            for vlan_id, vlan_data in data.items():
                dprint(f"Found vlan: {vlan_id}")
                v = Vlan(id=int(vlan_id))
                v.name = vlan_data["name"]
                if vlan_data["status"] != "active":
                    v.admin_status = VLAN_ADMIN_DISABLED
                self.add_vlan(v)

            #
            # get interface information
            #
            # command = "show interfaces"
            data = json_data.get('result')[2]
            for if_name, if_data in data["interfaces"].items():
                dprint(f"Found interface: {if_name}")
                dprint(f"IF_DATA=\n{if_data}\n")
                iface = Interface(if_name)
                iface.name = if_name

                match if_data["hardware"]:
                    case "ethernet":
                        iface.type = IF_TYPE_ETHERNET
                        iface.phys_addr = if_data["physicalAddress"]
                    case "loopback":
                        iface.type = IF_TYPE_LOOPBACK
                    case _:
                        iface.type = IF_TYPE_OTHER

                iface.description = if_data["description"]

                match if_data['interfaceStatus']:
                    case 'disabled':  # Admin-DOWN
                        # note this is default state:
                        iface.admin_status = False
                        iface.oper_status = False
                    case 'notconnect':  # Admin-UP but protocol-DOWN
                        iface.admin_status = True
                        iface.oper_status = False
                    case 'connected':  # UP/UP
                        iface.admin_status = True
                        if if_data["lineProtocolStatus"] == 'up':
                            iface.oper_status = True
                    # not sure this is correct ?
                    case "errdisabled":
                        iface.error_status = True
                    case _:
                        # unknown state ? should not happen...
                        self.add_warning(warning=f"Unknown state on {if_name}: {if_data['interfaceStatus']}")

                iface.speed = int(if_data["bandwidth"]) / 1000000  # bandwidth is in bps!

                if 'duplex' in if_data:
                    match if_data["duplex"]:
                        case "duplexFull":
                            iface.duplex = IF_DUPLEX_FULL
                        case "duplexHalf":
                            iface.duplex = IF_DUPLEX_HALF

                match if_data["forwardingModel"]:
                    case "routed":
                        if iface.type != IF_TYPE_LOOPBACK:  # loopback are always routed :-)
                            iface.is_routed = True

                iface.mtu = int(if_data["mtu"])

                # parse ipv4 addresses of this interface:
                if "interfaceAddress" in if_data:
                    for addr in if_data["interfaceAddress"]:
                        dprint(f"Found IPv4: {addr['primaryIp']}")
                        iface.add_ip4_network(address=f"{addr['primaryIp']['address']}/{addr['primaryIp']['maskLen']}")

                # # parse ipv6 addresses of this interface:
                if "interfaceAddressIp6" in if_data:
                    # "real" IPv6 addresses:
                    for addr in if_data['interfaceAddressIp6']['globalUnicastIp6s']:
                        dprint(f"Found IPv6: {addr}")
                        ipv6 = addr['address']
                        prefix_len = 64  # default for IPv6 subnets
                        # we need to get the netmask from the subnet:
                        netmask_pos = addr["subnet"].rfind("/")
                        if netmask_pos > 0:
                            # and get the mask len from that:
                            prefix_len = int(addr["subnet"][netmask_pos + 1 : :])
                        iface.add_ip6_network(address=ipv6, prefix_len=prefix_len)
                    # LinkLocal:
                    iface.add_ip6_network(address=f"{if_data['interfaceAddressIp6']['linkLocalIp6']['address']}")

                # done, add this interface to the list...
                self.add_interface(iface)

            #
            # get vlans on interfaces
            # we can read the switchport information to read the untagged and tagged vlans
            #
            # command = "show interfaces switchport"
            # data = json_data.get('result')[3]
            # dprint("=== SWITCHPORT DATA ===")
            # dprint(data)
            # dprint("============")
            data = json_data.get('result')[3]['switchports']
            for if_name, info in data.items():
                switchport = info['switchportInfo']
                dprint("===========")
                dprint(f"Found VLAN info for: {if_name}")
                dprint(info)
                dprint("===========")
                iface = self.get_interface_by_name(name=if_name)
                if iface:
                    dprint("   found Interface()")
                    if switchport['mode'] == 'trunk':
                        iface.is_tagged = True
                        # the PVID native untagged vlan is set in this attribute for trunks:
                        iface.untagged_vlan = int(switchport['trunkingNativeVlanId'])
                        if switchport['trunkAllowedVlans'] == 'ALL':
                            # add all vlans
                            for v in self.vlans.values():
                                iface.add_tagged_vlan(vlan_id=v.id)
                        else:
                            parser = RangeParser()
                            tagged_vlans = parser.parse(switchport['trunkAllowedVlans'])
                            for vlan_id in tagged_vlans:
                                iface.add_tagged_vlan(vlan_id=vlan_id)
                    else:
                        # access mode:
                        iface.untagged_vlan = int(switchport['accessVlanId'])

            #
            # get optical transceiver data
            #
            # command = "show interfaces transceiver properties"
            data = json_data.get('result')[4]['interfaces']
            for if_name, trx_data in data.items():
                dprint(f"Found TRX for: {if_name}")
                dprint(trx_data)
                if trx_data["mediaType"].lower() == "not present":
                    continue
                iface = self.get_interface_by_name(name=if_name)
                if iface:
                    dprint("   found Interface()")
                    trx = Transceiver()
                    trx.type = trx_data["mediaType"]
                    iface.transceiver = trx

            #
            # get LACP port-channel interfaces
            #
            # command = "show port-channel"
            #
            # data = json_data.get('result')[5]
            # dprint("=== Port-Channel DATA ===")
            # dprint(data)
            # dprint("============")
            data = json_data.get('result')[5]['portChannels']
            for po_name, po_info in data.items():
                # does this port-channel exist ?
                port_channel = self.get_interface_by_name(name=po_name)
                if port_channel:
                    dprint(f"Found Port-Channel Interface() for {po_name}")
                    port_channel.type = IF_TYPE_LAGG
                    port_channel.lacp_type = LACP_IF_TYPE_AGGREGATOR
                    # find the member interfaces:
                    member_type_list = ['inactivePorts', 'inactivePorts']
                    for member_type in member_type_list:
                        for member_name, member_info in po_info[member_type].items():
                            member = self.get_interface_by_name(name=member_name)
                            if member:
                                member.lacp_type = LACP_IF_TYPE_MEMBER
                                member.lacp_master_name = po_name
                                member.lacp_master_index = 1
                                # add to list of port-channel
                                port_channel.lacp_members[member.key] = member.name

            #
            # read VRF info
            #
            # command = "show vrf"
            data = json_data.get('result')[6]['vrfs']
            for name, vrf_data in data.items():
                dprint(f"Found vrf: {name}")
                if name == "default":  # the non-VRF or default routing table.
                    continue
                v = self.get_vrf_by_name(name=name)
                v.set_rd(rd=vrf_data["routeDistinguisher"])
                if vrf_data["protocols"]["ipv4"]["supported"]:
                    v.set_ipv4()
                if vrf_data["protocols"]["ipv6"]["supported"]:
                    v.set_ipv6()
                # see if this has member interfaces:
                for if_name in vrf_data["interfaces"]:
                    dprint(f"  Member interface: {if_name}")
                    iface = self.get_interface_by_name(name=if_name)
                    if iface:
                        dprint("   found Interface()")
                        v.interfaces.append(if_name)
                        iface.vrf_name = name

        except Exception as err:
            dprint(f"  ERROR running '{command_list}': {err}")
            self.error.status = True
            self.error.description = f"Error running eAPI command = '{command_list}'!"
            self.error.details = f"Cannot read device information: {format(err)}"
            self.add_warning(
                warning=f"Cannot read device information: {repr(err)} ({str(type(err))}) => {traceback.format_exc()}"
            )
            return False

        # the REST API gives responses in alphbetic order, eg 1/1/10 before 1/1/2.
        # sort this to the human natural order we expect:
        self.set_interfaces_natural_sort_order()

        return True

    def get_my_client_data(self) -> bool:
        '''
        read mac addressess, and lldp neigbor info.
        Not yet fully supported in AOS-CX API.
        return True on success, False on error and set self.error variables
        '''
        dprint("AristaApiConnector.get_my_client_data()")

        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        try:
            # the Arista eAPI allows to bundle many commands into a single request through sending them as a list.
            # You can then parse the responses in a list, in order of the commands given.
            command_list = []
            command_list.append("show mac address-table")
            command_list.append("show arp vrf all")
            command_list.append("show ipv6 neighbors vrf all")
            command_list.append("show lldp neighbors detail")

            # run the commands:
            json_data = self._eapi_run_command(command=command_list)
            # The 'result' key will contain a list of command outputs, in order of commands given.
            # dprint(f"RETURN:\n{json_data}")

            #
            # get Layer 2 MAC/ETHERNET info
            #
            # command = "show mac address-table"
            dprint("\n--- ETHERNET ADDRESSES ---\n")
            data = json_data.get('result')[0]
            for mac in data['unicastTable']['tableEntries']:
                dprint(f"Ethernet: {mac}")
                # add this to the known addressess:
                if mac['interface'] == 'Router':
                    # internal ethernet on the Arista device
                    dprint("  Ignored!")
                    continue
                self.add_learned_ethernet_address(
                    if_name=mac['interface'], eth_address=mac['macAddress'], vlan_id=int(mac['vlanId'])
                )

            #
            # get IPV4 ARP data
            #
            # command = "show arp vrf all"
            dprint("\n--- ARP ---\n")
            data = json_data.get('result')[1]
            for vrf_name, vrf_arp in data['vrfs'].items():
                dprint(f"VRF: {vrf_name}")
                for arp in vrf_arp['ipV4Neighbors']:
                    dprint(f"  ARP = {arp}")
                    (vlan_id, if_name) = get_vlan_and_interface_from_string(arp['interface'])
                    dprint(f"    Adding to if_name: {if_name}, vlan: {vlan_id}")
                    self.add_learned_ethernet_address(
                        if_name=if_name,
                        eth_address=arp['hwAddress'],
                        vlan_id=vlan_id,
                        ip4_address=arp['address'],
                    )

            #
            # get IPV6 Neighbors
            #
            # command = "show ipv6 neighbors vrf all"
            dprint("\n--- IPV6 ND ---\n")
            data = json_data.get('result')[2]
            for vrf_name, vrf_nd in data['vrfs'].items():
                dprint(f"VRF: {vrf_name}")
                for nd in vrf_nd['ipV6Neighbors']:
                    dprint(f"  ND = {nd}")
                    (vlan_id, if_name) = get_vlan_and_interface_from_string(nd['interface'])
                    dprint(f"    Adding to if_name: {if_name}, vlan_id: {vlan_id}")
                    self.add_learned_ethernet_address(
                        if_name=if_name,
                        eth_address=nd['hwAddress'],
                        vlan_id=vlan_id,
                        ip6_address=nd['address'],
                    )

            #
            # LLDP neighbors
            #
            # command = "show lldp neigbors"
            dprint("\n--- LLDP NEIGHBORS ---\n")
            data = json_data.get('result')[3]['lldpNeighbors']
            for if_name, nb_data in data.items():
                dprint(f"LLDP on {if_name}")
                for nb in nb_data['lldpNeighborInfo']:
                    dprint(f" Neighbor {nb['systemName']} = {nb}")
                    # get an OpenL2M NeighborDevice()
                    neighbor = NeighborDevice(nb["chassisId"])
                    neighbor.set_sys_name(nb['systemName'])
                    neighbor.set_sys_description(nb['systemDescription'])
                    # parse neighbor remote interface info:
                    if "neighborInterfaceInfo" in nb:
                        neighbor.port_name = nb['neighborInterfaceInfo']['interfaceId_v2']
                        neighbor.set_port_description(nb['neighborInterfaceInfo']['interfaceDescription'])

                    # management addresses given?
                    mgmt_ipv4 = ""  # used to register ethernet address.
                    mgmt_ipv6 = ""
                    if "managementAddresses" in nb:
                        for addr in nb['managementAddresses']:
                            dprint(f" Mgmt addr: {addr}")
                            # Needs parsing...
                            match addr["addressType"]:
                                case "ipv4":
                                    dprint(" is IPv4")
                                    neighbor.management_address_v4 = addr["address"]
                                    mgmt_ipv4 = addr["address"]
                                case "ipv6":
                                    dprint(" is IPv6")
                                    neighbor.management_address_v6 = addr["address"]
                                    mgmt_ipv6 = addr["address"]
                                case _:
                                    # we cannot handle this!
                                    dprint("Unknown management address type!")

                    neighbor.set_chassis_string(nb['chassisId'])
                    if nb['chassisIdType'] == 'macAddress':
                        neighbor.set_chassis_type(LLDP_CHASSIC_TYPE_ETH_ADDR)
                        # add this ethernet address to our interface data
                        # NOTE: still need to add the ipv4/v6 management addresses:
                        self.add_learned_ethernet_address(
                            if_name=if_name,
                            eth_address=neighbor.chassis_string,
                            # vlan_id = vlan_id,
                            ip4_address=mgmt_ipv4,
                            ip6_address=mgmt_ipv6,
                        )

                    # remote device capabilities:
                    for c, value in nb['systemCapabilities'].items():
                        match c:
                            case "bridge":
                                if value:
                                    neighbor.set_capability(LLDP_CAPABILITIES_BRIDGE)
                            case "router":
                                if value:
                                    neighbor.set_capability(LLDP_CAPABILITIES_ROUTER)
                            # there are likely other values, we just have not seen those yet!

                    # add to device interface:
                    self.add_neighbor_object(if_name, neighbor)

        except Exception as err:
            dprint(f"  ERROR running '{command_list}': {err}")
            self.error.status = True
            self.error.description = f"Error running eAPI command = '{command_list}'!"
            self.error.details = f"Cannot read device information: {format(err)}"
            self.add_warning(
                warning=f"Cannot read device information: {repr(err)} ({str(type(err))}) => {traceback.format_exc()}"
            )
            return False

        return True

    #
    # set interface admin status (up/down)
    #
    def set_interface_admin_status(self, interface: Interface, new_state: bool) -> bool:
        '''
        Set the interface to the requested state (up or down)

        Args:
            interface = Interface() object for the requested port
            new_state = True / False  (enabled/disabled)

        Returns:
            return True on success, False on error and set self.error variables
        '''
        # interface.admin_status = new_state
        dprint(f"AristaApiConnector.set_interface_admin_status() for {interface.name} to {bool(new_state)}")

        if new_state:
            status = "no shutdown"
        else:
            status = "shutdown"
        cmds = [
            "configure terminal",
            f"interface {interface.name}",
            f"{status}",
            "end",
        ]
        dprint(f"Running Commands:\n{cmds}")
        try:
            # run the command:
            json_data = self._eapi_run_command(command=cmds, format="json")
            # The 'result' key will contain a list of command output.
            dprint(f"RETURN:\n{json_data}")
            if 'error' in json_data:
                # some error occured !
                dprint(f"  ERROR running command!")
                error_code = json_data['error']['code']
                error_msg = json_data['error']['message']
                self.error.status = True
                self.error.description = (
                    f"Error '{json_data['error']['code']}' running eAPI commands: '{json_data['error']['message']}'"
                )
                self.error.details = f"Cannot set interface admin status. Full return data: {json_data}"
                self.add_warning(warning=f"Cannot set interface admin status: {json_data}")
                return False

        except Exception as err:
            dprint(f"  ERROR running '{cmds}': {err}")
            self.error.status = True
            self.error.description = f"Error running eAPI commands = '{cmds}'!"
            self.error.details = f"Cannot set interface admin status: {format(err)}"
            self.add_warning(
                warning=f"Cannot set interface admin status: {repr(err)} ({str(type(err))}) => {traceback.format_exc()}"
            )
            return False

        # call the Connector() class for bookkeeping
        super().set_interface_admin_status(interface=interface, new_state=new_state)
        return True

    #
    # set interface description
    #
    def set_interface_description(self, interface: Interface, description: str) -> bool:
        '''
        Set the interface description (aka. description) to the string

        Args:
            interface = Interface() object for the requested port
            description = a string with the requested text

        Returns:
            return True on success, False on error and set self.error variables
        '''
        # interface.admin_status = new_state
        dprint(f"AristaApiConnector.set_interface_description() for {interface.name} to '{description}'")

        if description:
            description_cmd = f"description {description}"
        else:
            description_cmd = "no description"

        cmds = [
            "configure terminal",
            f"interface {interface.name}",
            description_cmd,
            "end",
        ]
        dprint(f"Running Commands:\n{cmds}")
        try:
            # run the command:
            json_data = self._eapi_run_command(command=cmds, format="json")
            # The 'result' key will contain a list of command output.
            dprint(f"RETURN:\n{json_data}")
            if 'error' in json_data:
                # some error occured !
                dprint(f"  ERROR running command!")
                error_code = json_data['error']['code']
                error_msg = json_data['error']['message']
                self.error.status = True
                self.error.description = (
                    f"Error '{json_data['error']['code']}' running eAPI commands: '{json_data['error']['message']}'"
                )
                self.error.details = f"Cannot set interface description. Full return data: {json_data}"
                self.add_warning(warning=f"Cannot set interface description: {json_data}")
                return False

        except Exception as err:
            dprint(f"  ERROR running '{cmds}': {err}")
            self.error.status = True
            self.error.description = f"Error running eAPI commands = '{cmds}'!"
            self.error.details = f"Cannot set interface description: {format(err)}"
            self.add_warning(
                warning=f"Cannot set interface description: {repr(err)} ({str(type(err))}) => {traceback.format_exc()}"
            )
            return False

        # call the Connector() class for bookkeeping
        super().set_interface_description(interface=interface, description=description)
        return True

    def set_interface_untagged_vlan(self, interface: Interface, new_vlan_id: int) -> bool:
        """
        Override the VLAN change, this is done Comware specific using the Comware VLAN MIB
        return True on success, False on error and set self.error variables
        """
        dprint(
            f"AristaApiConnector().set_interface_untagged_vlan() port {interface.name} to {new_vlan_id} ({type(new_vlan_id)})"
        )
        new_vlan = self.get_vlan_by_id(new_vlan_id)
        if not new_vlan:
            self.error.status = True
            self.error.description = f"Cannot find Vlan object for vlan {new_vlan_id} for port '{interface.name}'"
            self.error.details = ""
            return False
        if interface:
            if interface.is_tagged:
                dprint("Tagged/Trunk Mode!")
                # set the TRUNK_NATIVE_VLAN OID:
                cmds = [
                    "configure terminal",
                    f"interface {interface.name}",
                    f"switchport trunk native vlan {new_vlan_id}",
                    "end",
                ]
            else:
                # regular access mode untagged port:
                dprint("Acces Mode!")
                cmds = [
                    "configure terminal",
                    f"interface {interface.name}",
                    f"switchport access vlan {new_vlan_id}",
                    "end",
                ]

            dprint(f"Running Commands:\n{cmds}")
            try:
                # run the command:
                json_data = self._eapi_run_command(command=cmds, format="json")
                # The 'result' key will contain a list of command output.
                dprint(f"RETURN:\n{json_data}")
                if 'error' in json_data:
                    # some error occured !
                    dprint(f"  ERROR running command!")
                    error_code = json_data['error']['code']
                    error_msg = json_data['error']['message']
                    self.error.status = True
                    self.error.description = (
                        f"Error '{json_data['error']['code']}' running eAPI commands: '{json_data['error']['message']}'"
                    )
                    self.error.details = f"Cannot set interface vlan. Full return data: {json_data}"
                    self.add_warning(warning=f"Cannot set interface vlan: {json_data}")
                    return False

            except Exception as err:
                dprint(f"  ERROR running '{cmds}': {err}")
                self.error.status = True
                self.error.description = f"Error running eAPI commands = '{cmds}'!"
                self.error.details = f"Cannot set interface vlan: {format(err)}"
                self.add_warning(
                    warning=f"Cannot set interface vlan: {repr(err)} ({str(type(err))}) => {traceback.format_exc()}"
                )
                return False

            # all OK - do bookkeeping.
            super().set_interface_untagged_vlan(interface=interface, new_vlan_id=new_vlan_id)
            return True
        # interface not found, return False!
        return False

    def vlan_create(self, vlan_id: int, vlan_name: str) -> bool:
        '''
        Create a new vlan on this device. Upon success, this then needs to call the base class for book keeping!

        Args:
            id (int): the vlan id
            name (str): the name of the vlan

        Returns:
            True on success, False on error and set self.error variables.
        '''
        dprint(f"AristaApiConnector.vlan_create() for vlan {vlan_id} = '{vlan_name}'")

        cmds = [
            "configure terminal",
            f"vlan {vlan_id}",
            f"name {vlan_name}",
            "end",
        ]

        if self._run_commands(commands=cmds, action=f"create vlan {vlan_id}"):
            # all OK, now do the book keeping
            super().vlan_create(vlan_id=vlan_id, vlan_name=vlan_name)
            return True

        return False

    def vlan_edit(self, vlan_id: int, vlan_name: str) -> bool:
        '''
        Edit the vlan name. Upon success, this then needs to call the base class for book keeping!

        Args:
            id (int): the vlan id to edit
            name (str): the new name of the vlan

        Returns:
            True on success, False on error and set self.error variables.
        '''
        dprint(f"AristaApiConnector.vlan_edit() for vlan {vlan_id} = '{vlan_name}'")

        vlan = self.get_vlan_by_id(vlan_id)
        if not vlan:
            self.error.status = True
            self.error.description = f"Vlan {vlan_id} does not exist!"
            self.error.details = ""
            return False

        if vlan_name:
            cmds = [
                "configure terminal",
                f"vlan {vlan_id}",
                f"name {vlan_name}",
                "end",
            ]
        else:
            cmds = [
                "configure terminal",
                f"vlan {vlan_id}",
                f"no name",
                "end",
            ]

        if self._run_commands(commands=cmds, action=f"rename vlan {vlan_id}"):
            # all OK, now do the book keeping
            super().vlan_edit(vlan_id=vlan_id, vlan_name=vlan_name)
            return True

        return False

    def vlan_delete(self, vlan_id: int) -> bool:
        '''
        Delete the vlan. Upon success, this then needs to call the base class for book keeping!

        Args:
            id (int): the vlan id to edit

        Returns:
            True on success, False on error and set self.error variables.
        '''
        dprint(f"AristaApiConnector.vlan_delete() for vlan {vlan_id}")

        vlan = self.get_vlan_by_id(vlan_id)
        if not vlan:
            self.error.status = True
            self.error.description = f"Vlan {vlan_id} does not exist!"
            self.error.details = ""
            return False

        cmds = [
            "configure terminal",
            f"no vlan {vlan_id}",
            "end",
        ]

        if self._run_commands(commands=cmds, action=f"delete vlan {vlan_id}"):
            # all OK, now do the book keeping
            super().vlan_delete(vlan_id=vlan_id)
            return True

        return False

    def save_running_config(self) -> bool:
        """
        save the current config to startup via api.

        Returns:
            (bool) - True if this succeeds, False on failure. self.error() will be set in that case
        """
        dprint("AristaApiConnector().save_running_config()")

        cmds = [
            "write memory",
        ]

        return self._run_commands(commands=cmds, action="save configuration")

    #
    # here we override the SSH command execution using Netmiko,
    # and implement it using the eAPI.
    #
    def _execute_command(self, command: str) -> bool:
        """
        Execute a single command on the device using eAPI.
        Save the command output to self.output
        On error, set self.error as needed.

        Args:
            command: the string the execute as a command on the device

        Returns:
            True if success, False on failure.
            On success, save the command output to self.output.
            On failure, set self.error as applicable.
        """
        dprint(f"Arista _execute_command() '{command}'")

        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        try:
            # run the command:
            json_data = self._eapi_run_command(command=command, format="text")
            # The 'result' key will contain a list of command output.
            # dprint(f"RETURN:\n{json_data}")
            self.netmiko_output = json_data.get('result')[0]['output']
            return True
        except Exception as err:
            dprint(f"  ERROR running '{command}': {err}")
            self.error.status = True
            self.error.description = f"Error running eAPI command = '{command}'!"
            self.error.details = f"Cannot read device information: {format(err)}"
            self.add_warning(
                warning=f"Cannot read device information: {repr(err)} ({str(type(err))}) => {traceback.format_exc()}"
            )
            return False

    def _open_device(self) -> bool:
        '''
        Arista API is stateless, so no need to open...
        return True on success, False on failure, and will set self.error
        '''
        dprint("Arista eAPI _open_device()")

        # do we have creds set?
        if not self.switch.netmiko_profile:
            self.error.status = True
            self.error.description = "Please configure a Credentials Profile to be able to connect to this device!"
            dprint("  _open_device: No Credentials!")
            return False

        # do we want to check SSL certificates?
        if not self.switch.netmiko_profile.verify_hostkey:
            dprint("  Cert warnings disabled in urllib3!")
            # disable unknown cert warnings
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            # or all warnings:
            # urllib3.disable_warnings()

        dprint("  _open_device() OK!")
        return True

    def _close_device(self) -> bool:
        '''
        eAPI is stateless, so close is not needed!
        '''
        dprint("Arist eAPI _close_device()")
        return True

    def _run_commands(self, commands: list, action: str) -> bool:
        """Run multiple commands using the eAPI.

        Args:
            commands: list of command string to run
            action: description of what this tries to accomplish. Will be used if this fails.

        Returns:
            True if all goes OK.
            False if this fails. the self.error() variable will be set with information about the failure.
        """
        dprint(f"AristaApiConnector().run_command:\n{commands}")

        try:
            # run the command:
            json_data = self._eapi_run_command(command=commands)
            # The 'result' key will contain a list of command output.
            dprint(f"RETURN:\n{json_data}")
            if 'error' in json_data:
                # some error occured !
                dprint(f"  ERROR running command!")
                error_code = json_data['error']['code']
                error_msg = json_data['error']['message']
                self.error.status = True
                self.error.description = (
                    f"Error '{json_data['error']['code']}' running eAPI commands: '{json_data['error']['message']}'"
                )
                self.error.details = f"Cannot {action}. Full return data: {json_data}"
                return False

        except Exception as err:
            dprint(f"  ERROR running '{commands}': {err}")
            self.error.status = True
            self.error.description = f"Error running eAPI commands = '{commands}'!"
            self.error.details = f"Cannot {action}: {format(err)}"
            return False
        # all OK
        dprint("All OK!")
        return True

    def _eapi_run_command(self, command, format="json", autoComplete=True):
        """Run a specifc Arista eAPI command on the router configured.
        By default, return as JSON, and allow for command auto-complete.

        """
        # eAPI endpoint
        url = f"https://{self.switch.primary_ip4}/command-api"

        # the API needs a list format for the command or multiple commands:
        if isinstance(command, list):
            cmds = command
        elif isinstance(command, str):
            cmds = [f"{command}"]
        else:
            # cannot handle this!
            raise Exception(f"Unknown command type: f{type(command)}")

        # JSON-RPC request payload for 'show ip route'
        payload = {
            "jsonrpc": "2.0",
            "method": "runCmds",
            "params": {
                "format": format,
                "timestamps": False,
                "autoComplete": autoComplete,
                "expandAliases": False,
                "version": 1,
                "cmds": cmds,
            },
            "id": 1,
        }

        # Headers for the request
        headers = {"Content-type": "application/json"}

        try:
            # Send the request
            response = requests.post(
                url,
                data=json.dumps(payload),
                headers=headers,
                auth=(self.switch.netmiko_profile.username, self.switch.netmiko_profile.password),
                verify=False,
            )
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error connecting to Arista switch (equests.exceptions.RequestException): {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Error decoding JSON response (json.JSONDecodeError): {e}")
        except KeyError as e:
            raise Exception(f"Unexpected JSON structure (KeyError): Missing key {e}")
        except Exception as e:
            raise Exception(f"Generic error caught in arista_run_command: {e}")
