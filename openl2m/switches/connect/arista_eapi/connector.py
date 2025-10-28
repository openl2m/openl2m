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
import requests

# used to disable unknown SSL cert warnings:
import urllib3
import traceback

from switches.connect.classes import Interface, PoePort, NeighborDevice, Transceiver, Vlan, EthernetAddress
from switches.connect.connector import Connector
from switches.connect.constants import (
    VLAN_ADMIN_DISABLED,
    POE_PORT_ADMIN_DISABLED,
    POE_PORT_ADMIN_ENABLED,
    VLAN_ADMIN_DISABLED,
    IF_DUPLEX_HALF,
    IF_DUPLEX_FULL,
    IF_TYPE_OTHER,
    IF_TYPE_LOOPBACK,
    IF_TYPE_VIRTUAL,
    IF_TYPE_ETHERNET,
    IF_TYPE_LAGG,
    LACP_IF_TYPE_MEMBER,
    LACP_IF_TYPE_AGGREGATOR,
    LLDP_CHASSIC_TYPE_ETH_ADDR,
    LLDP_CAPABILITIES_BRIDGE,
    LLDP_CAPABILITIES_ROUTER,
    LLDP_CAPABILITIES_WLAN,
    LLDP_CAPABILITIES_PHONE,
    IANA_TYPE_OTHER,
    IANA_TYPE_IPV4,
    IANA_TYPE_IPV6,
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
        # force READ-ONLY for now
        self.read_only = True
        if switch.description:
            self.add_more_info('System', 'Description', switch.description)
        # options supported:
        self.can_reload_all = True

    def get_my_basic_info(self) -> bool:
        """
        placeholder, to be implemented.
        """
        dprint("AristaApiConnector get_my_basic_info()")
        self.hostname = self.switch.hostname

        if not self._open_device():
            return False  # self.error already set!

        try:
            # the Arista eAPI allows to bundle many commands into a single request through sending them as a list.
            # You can then parse the responses in a list, in order of the commands given.
            command_list = []
            command_list.append("show version")
            command_list.append("show vlan")
            command_list.append("show interfaces")
            command_list.append("show interfaces vlans")
            command_list.append("show interfaces transceiver properties")
            command_list.append("show vrf")

            # run the commands:
            json_data = self._arista_run_command(command=command_list)
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

                if if_data["lineProtocolStatus"] == 'up':
                    iface.admin_status = True
                    iface.oper_status = True
                else:
                    iface.oper_status = False
                    # what is admin status:
                    # not sure this is correct ?
                    if if_data["interfaceStatus"] == "errdisabled":
                        iface.admin_status = False

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
            #
            # command = "show interfaces vlans"
            # NOTE: on tagged interfaces this does NOT read the untagged vlan!
            data = json_data.get('result')[3]['interfaces']
            for if_name, vlan_data in data.items():
                dprint(f"Found VLAN info for: {if_name}")
                dprint(vlan_data)
                iface = self.get_interface_by_name(name=if_name)
                if iface:
                    dprint("   found Interface()")
                    if 'untaggedVlan' in vlan_data:
                        iface.untagged_vlan = int(vlan_data)
                    if 'taggedVlans' in vlan_data:
                        iface.is_tagged = True
                        for vlan_id in vlan_data['taggedVlans']:
                            iface.add_tagged_vlan(vlan_id=int(vlan_id))

            # we can read the switchport information to read the untagged vlans

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
            # read VRF info
            #
            # command = "show vrf"
            data = json_data.get('result')[5]['vrfs']
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
            json_data = self._arista_run_command(command=command_list)
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
                                    neighbor.management_address_type = IANA_TYPE_IPV4
                                    neighbor.management_address = addr["address"]
                                    mgmt_ipv4 = addr["address"]
                                case "ipv6":
                                    dprint(" is IPv6")
                                    neighbor.management_address_type = IANA_TYPE_IPV6
                                    neighbor.management_address = addr["address"]
                                    mgmt_ipv6 = addr["address"]
                                case _:
                                    dprint("Unknown management address type!")
                                    neighbor.management_address_type = IANA_TYPE_OTHER
                                    neighbor.management_address = addr["address"]

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
    # here we override the SSH command execution using Netmiko,
    # and implement it using the eAPI.
    #
    def netmiko_execute_command(self, command: str) -> bool:
        """
        Execute a single command on the device using eAPI.
        Save the command output to self.output
        On error, set self.error as needed.

        Args:
            command: the string the execute as a command on the device

        Returns:
            (boolean): True if success, False on failure.
                       On success, save the command output to self.output.
                       On failure, set self.error as applicable.
        """
        dprint(f"Arista netmiko_execute_command() '{command}'")

        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        try:
            # run the command:
            json_data = self._arista_run_command(command=command, format="text")
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

    def _arista_run_command(self, command, format="json", autoComplete=True):
        """Run a specifc Arista command on the router configured.
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
