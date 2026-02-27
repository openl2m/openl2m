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
HPE Comware REST API Connector

This implements a REST api driver from Comware devices. This follows the API docs outlined
in the HPE Comware NetConf documentation.
"""

from django.http.request import HttpRequest
import pprint
# from rangeparser import RangeParser

# used to disable unknown SSL cert warnings:
import base64
import json
import requests
import urllib3
# import traceback
from typing import List

from switches.connect.classes import Interface, Vlan, Transceiver, PoePort
# NeighborDevice,
from switches.connect.connector import Connector
from switches.connect.constants import (
    # VLAN_ADMIN_DISABLED,
    # POE_PORT_ADMIN_DISABLED,
    #POE_PORT_ADMIN_ENABLED,
    IF_DUPLEX_UNKNOWN,
    IF_DUPLEX_HALF,
    IF_DUPLEX_FULL,
    # IF_TYPE_OTHER,
    # IF_TYPE_LOOPBACK,
    # IF_TYPE_VIRTUAL,
    # IF_TYPE_ETHERNET,
    IF_TYPE_LAGG,
    LACP_IF_TYPE_MEMBER,
    LACP_IF_TYPE_AGGREGATOR,
    POE_PSE_STATUS_ON,
    POE_PSE_STATUS_OFF,
    POE_PSE_STATUS_FAULT,
    # LLDP_CHASSIC_TYPE_ETH_ADDR,
    # LLDP_CAPABILITIES_BRIDGE,
    # LLDP_CAPABILITIES_ROUTER,
    # LLDP_CAPABILITIES_WLAN,
    # LLDP_CAPABILITIES_PHONE,
    # IANA_TYPE_OTHER,
    # IANA_TYPE_IPV4,
    # IANA_TYPE_IPV6,
)
from switches.models import Switch, SwitchGroup
# from switches.utils import time_duration, dprint
from switches.utils import dprint

API_VERSION=1

REST_DEBUG = False  # for development only. If True, lots of REST debugging will be printed!
                    # also requires settings.DEBUG = True!

class HPECwRestConnector(Connector):
    """
    This implements an HPE Comware REST API connector object.
    """

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        # call the super class
        dprint("HPECwRestConnector __init__")
        super().__init__(request, group, switch)
        self.description = "HPE Comware REST API driver"
        self.vendor_name = "HPE/Aruba"
        # can edit (most) entries
        self.read_only = True
        if switch.description:
            self.add_more_info("System", "Description", switch.description)

        # this holds the REST api attributes
        self.base_url = f"https://{self.switch.primary_ip4}/api/v{API_VERSION}/"
        self.token: str = ""                    # REST token after username/password login
        self.token_timeout: str = ""            # time token expires
        self.headers: dict = {}                 # contains HTTP headers for GET/POST
        self.response = None                    # full response from request, in case user wants it!

        # login and get a REST token
        if not self._open_device():
            raise Exception(self.error.description)

        # capabilities supported by this eAPI driver:
        self.can_change_admin_status= False
        self.can_change_vlan= False
        self.can_edit_vlans= False  # if true, this driver can edit (create/delete) vlans on the device!
        self.can_set_vlan_name= False  # set to False if vlan create/delete cannot set/change vlan name!
        # self.can_change_poe_status = False - we do not have a test switch with PoE !
        self.can_change_description= False
        self.can_save_config= False  # do we have the ability (or need) to execute a 'save config' or 'write memory' ?
        self.can_reload_all= True  # if true, we can reload all our data (and show a button on screen for this)
        self.can_edit_tags= False  # True if this driver can edit 802.1q tagged vlans on interfaces
        self.can_allow_all= False  # if True, driver can perform equivalent of "vlan trunk allow all", additional to "allow x, y, z"


    #########################################
    # Comware REST API supporting functions #
    #########################################

    def _debug_request(self):
        #
        # print request url response info
        #
        if not REST_DEBUG:
            return
        dprint(
            "---REQUEST ---\n"
            f"URL: {self.response.request.url}\n"
            f"Method: {self.response.request.method}\n"
            f"Headers: {self.response.request.headers}\n"
            f"Body: {self.response.request.body}\n"
            "--- RESPONSE ---\n"
            f"Status Code: {self.response.status_code}\n"
            f"Reason: {self.response.reason}\n"
            f"Headers: {self.response.headers}\n"
            f"Content (text): {self.response.text}\n"
        )

    def _set_headers(self, type="json"):
        #
        # set request headers. We use JSON format as default
        #
        self.headers = {
            "X-Auth-Token": self.token,
            "Content-Type": f"application/{type}",
        }

    def get_path(self, path: str, headers: str = ""):
        #
        # GET a specific REST endpoint and return JSON response.
        # will return response or None if error is trapped (most likely because API endpoint does not exist).
        #
        if not headers:
            # set to default
            headers = self.headers
        # make the request:
        self.response = requests.get(url=self.base_url + path, headers=headers, verify=self.switch.netmiko_profile.verify_hostkey)
        self._debug_request()
        try:
            self.response.raise_for_status()
        except Exception:
            # some error occured (after we had a valid token!), return nothing!
            return None

        if self.response.status_code == 200:    # valid return!
            return json.loads(self.response.text)
        else:
            # likely 204 - Valid return, but No Content
            return None

    def _open_device(self) -> bool:
        """
        Once we have a token, REST API is stateless, so no need to open again...
        return True on success, False on failure, and will set self.error
        """
        dprint("API _open_device()")

        if self.token:
            dprint("  token available!")
            return True

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

        return self.login()

    def _close_device(self) -> bool:
        """
        eAPI is stateless, just clear out token.
        """
        dprint("HPECwRestConnector._close_device()")
        self.token = ""
        self.token_timeout = ""
        return True

    def login(self):
        #
        # login is a POST to the server to get a REST token
        #
        dprint("HPECwRestConnector.login()")
        # set the authentication header:
        auth_plain = f"{self.switch.netmiko_profile.username}:{self.switch.netmiko_profile.password}"
        auth_base64 = base64.b64encode(auth_plain.encode("ascii")).decode("ascii")
        headers = {
            "Authorization": f"Basic {auth_base64}",
            # "Content-Type": "application/json",
        }

        # and try the "get-token" url
        try:
            self.response = self.post(path="Tokens", headers=headers)
        except Exception as err:
            dprint(f"ERROR: cannot login! Info: {err}")
            self.error.status = True
            self.error.description = "Error getting token. Please verify your Credentials Profile!"
            return False

        self.token = self.response['token-id']
        self.token_timeout = self.response['expiry-time']
        dprint(f" Found token: {self.token} (expires {self.token_timeout})")
        self._set_headers()
        return True

    def post(self, path: str, data: dict = {}, headers: str = ""):
        #
        # POST a specific REST endpoint and return JSON response.
        # will raise exception on error
        #
        dprint("HPECwRestConnector.post()")
        if not headers:
            # set to default
            headers = self.headers
        self.response = requests.post(url=self.base_url + path, headers=headers, data=data, verify=self.switch.netmiko_profile.verify_hostkey)
        self._debug_request()
        self.response.raise_for_status()

        return json.loads(self.response.text)


    ##############################
    # OpenL2M specific functions #
    ##############################

    def get_my_basic_info(self) -> bool:
        """
        Get basic info via REST
        """
        dprint("HPECwRestConnector.get_my_basic_info()")
        self.hostname = self.switch.hostname

        if not self._open_device():
            return False  # self.error already set!

        facts = self.get_path(path="Device/Base")
        if facts:
            dprint(f"Device facts = {facts}")
            self.add_more_info("System", "Hostname", facts["HostName"])
            self.add_more_info("System", "Model", facts["HostDescription"])
            # self.add_more_info("System", "Serial", facts["serial_number"])
            # self.add_more_info("System", "OS Version", facts["os"])
            self.add_more_info("System", "Uptime", facts["Uptime"])

        #
        # get vlan info
        #
        # Note: this api call also returns information about the interfaces active on each vlan!
        # we will use this later to find 802.1q tagged info
        #
        vlans = self.get_path(path="VLAN/VLANs")
        if vlans:
            # vlans is a list of dict() for each vlan
            dprint(f"Vlans found:\n{vlans}")
            for vlan in vlans["VLANs"]:
                dprint(f"Found vlan: {vlan['ID']}")
                # create OpenL2M Vlan() object!
                v = Vlan(id=int(vlan['ID']))
                v.name = vlan["Name"]
                v.description = vlan["Description"]
                self.add_vlan(v)

        #
        # get interface information
        #
        # Note: varies values for up/down, type, etc. are defined in the Comware NetConf documentation
        #
        interfaces = self.get_path(path="Ifmgr/Interfaces")
        if interfaces:
            for i in interfaces["Interfaces"]:
                dprint(f"\n-----\nFound interface: {i['Name']}")

                # as all other references in the API use the IfIndex,
                # we use 'IfIndex' as the key to this interface, ie. NOT the name!
                iface = Interface(i['IfIndex'])
                iface.name = i['Name']

                if int(i['AdminStatus']) == 1:
                    iface.admin_status = True
                else:
                    iface.admin_status = False

                if int(i['OperStatus']) == 1:
                    iface.oper_status = True
                else:
                    iface.oper_status = False

                try:
                    iface.speed = int(int(i['ActualSpeed']) / 1000)   # in Bps !
                except Exception:
                    dprint("Note: Invalid speed: {i['ActualSpeed]}")

                if "ConfigDuplex" in i:
                    match int(i["ConfigDuplex"]):
                        case 1: # Full
                            iface.duplex = IF_DUPLEX_FULL
                        case 2: # Half
                            iface.duplex = IF_DUPLEX_HALF
                        case _: # should not happen!
                            iface.duplex = IF_DUPLEX_UNKNOWN

                if "Description" in i:
                    iface.description = i["Description"]

                if "PortLayer" in i and int(i["PortLayer"]) == 2:     # layer 3- routed
                    dprint("  Routed Mode!")
                    iface.is_routed = True
                    if "InetAddressIPV4" in i:
                        # get ipv4 info
                        iface.add_ip4_network(address=i["InetAddressIPV4"], netmask=i["InetAddressIPV4Mask"])

                    # IPv6 not available with this call!
                    #     # 'mask' attribute is really prefix lenght!
                    #     iface.add_ip6_network(address=ip['addr'], prefix_len=ip['mask'])

                if "ifType" in i:
                    iface.type = int(i["ifType"])

                if "LinkType" in i:
                    match int(i["LinkType"]):
                        case 1: # access
                            dprint("  Access Mode!")
                            iface.is_tagged = False
                            iface.untagged_vlan = int(i['PVID'])

                        case 2:
                            dprint("  Trunk Mode!")
                            iface.is_tagged = True
                            iface.untagged_vlan = int(i['PVID'])
                            # # tagged vlans to be parsed from 'permitted_vlans' and 'taggedvlan':
                            # if i['taggedvlan'] is not None:
                            #     parser = RangeParser()
                            #     tagged_vlans = parser.parse(i["taggedvlan"])
                            #     for vlan_id in tagged_vlans:
                            #         iface.add_tagged_vlan(vlan_id=vlan_id)

                        case 3:
                            dprint("  Hybrid Mode!")
                            iface.manageable = False
                            iface.unmanage_reason = "Access denied: interface in Hybrid mode!"

                        case _:
                            dprint(f"UNKNOWN Link-Type: {i['Linktype']}")
                            iface.manageable = False
                            iface.unmanage_reason = f"Access denied: unknown interface mode! (LinkType {i['Linktype']})"


                        #case _:
                        #

                if "ConfigMTU" in i:
                    iface.mtu = int(i["ConfigMTU"])


                #     # parse ipv4 addresses of this interface:
                #     if "interfaceAddress" in if_data:
                #         for addr in i["interfaceAddress"]:
                #             dprint(f"Found IPv4: {addr['primaryIp']}")
                #             iface.add_ip4_network(address=f"{addr['primaryIp']['address']}/{addr['primaryIp']['maskLen']}")

                #     # # parse ipv6 addresses of this interface:
                #     if "interfaceAddressIp6" in if_data:
                #         # "real" IPv6 addresses:
                #         for addr in i["interfaceAddressIp6"]["globalUnicastIp6s"]:
                #             dprint(f"Found IPv6: {addr}")
                #             ipv6 = addr["address"]
                #             prefix_len = 64  # default for IPv6 subnets
                #             # we need to get the netmask from the subnet:
                #             netmask_pos = addr["subnet"].rfind("/")
                #             if netmask_pos > 0:
                #                 # and get the mask len from that:
                #                 prefix_len = int(addr["subnet"][netmask_pos + 1 : :])
                #             iface.add_ip6_network(address=ipv6, prefix_len=prefix_len)
                #         # LinkLocal:
                #         iface.add_ip6_network(address=f"{i['interfaceAddressIp6']['linkLocalIp6']['address']}")

                # done, add this interface to the list...
                self.add_interface(iface)

            #
            # get PoE data
            #

            # PowerSupplies
            PSE = self.get_path(path="PoE/PSEs")
            if PSE:
                for p in PSE["PSEs"]:
                    # create a PoePSE() for OpenL2M use:
                    # "PowerLimit" is in mW, ie divide by 1000 for W
                    ps = self.add_poe_powersupply(id=p["PSEID"], power_available=int(p["PowerLimit"]) / 1000)
                    ps.power_consumed = int(p["CurrentPower"]) / 1000
                    match int(p["OperStatus"]):
                        case 1:
                            ps.status = POE_PSE_STATUS_ON
                        case 2:
                            ps.status = POE_PSE_STATUS_OFF
                        case 3:
                            ps.status = POE_PSE_STATUS_FAULT
                    ps.power_consumed = int(p["AveragePower"]) / 1000
                    # some drivers have this easily available:
                    ps.model = p["Model"]
                    # ps.name = ""
                    # ps.description = ""
                    # ps.part_number = ""
                    # ps.serial = ""

            # PoE Ports
            # Note: this API point on gives ports that are using PoE,
            # NOT ports that are capable of PoE!
            PoEPorts= self.get_path(path="PoE/Ports")
            if PoEPorts:
                for port in PoEPorts["Ports"]:
                    # get the interface from IfIndex:
                    iface = self.get_interface_by_key(key=port['IfIndex'])
                    if iface:
                        admin_status = port["AdminEnable"]
                        poe = PoePort(index=port["IfIndex"], admin_status=admin_status)
                        # set various values found:
                        poe.power_consumption_supported = True
                        poe.power_consumed = int(port["CurrentPower"])  # power consumed in milliWatt
                        poe.power_available = int(port["PowerLimit"]) # power available in milliWatt
                        poe.max_power_consumed = int(port["PeakPower"])  # max power drawn since PoE reset, in milliWatt
                        # "DetectionStatus" matches the SNMP POE mib definitions
                        poe.detect_status = int(port["DetectionStatus"])
                        # and assign to interface:
                        iface.poe_entry = poe

            #
            # get LACP/Port-Channel ports
            #

            # first get the LACP Groups, to find Bridge or Route aggregates
            laggs = self.get_path(path="LAGG/LAGGGroups")
            if laggs:
                # build dict with type and aggregate interface info
                lag_master_info = {}
                for lag in laggs["LAGGGroups"]:
                    lag_iface = self.get_interface_by_key(key=lag["IfIndex"])
                    if lag_iface:
                        lag_iface.type = IF_TYPE_LAGG
                        lag_iface.lacp_type = LACP_IF_TYPE_AGGREGATOR
                        # store aggregation interface:
                        lag_master_info[lag["GroupId"]] = lag_iface

                # now find the members, and map to an aggregate interface
                lacp_members = self.get_path(path="LAGG/LAGGMembers")
                if lacp_members:
                    for member in lacp_members["LAGGMembers"]:
                        dprint(f"Found LAGG Member:\n{member}")
                        # a possible LAGG interface ?
                        if member["GroupId"] in lag_master_info:
                            # get this interface
                            member_iface = self.get_interface_by_key(key=member["IfIndex"])
                            if member_iface:
                                dprint(f"    found Interface() for '{member_iface.name}'")
                                member_iface.lacp_type = LACP_IF_TYPE_MEMBER
                                member_iface.lacp_master_name = lag_master_info[member["GroupId"]].name
                                member_iface.lacp_master_index = int(member["GroupId"])   # needs to be an integer!
                                # add to list of port-channel
                                lag_master_info[member["GroupId"]].lacp_members[member["IfIndex"]] = member_iface.name
                            else:   # should not happen.
                                err_str = f"ERROR: cannot find LACP member interface for index {member['IfIndex']} for LAGG {member['GroupId']}"
                                dprint(err_str)
                                self.add_warning(err_str)

            #
            # get IRF ports
            #
            irf_ports = self.get_path("IRF/IRFPorts")
            if irf_ports:
                for irf in irf_ports["IRFPorts"]:
                    dprint("\n\nIRF port")
                    dprint(pprint.pformat(irf))
                    # are IRF interfaces defined ?
                    if "Interface" in irf:
                        if_info = irf["Interface"][0]
                        dprint("IF_INFO=")
                        dprint(if_info)
                        # get the interface
                        irf_iface = self.get_interface_by_name(name=if_info["IfName"])
                        if irf_iface:
                            # note that we don't care about IRF port type!
                            irf_iface.manageable = False
                            irf_iface.unmanage_reason = "Access denied: interface in IRF (stacking) mode!"

            #
            # get optical transceiver data
            #
            dprint("\n\n--- OPTICS ---\n")
            transceivers = self.get_path(path="Device/Transceivers")
            if transceivers:
                for optics in transceivers["Transceivers"]:
                    dprint(f"Found Optics for ifIndex {optics['IfIndex']}")
                    iface = self.get_interface_by_key(key=optics['IfIndex'])
                    if iface:
                        dprint("   found Interface()")
                        trx = Transceiver()
                        trx.type = optics["TransceiverType"]
                        trx.vendor = optics["VendorName"]
                        trx.serial = optics["SerialNumber"]
                        dprint(f"\nOptics info:\n{i}\n")
                        match int(optics['FiberDiameterType']):
                            case 1:     # 9 micron, ie SM
                                trx.wavelength = int(optics["WaveLength"])   # likely 1310
                            case 2:     # 50 micron, ie MM
                                trx.wavelength = int(optics["WaveLength"])   # likely 850
                            case 3:     # 62.5 micron, ie MM
                                trx.wavelength = int(optics["WaveLength"])   # likely 850
                            case 4:     # copper
                                trx.wavelength = 0

                        # note used:
                        # trx.description: str = ""
                        # trx.connector: str = ""  # 'LC', SC', etc.

                        iface.transceiver = trx

#             #
#             # read VRF info
#             #
#             # for name, vrf_data in data.items():
#             #     dprint(f"Found vrf: {name}")
#             #     if name == "default":  # the non-VRF or default routing table.
#             #         continue
#             #     v = self.get_vrf_by_name(name=name)
#             #     v.set_rd(rd=vrf_data["routeDistinguisher"])
#             #     if vrf_data["protocols"]["ipv4"]["supported"]:
#             #         v.set_ipv4()
#             #     if vrf_data["protocols"]["ipv6"]["supported"]:
#             #         v.set_ipv6()
#             #     # see if this has member interfaces:
#             #     for if_name in vrf_data["interfaces"]:
#             #         dprint(f"  Member interface: {if_name}")
#             #         iface = self.get_interface_by_name(name=if_name)
#             #         if iface:
#             #             dprint("   found Interface()")
#             #             v.interfaces.append(if_name)
#             #             iface.vrf_name = name

        # API may gives responses in alphbetic order, eg 1/1/10 before 1/1/2.
        # sort this to the human natural order we expect:
        self.set_interfaces_natural_sort_order()

        return True

    def get_my_client_data(self) -> bool:
        """
        read mac addressess, and lldp neigbor info.
        return True on success, False on error and set self.error variables
        """
        dprint("HPECwRestConnector.get_my_client_data()")

        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        #
        # get Layer 2 MAC/ETHERNET info
        #
        dprint("\n\n--- MAC tables ---")
        macs = self.get_path(path="MAC/MacUnicastTable")
        if macs:
            dprint(pprint.pformat(macs))
        # for mac in data["unicastTable"]["tableEntries"]:
        #     dprint(f"Ethernet: {mac}")
        #     # add this to the known addressess:
        #     if mac["interface"] == "Router":
        #         # internal ethernet on the device
        #         dprint("  Ignored!")
        #         continue
        #     self.add_learned_ethernet_address(
        #         if_name=mac["interface"], eth_address=mac["macAddress"], vlan_id=int(mac["vlanId"])
        #     )


        #
        # get IPV4 ARP data
        #
        dprint("\n\n--- IPv4 ARP tables ---")
        arps = self.get_path(path="ARP/ArpTable")
        if arps:
            dprint(pprint.pformat(arps))
        # for vrf_name, vrf_arp in data["vrfs"].items():
        #     dprint(f"VRF: {vrf_name}")
        #     for arp in vrf_arp["ipV4Neighbors"]:
        #         dprint(f"  ARP = {arp}")
        #         vlan_id, if_name = get_vlan_and_interface_from_string(arp["interface"])
        #         dprint(f"    Adding to if_name: {if_name}, vlan: {vlan_id}")
        #         self.add_learned_ethernet_address(
        #             if_name=if_name,
        #             eth_address=arp["hwAddress"],
        #             vlan_id=vlan_id,
        #             ip4_address=arp["address"],
        #         )


        #
        # get IPV6 ND (aka Neighbors)
        #
        dprint("\n\n--- IPv6 ND tables ---")
        ipv6nd = self.get_path(path="ND/NDTable")
        if ipv6nd:
            dprint(pprint.pformat(ipv6nd))
        # for vrf_name, vrf_nd in data["vrfs"].items():
        #     dprint(f"VRF: {vrf_name}")
        #     for nd in vrf_nd["ipV6Neighbors"]:
        #         dprint(f"  ND = {nd}")
        #         vlan_id, if_name = get_vlan_and_interface_from_string(nd["interface"])
        #         dprint(f"    Adding to if_name: {if_name}, vlan_id: {vlan_id}")
        #         self.add_learned_ethernet_address(
        #             if_name=if_name,
        #             eth_address=nd["hwAddress"],
        #             vlan_id=vlan_id,
        #             ip6_address=nd["address"],
        #         )

        #
        # LLDP neighbors
        #
        dprint("\n\n--- LLDP - CDP Neighbors ---")
        neighbors = self.get_path(path="LLDp/CDPNeighbors")
        if neighbors:
            dprint(pprint.pformat(neighbors))

        dprint("\n\n--- LLDP - LLDP Neighbors ---")
        neighbors = self.get_path(path="LLDp/LLDPNeighbors")
        if neighbors:
            dprint(pprint.pformat(neighbors))


        # for if_name, nb_data in data.items():
        #     dprint(f"LLDP on {if_name}")
        #     for nb in nb_data["lldpNeighborInfo"]:
        #         dprint(f" Neighbor {nb['systemName']} = {nb}")
        #         # get an OpenL2M NeighborDevice()
        #         neighbor = NeighborDevice(nb["chassisId"])
        #         neighbor.set_sys_name(nb["systemName"])
        #         neighbor.set_sys_description(nb["systemDescription"])
        #         # parse neighbor remote interface info:
        #         if "neighborInterfaceInfo" in nb:
        #             neighbor.port_name = nb["neighborInterfaceInfo"]["interfaceId_v2"]
        #             neighbor.set_port_description(nb["neighborInterfaceInfo"]["interfaceDescription"])

        #         # management addresses given?
        #         mgmt_ipv4 = ""  # used to register ethernet address.
        #         mgmt_ipv6 = ""
        #         if "managementAddresses" in nb:
        #             for addr in nb["managementAddresses"]:
        #                 dprint(f" Mgmt addr: {addr}")
        #                 # Needs parsing...
        #                 match addr["addressType"]:
        #                     case "ipv4":
        #                         dprint(" is IPv4")
        #                         neighbor.management_address_v4 = addr["address"]
        #                         mgmt_ipv4 = addr["address"]
        #                     case "ipv6":
        #                         dprint(" is IPv6")
        #                         neighbor.management_address_v6 = addr["address"]
        #                         mgmt_ipv6 = addr["address"]
        #                     case _:
        #                         # we cannot handle this!
        #                         dprint("Unknown management address type!")

        #         neighbor.set_chassis_string(nb["chassisId"])
        #         if nb["chassisIdType"] == "macAddress":
        #             neighbor.set_chassis_type(LLDP_CHASSIC_TYPE_ETH_ADDR)
        #             # add this ethernet address to our interface data
        #             # NOTE: still need to add the ipv4/v6 management addresses:
        #             self.add_learned_ethernet_address(
        #                 if_name=if_name,
        #                 eth_address=neighbor.chassis_string,
        #                 # vlan_id = vlan_id,
        #                 ip4_address=mgmt_ipv4,
        #                 ip6_address=mgmt_ipv6,
        #             )

        #         # remote device capabilities:
        #         for c, value in nb["systemCapabilities"].items():
        #             match c:
        #                 case "bridge":
        #                     if value:
        #                         neighbor.set_capability(LLDP_CAPABILITIES_BRIDGE)
        #                 case "router":
        #                     if value:
        #                         neighbor.set_capability(LLDP_CAPABILITIES_ROUTER)
        #                 # there are likely other values, we just have not seen those yet!

        #         # add to device interface:
        #         self.add_neighbor_object(if_name, neighbor)

        return True

    #
    # set interface admin status (up/down)
    #
    def set_interface_admin_status(self, interface: Interface, new_state: bool) -> bool:
        """
        Set the interface to the requested state (up or down)

        Args:
            interface = Interface() object for the requested port
            new_state = True / False  (enabled/disabled)

        Returns:
            return True on success, False on error and set self.error variables
        """
        # interface.admin_status = new_state
        dprint(f"HPECwRestConnector.set_interface_admin_status() for {interface.name} to {bool(new_state)}")

        # if new_state:
        #     status = "no shutdown"
        # else:
        #     status = "shutdown"
        # cmds = [
        #     "configure terminal",
        #     f"interface {interface.name}",
        #     f"{status}",
        #     "end",
        # ]

        # if self._run_commands(commands=cmds, action="set interface admin status"):
        #     # all OK, now do the book keeping
        #     super().set_interface_admin_status(interface=interface, new_state=new_state)
        #     return True

        return False

    #
    # set interface description
    #
    def set_interface_description(self, interface: Interface, description: str) -> bool:
        """
        Set the interface description (aka. description) to the string

        Args:
            interface = Interface() object for the requested port
            description = a string with the requested text

        Returns:
            return True on success, False on error and set self.error variables
        """
        # interface.admin_status = new_state
        dprint(f"HPECwRestConnector.set_interface_description() for {interface.name} to '{description}'")

        # if description:
        #     description_cmd = f"description {description}"
        # else:
        #     description_cmd = "no description"

        # cmds = [
        #     "configure terminal",
        #     f"interface {interface.name}",
        #     description_cmd,
        #     "end",
        # ]

        # if self._run_commands(commands=cmds, action="set interface description"):
        #     # all OK, now do the book keeping
        #     super().set_interface_description(interface=interface, description=description)
        #     return True

        return False

    def set_interface_untagged_vlan(self, interface: Interface, new_vlan_id: int) -> bool:
        """
        Override the VLAN change
        return True on success, False on error and set self.error variables
        """
        dprint(
            f"HPECwRestConnector().set_interface_untagged_vlan() port {interface.name} to {new_vlan_id} ({type(new_vlan_id)})"
        )
        # new_vlan = self.get_vlan_by_id(new_vlan_id)
        # if not new_vlan:
        #     self.error.status = True
        #     self.error.description = f"Cannot find Vlan object for vlan {new_vlan_id} for port '{interface.name}'"
        #     self.error.details = ""
        #     return False
        # if interface.is_tagged:
        #     dprint("Tagged/Trunk Mode!")
        #     # set the TRUNK_NATIVE_VLAN OID:
        #     cmds = [
        #         "configure terminal",
        #         f"interface {interface.name}",
        #         f"switchport trunk native vlan {new_vlan_id}",
        #         "end",
        #     ]
        # else:
        #     # regular access mode untagged port:
        #     dprint("Acces Mode!")
        #     cmds = [
        #         "configure terminal",
        #         f"interface {interface.name}",
        #         f"switchport access vlan {new_vlan_id}",
        #         "end",
        #     ]

        # if self._run_commands(commands=cmds, action=f"set interface vlan to {new_vlan_id}"):
        #     # all OK, now do the book keeping
        #     super().set_interface_untagged_vlan(interface=interface, new_vlan_id=new_vlan_id)
        #     return True

        return False

    def set_interface_vlans(self, interface: Interface, untagged_vlan: int, tagged_vlans: List[int], allow_all: bool = False) -> bool:
        """
        Set the interface to the untagged and tagged vlans.

        Args:
            interface = Interface() object for the requested port
            untagged_vlan = an integer with the requested untagged vlan
            tagged_vlans = a List() of integer vlan id's that should be allowed as 802.1q tagged vlans.

        Returns:
            True on success, False on error and set self.error variables
        """
        dprint(
            f"HPECwRestConnector.set_interface_vlans() for {interface.name} to untagged {untagged_vlan}, tagged {tagged_vlans}, allow_all={allow_all}"
        )
        # if not len(tagged_vlans) and not allow_all:
        #     # no tagged vlan, ie "access mode".
        #     cmds = [
        #         "configure terminal",
        #         f"interface {interface.name}",
        #         "switchport mode access",
        #         f"switchport access vlan {untagged_vlan}",
        #         "no switchport trunk native vlan",  # not needed, added for config clarity!
        #         "no switchport trunk allowed vlan",  # not needed, added for config clarity!
        #         "end",
        #     ]
        # else:
        #     # trunk mode, setup mode and native vlan:
        #     cmds = [
        #         "configure terminal",
        #         f"interface {interface.name}",
        #         "switchport mode trunk",
        #         "no switchport access vlan",  # not needed, added for config clarity!
        #         f"switchport trunk native vlan {untagged_vlan}",
        #     ]
        #     # allow all vlans?
        #     if allow_all:
        #         cmds.append("switchport trunk allow vlan all")
        #     # or just some specific vlans:
        #     else:
        #         # start with clean slate on trunk
        #         cmds.append("switchport trunk allowed vlan none")
        #         # loop through all vlans, and see if they are allowed
        #         allow = []
        #         for vid in self.vlans.keys():
        #             if vid in tagged_vlans:
        #                 # allowed!
        #                 allow.append(str(vid))
        #         # add allowed vlans to commands
        #         cmds.append("switch trunk allowed vlan add " + ", ".join(allow))

        #     # and finish the command list:
        #     cmds.append("end")

        # # execute the command:
        # if self._run_commands(
        #     commands=cmds, action=f"set interface vlans to untagged {untagged_vlan}, tagged={tagged_vlans}, allow_all={allow_all}"
        # ):
        #     # call the base Connector() for bookkeeping:
        #     super().set_interface_vlans(interface=interface, untagged_vlan=untagged_vlan, tagged_vlans=tagged_vlans, allow_all=allow_all)
        #     return True

        return False

    def vlan_create(self, vlan_id: int, vlan_name: str) -> bool:
        """
        Create a new vlan on this device. Upon success, this then needs to call the base class for book keeping!

        Args:
            id (int): the vlan id
            name (str): the name of the vlan

        Returns:
            True on success, False on error and set self.error variables.
        """
        dprint(f"HPECwRestConnector.vlan_create() for vlan {vlan_id} = '{vlan_name}'")

        # cmds = [
        #     "configure terminal",
        #     f"vlan {vlan_id}",
        #     f"name {vlan_name}",
        #     "end",
        # ]

        # if self._run_commands(commands=cmds, action=f"create vlan {vlan_id}"):
        #     # all OK, now do the book keeping
        #     super().vlan_create(vlan_id=vlan_id, vlan_name=vlan_name)
        #     return True

        return False

    def vlan_edit(self, vlan_id: int, vlan_name: str) -> bool:
        """
        Edit the vlan name. Upon success, this then needs to call the base class for book keeping!

        Args:
            id (int): the vlan id to edit
            name (str): the new name of the vlan

        Returns:
            True on success, False on error and set self.error variables.
        """
        dprint(f"HPECwRestConnector.vlan_edit() for vlan {vlan_id} = '{vlan_name}'")

        # vlan = self.get_vlan_by_id(vlan_id)
        # if not vlan:
        #     self.error.status = True
        #     self.error.description = f"Vlan {vlan_id} does not exist!"
        #     self.error.details = ""
        #     return False

        # if vlan_name:
        #     cmds = [
        #         "configure terminal",
        #         f"vlan {vlan_id}",
        #         f"name {vlan_name}",
        #         "end",
        #     ]
        # else:
        #     cmds = [
        #         "configure terminal",
        #         f"vlan {vlan_id}",
        #         "no name",
        #         "end",
        #     ]

        # if self._run_commands(commands=cmds, action=f"rename vlan {vlan_id}"):
        #     # all OK, now do the book keeping
        #     super().vlan_edit(vlan_id=vlan_id, vlan_name=vlan_name)
        #     return True

        return False

    def vlan_delete(self, vlan_id: int) -> bool:
        """
        Delete the vlan. Upon success, this then needs to call the base class for book keeping!

        Args:
            id (int): the vlan id to edit

        Returns:
            True on success, False on error and set self.error variables.
        """
        dprint(f"HPECwRestConnector.vlan_delete() for vlan {vlan_id}")

        # vlan = self.get_vlan_by_id(vlan_id)
        # if not vlan:
        #     self.error.status = True
        #     self.error.description = f"Vlan {vlan_id} does not exist!"
        #     self.error.details = ""
        #     return False

        # cmds = [
        #     "configure terminal",
        #     f"no vlan {vlan_id}",
        #     "end",
        # ]

        # if self._run_commands(commands=cmds, action=f"delete vlan {vlan_id}"):
        #     # all OK, now do the book keeping
        #     super().vlan_delete(vlan_id=vlan_id)
        #     return True

        return False

    def save_running_config(self) -> bool:
        """
        save the current config to startup via api.

        Returns:
            (bool) - True if this succeeds, False on failure. self.error() will be set in that case
        """
        dprint("HPECwRestConnector().save_running_config()")

        # cmds = [
        #     "write memory",
        # ]

        # return self._run_commands(commands=cmds, action="save configuration")

        return False

    #
    # here we override the SSH command execution using Netmiko,
    # and implement it using the eAPI.
    #
    # def _execute_command(self, command: str) -> bool:
    #     """
    #     Execute a single command on the device using eAPI.
    #     Save the command output to self.output
    #     On error, set self.error as needed.

    #     Args:
    #         command: the string the execute as a command on the device

    #     Returns:
    #         True if success, False on failure.
    #         On success, save the command output to self.output.
    #         On failure, set self.error as applicable.
    #     """
    #     dprint(f"HPECwRestConnector()._execute_command() '{command}'")

    #     if not self._open_device():
    #         dprint("_open_device() failed!")
    #         return False

    #     # try:
    #     #     # run the command:
    #     #     json_data = self._eapi_run_command(command=command, format="text")
    #     #     # The 'result' key will contain a list of command output.
    #     #     # dprint(f"RETURN:\n{json_data}")
    #     #     self.netmiko_output = json_data.get("result")[0]["output"]
    #     #     return True
    #     # except Exception as err:
    #     #     dprint(f"  ERROR running '{command}': {err}")
    #     #     self.error.status = True
    #     #     self.error.description = f"Error running eAPI command = '{command}'!"
    #     #     self.error.details = f"Cannot read device information: {format(err)}"
    #     #     self.add_warning(
    #     #         warning=f"Cannot read device information: {repr(err)} ({str(type(err))}) => {traceback.format_exc()}"
    #     #     )

    #     return False

    def _run_commands(self, commands: list, action: str) -> bool:
        """Run multiple commands using the eAPI.

        Args:
            commands: list of command string to run
            action: description of what this tries to accomplish. Will be used if this fails.

        Returns:
            True if all goes OK.
            False if this fails. the self.error() variable will be set with information about the failure.
        """
        dprint(f"HPECwRestConnector()._run_command:\n{commands}")

        # try:
        #     # run the command:
        #     json_data = self._eapi_run_command(command=commands)
        #     # The 'result' key will contain a list of command output.
        #     dprint(f"RETURN:\n{json_data}")
        #     if "error" in json_data:
        #         # some error occured !
        #         dprint("  ERROR running command!")
        #         # error_code = json_data['error']['code']
        #         # error_msg = json_data['error']['message']
        #         self.error.status = True
        #         self.error.description = (
        #             f"Error '{json_data['error']['code']}' running eAPI commands: '{json_data['error']['message']}'"
        #         )
        #         self.error.details = f"Cannot {action}. Full return data: {json_data}"
        #         return False

        # except Exception as err:
        #     dprint(f"  ERROR running '{commands}': {err}")
        #     self.error.status = True
        #     self.error.description = f"Error running eAPI commands = '{commands}'!"
        #     self.error.details = f"Cannot {action}: {format(err)}"
        #     return False
        # # all OK
        # dprint("All OK!")
        # return True

        return False

