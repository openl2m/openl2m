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
ArubaOS Switch REST API Connector

This implements a REST api driver from Aruba AOS-S switches.
This follows the API docs outlined in the Aruba Networking AOS-S v16.11 REST API docs at
https://arubanetworking.hpe.com/techdocs/AOS-Switch/16.11/Aruba%20REST%20API%20for%20AOS-S%2016.11.pdf
"""

import base64
import json

from django.http.request import HttpRequest

# used to disable unknown SSL cert warnings:
import urllib3

from switches.connect.classes import Interface, Vlan, Transceiver, NeighborDevice

# from switches.connect.classes import PoePort, StackMember
from switches.connect.restconnector import RESTConnector
from switches.connect.constants import (
    # VLAN_ADMIN_DISABLED,
    # POE_PORT_ADMIN_DISABLED,
    # POE_PORT_ADMIN_ENABLED,
    # IF_DUPLEX_UNKNOWN,
    # IF_DUPLEX_HALF,
    # IF_DUPLEX_FULL,
    # IF_TYPE_OTHER,
    # IF_TYPE_LOOPBACK,
    IF_TYPE_VIRTUAL,
    IF_TYPE_ETHERNET,
    IF_TYPE_LAGG,
    LACP_IF_TYPE_MEMBER,
    LACP_IF_TYPE_AGGREGATOR,
    # POE_PSE_STATUS_ON,
    # POE_PSE_STATUS_OFF,
    # POE_PSE_STATUS_FAULT,
    LLDP_CHASSIC_TYPE_ETH_ADDR,
    LLDP_CAPABILITIES_OTHER,
    LLDP_CAPABILITIES_REPEATER,
    LLDP_CAPABILITIES_BRIDGE,
    LLDP_CAPABILITIES_WLAN,
    LLDP_CAPABILITIES_ROUTER,
    LLDP_CAPABILITIES_PHONE,
    LLDP_CAPABILITIES_DOCSIS,
    LLDP_CAPABILITIES_STATION,
    # IANA_TYPE_OTHER,
    # IANA_TYPE_IPV4,
    # IANA_TYPE_IPV6,
    VLAN_STATUS_PERMANENT,
)
from switches.models import Switch, SwitchGroup

# from switches.utils import time_duration, dprint
from switches.utils import dprint

# various commands use version 4, 5 or 6...
API_VERSION = 4


class ArubaAOSsRestConnector(RESTConnector):
    """
    This implements an Aruba AOS-S REST API connector object.
    """

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        # call the super class
        dprint("Aruba_AOSS_RestConnector __init__")
        super().__init__(request, group, switch)
        self.description = "Aruba AOS-S REST API driver"
        self.vendor_name = "HPE/Aruba"
        # we can override the settings calculated from switch.read_only, group.ready_only and user.profile.read_only
        # but we should only do this to create a Read-Only driver!
        # self.read_only = True

        if switch.description:
            self.add_more_info("System", "Description", switch.description)

        self._set_base_url(base_url=f"https://{self.switch.primary_ip4}/rest/v{API_VERSION}/")

        # self.port_index_to_if_index: Dict[
        #     int, str
        # ] = {}  # this maps switchport "PortIndex" as key (int) to MIB-II IfIndex (str)

        # we are NOT logging in here!
        # if not self._open_device():
        #     raise Exception(self.error.description)

        # capabilities supported by this eAPI driver:
        self.can_change_admin_status = True
        self.can_change_vlan = True
        self.can_change_poe_status = False
        self.can_change_description = True
        self.can_save_config = True  # do we have the ability (or need) to execute a 'save config' or 'write memory' ?
        self.can_reload_all = True  # if true, we can reload all our data (and show a button on screen for this)
        self.can_edit_vlans = True  # if true, this driver can edit (create/delete) vlans on the device!
        self.can_set_vlan_name = True  # set to False if vlan create/delete cannot set/change vlan name!
        self.can_edit_tags = False  # True if this driver can edit 802.1q tagged vlans on interfaces
        self.can_allow_all = (
            True  # if True, driver can perform equivalent of "vlan trunk allow all", additional to "allow x, y, z"
        )

    def __del__(self):
        """when we close the object, release the REST ticket, so the switch does not run out of resources!"""
        self._close_device()

    #########################################
    # AOS-S REST API supporting functions #
    #########################################

    def _open_device(self) -> bool:
        """
        Once we have a token, REST API is stateless, so no need to open again...
        return True on success, False on failure, and will set self.error
        """
        dprint("ArubaAOSsRestConnector._open_device()")

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
            urllib3.disable_warnings()

        return self.login()

    def _close_device(self) -> bool:
        """
        eAPI is stateless, just clear out token.
        """
        dprint("Aruba_AOSS_RestConnector._close_device()")

        # need to call DELETE to the session-login URI
        if self.cookies:
            # do we want to check SSL certificates?
            if not self.switch.netmiko_profile.verify_hostkey:
                dprint("  Cert warnings disabled in urllib3!")
                # disable unknown cert warnings
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                # or all warnings:
                urllib3.disable_warnings()

            self._delete(path="login-sessions", message="API LOGOUT")

            # and clear internal cookie jar:
            self.cookies = {}

        return True

    def login(self):
        #
        # login is a POST to the server to get a REST token
        #
        dprint("Aruba_AOSS_RestConnector.login()")

        # POST data is username and password
        # Note: request will do URLEncoding on dict, but NOT encode a string
        # we need to post password WITHOUT url-encoding, but send the attributes as a dict!
        data = f'{{"userName": "{self.switch.netmiko_profile.username}", "password": "{self.switch.netmiko_profile.password}"}}'

        # and try the "login-sessions" url
        try:
            dprint(f" Login data: {data}")
            self._post(path="login-sessions", data=data, message="API LOGIN")
            data = json.loads(self.response.text)
            if "cookie" in data:
                dprint(f"  Found sessionId: {data['cookie']}")
                session = data["cookie"].split("=")
                cookies = {session[0]: session[1]}
                dprint(f"  Setting cookies: {cookies}")
                self._set_cookies(cookies=cookies)
                return True
            # Hmm? No token?
            dprint("ERROR: No login sessionId found!")
            self.error.description = "Error getting login sessionId!"
            self.error.details = "We're not sure what happened!"
            return False
        except Exception as err:
            dprint(f"ERROR: cannot login! - {err}")
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot open REST session: {format(err)}"
            return False

    ##############################
    # OpenL2M specific functions #
    ##############################

    #
    # From the Aruba AOS-S REST API docs:
    #
    # GET is used to read various configurations and operational data from the device.
    # Data is returned in the body of the response.
    #
    # POST can only be used to create new objects or attributes, ie when they are NOT SET YET!
    # Data is sent in the body of the request.
    #
    # PUT will update with value, but NOT clear out! (ie you cannot set description="").
    # Data is send in the body of the request.
    # Success will return code 204 - No content.
    # You can repeatedly PUT with the same value!
    #
    # DELETE needs to be used to remove an object. It does NOT take request body data.
    #

    # Aruba AOS-S API ENDPOINTS are described in the file "device-api-xx-16.xx" from Aruba site
    # extract and look at these files for your specific device. Eg. for a 2930M, the "WC" train:
    # WC-device-api-v7.0/device-rest-api/services/common/server.html
    # WC-device-api-v7.0/device-rest-api/services/wired/server.html

    def get_my_basic_info(self) -> bool:
        """
        Get basic info via REST
        """
        dprint("Aruba_AOSS_RestConnector.get_my_basic_info()")
        self.hostname = self.switch.hostname

        if not self._open_device():
            return False  # self.error already set!

        # Returns the host system attributes.
        sys_info = self._get(path="system")
        if sys_info:
            self.add_more_info("System", "Hostname", sys_info["name"])
            # # add to database driver info:
            self.switch.hostname = sys_info["name"]
            self.set_driver_info(name="hostname", value=sys_info["name"])
            # self.set_driver_info(name="snmp_oid", value=sys_info["HostOid"])

        # Returns the status of the host system for standalone switches.
        system_status = self._get(path="system/status")
        # system: {'base_ethernet_address': {'octets': '94f128-038d40', 'version': 'MAV_EUI_48'},
        #  'firmware_version': 'WC.16.10.0001',
        #  'hardware_revision': 'JL319A',
        #  'name': 'TESTLAB-Aruba-2930M',
        #  'product_model': 'Aruba2930M-24G Switch(JL319A)',
        #  'serial_number': 'SG76JQK23C',
        #  'sys_fan_status': False,
        #  'sys_temp': 19,
        #  'sys_temp_threshold': 45,
        #  'total_memory_in_bytes': 339526144,
        #  'uri': '/system/status'}
        if system_status:
            self.add_more_info("System", "Model", system_status["product_model"])
            self.add_more_info("System", "Serial", system_status["serial_number"])
            self.add_more_info("System", "OS Version", system_status["firmware_version"])
            # add to driver info:
            self.set_driver_info(name="model", value=system_status["product_model"])
            self.set_driver_info(name="os_version", value=system_status["firmware_version"])
            self.set_driver_info(name="serial_number", value=system_status["serial_number"])

        # Returns the global system information for stacked switches.
        # system_global= self._get(path="system/status/global_info")
        # if system_global:
        #     dprint("system/status/global_info to be parsed...")

        # Returns the list of member specific system information for stacked switches.
        # system_members= self._get(path="system/status/members")
        # if system_members:
        #     dprint("system/status/members to be parsed...")

        # Returns the host system time configuration. Not useful...
        # system_time= self._get(path="system/time")

        #
        # get vlan info
        #
        vlans = self._get(path="vlans")
        if vlans:
            # # vlans is a list of dict() for each vlan
            for vlan in vlans["vlan_element"]:
                # create OpenL2M Vlan() object!
                v = Vlan(id=int(vlan['vlan_id']))
                v.name = vlan["name"]
                if vlan['type'] == 'VT_STATIC':
                    v.status = VLAN_STATUS_PERMANENT
                self.add_vlan(v)
                # get the details - adds nothing new to the vlan info
                # vlan_info = self._get(path=f"vlans/{vlan['vlan_id']}")
                # if vlan_info:
                #     dprint(f"\nVLAN_INFO: {pprint.pformat(vlan_info)}")

        #
        # get interface information
        #
        # Note: varies values for up/down, type, etc. are defined in the AOS-S REST documentation
        #
        ports = self._get(path="ports")
        if ports:
            for i in ports["port_element"]:
                # as all other references in the API use the 'id',
                # we use 'id' as the key to this interface, ie. NOT the name!
                iface = Interface(i['id'])
                iface.name = str(i['id'])
                iface.description = i['name']
                # iface.uri = i['uri']

                if i["is_port_enabled"]:
                    iface.admin_status = True
                if i["is_port_up"]:
                    iface.oper_status = True
                # this only shows ethernet interfaces
                iface.type = IF_TYPE_ETHERNET

                # Note that "trunk-group" attribute sets the trunk membership of an interface.
                # We call "trunk/ports" for this avoid complexities with the fact that TrkXX interfaces
                # can also show in this call to "ports", and hence we could create duplicate interfaces!

                # done, add this interface to the list...
                self.add_interface(iface)

        #
        # get LACP/Port-Channel ports or active "Trk" trunk interfaces
        #
        trunks = self._get(path="trunk/port")
        if trunks:
            for trunk in trunks["trunk_element"]:
                trunk_port_name = trunk["trunk_group"]
                dprint(f"FOUND TRUNK {trunk_port_name}")
                iface = self.get_interface_by_key(key=trunk_port_name)
                if not iface:
                    dprint(f"CREATING TRUNK interface {trunk_port_name}")
                    # create the trunk interface
                    iface = Interface(trunk_port_name)
                    iface.name = trunk_port_name
                    # if this existed, we will have real state.
                    # if not existed yet, we don't know real state, so set to UP/UP
                    iface.admin_status = True
                    iface.oper_status = True
                    self.add_interface(iface)
                # set attributes for an LACP/Trunk interface
                iface.description = f"LACP Trunk {trunk_port_name}"
                iface.can_edit_description = False
                iface.manageable = False
                iface.type = IF_TYPE_LAGG
                iface.lacp_type = LACP_IF_TYPE_AGGREGATOR
                iface.lacp_admin_key = 1  # needs to be > 0
                # add member:
                iface.lacp_members[trunk["port_id"]] = trunk["port_id"]
                # find member interface:
                member_iface = self.get_interface_by_key(key=trunk["port_id"])
                if member_iface:
                    dprint(f"    found Interface() for '{member_iface.name}'")
                    member_iface.lacp_type = LACP_IF_TYPE_MEMBER
                    member_iface.lacp_master_name = trunk_port_name
                    member_iface.lacp_master_index = 1  # needs to be an integer!
                else:  # should not happen.
                    err_str = f"ERROR: cannot find {trunk_port_name} member interface for {trunk['port_id']}"
                    dprint(err_str)
                    self.add_warning(err_str)

        #
        # smart-rate ports ?
        #
        # ports = self._get(path="smartrate/ports")
        # if ports:
        #     dprint("smartrate/ports to be parsed...")

        #
        # port statistics
        #
        port_stats = self._get(path="port-statistics")
        if port_stats:
            dprint("port-statistics to be parsed...")
            for pstat in port_stats["port_statistics_element"]:
                iface = self.get_interface_by_key(key=pstat["id"])
                if iface:
                    iface.speed = pstat["port_speed_mbps"]
                    # to be figured out:
                    #                 iface.duplex = IF_DUPLEX_FULL
                    #                 iface.duplex = IF_DUPLEX_HALF
                    #                 iface.duplex = IF_DUPLEX_UNKNOWN
                    #         iface.mtu = int(i["ConfigMTU"])

                else:  # should not happen:
                    dprint(f"WARNING: Interface() not found for id={pstat['id']}")

        # #
        # # get PoE data
        # #

        #
        # PoE PowerSupplies
        #
        # Note that usage is also reported in the individual power supplies, so no need for this call!
        # consumption = self._get(path="system/status/power/consumption")
        # {'power_consumption_element': [{'current_power_in_watts': '20',
        #                         'psu_model_description': '2930M-24G Switch'}],
        #                          'uri': '/system/status/power/consumption'}

        supplies = self._get(path="system/status/power/supply")
        if supplies:
            dprint("Power Supply data found!")
            for supply in supplies["system_power_supply"]:
                if supply["power_supply_state"] == "SPSS_NOT_PRESENT":  # empty slot!
                    continue
                pse = self.add_poe_powersupply(
                    id=supply["power_supply_number"],
                    power_available=int(supply["max_power_in_watts"]),
                )
                pse.set_consumed_power(supply["power_in_use_in_watts"])
                pse.mode = supply["model_info"]
                pse.description = supply["voltage_description"]
                if supply["power_supply_state"] == "SPSS_POWERED":
                    pse.set_enabled()
                else:
                    pse.set_disabled()

        #
        # PoE Ports - no device to test against
        #
        # poe_ports = self._get(path="poe/ports")
        # if poe_ports:
        #     dprint("poe/ports to be parsed (no test hardware!)")
        #
        # this returns "PortPoe" element, which has the following attributes:
        #     "uri":
        #     "port_id":
        #     "is_poe_enabled":
        #         "description": "Port PoE status",
        #         "type": "boolean",
        #     "poe_priority":
        #         "description": "Port PoE priority",
        #         "default_value": "PPP_LOW"
        #     "poe_allocation_method":
        #         "description": "PoE allocation method",
        #         "default_value": "PPAM_USAGE"
        #     "allocated_power_in_watts":
        #         "description": "Allocated power value. Default value for this param is platform dependent.",
        #         "type": "integer"
        #     "port_configured_type":
        #         "description": "Port configured type",
        #         "type": "string",
        #         "maxLength": 256,
        #         "minLength": 0
        #     "pre_standard_detect_enabled":
        #         "description": "pre_std_detect enabled/disable",
        #         "type": "boolean"

        #
        # get interface IPv4 and IPv6 addresses
        #
        addresses = self._get(path="ipaddresses")
        if addresses:
            for a in addresses["ip_address_subnet_element"]:
                if a["ip_address_mode"] == "IAAM_STATIC":
                    dprint(f"VLAN {a['vlan_id']}: {a['ip_address']['octets']} / {a['ip_mask']['octets']}")
                    # these devices do NOT give a virtual interface for vlans that are routed, so create one
                    iface = Interface(key=f"vlan_{a['vlan_id']}")
                    iface.name = f"Vlan{a['vlan_id']}"
                    iface.type = IF_TYPE_VIRTUAL
                    iface.admin_status = True
                    iface.oper_status = True
                    iface.description = "Vlan routed virtual interface"
                    iface.can_edit_description = False
                    iface.is_routed = True
                    iface.manageable = False
                    iface.unmanage_reason = "Virtual Interface cannot be edited!"
                    iface.add_ip4_network(address=a['ip_address']['octets'], netmask=a['ip_mask']['octets'])

                    # done, add this interface to the list...
                    self.add_interface(iface)

        #
        # get optical transceiver data
        #
        transceivers = self._get(path="transceivers")
        if transceivers:
            for optics in transceivers["transceiver_element"]:
                iface = self.get_interface_by_key(key=optics['port_id'])
                if iface:
                    trx = Transceiver()
                    trx.type = optics["type"]
                    # trx.vendor = optics["not given"]
                    trx.serial = optics["serial_number"]
                    trx.description = optics["product_number"]
                    iface.transceiver = trx

        #
        # Vlan port info, ie tagged/untagged and PVID/untagged vlan
        #
        vlan_ports = self._get(path="vlans-ports")
        if vlan_ports:
            for port in vlan_ports["vlan_port_element"]:
                iface = self.get_interface_by_key(key=port['port_id'])
                if iface:
                    match port["port_mode"]:
                        case "POM_UNTAGGED":
                            # this sets the PVID, but does NOT mean this is an untagged port! Leave self.is_tagged alone!
                            iface.untagged_vlan = port["vlan_id"]
                        case "POM_TAGGED_STATIC":
                            iface.is_tagged = True
                            # add this vlan as tagged!
                            iface.add_tagged_vlan(vlan_id=port["vlan_id"])
                        case _:
                            self.add_warning(f"WARNING: unknown mode for port {port['port_id']}  = {port['port_mode']}")

        # API returns may gives responses in alphbetic order, eg 1/1/10 before 1/1/2.
        # sort this to the human natural order we expect:
        self.set_interfaces_natural_sort_order()

        # save driver info
        self.save_driver_info()

        # to prevent the device from running out of REST ticket resources, close REST session
        self._close_device()

        return True

    def get_my_client_data(self) -> bool:
        """
        read mac addressess, and lldp neigbor info.
        return True on success, False on error and set self.error variables
        """
        dprint("Aruba_AOSS_RestConnector.get_my_client_data()")

        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        #
        # get Layer 2 MAC/ETHERNET info
        #
        macs = self._get(path="mac-table")
        if macs:
            # {'collection_result': {'filtered_elements_count': 11,
            #                        'total_elements_count': 11},
            #  'mac_table_entry_element': [{'mac_address': '943fc2-e37448',
            #                               'port_id': '24',
            #                               'uri': '/mac-table/943fc2-e37448',
            #                               'vlan_id': 41},
            #                              {'mac_address': '00005e-000165',
            #                               'port_id': '24',
            #                               'uri': '/mac-table/00005e-000165',
            #                               'vlan_id': 500},
            for mac in macs["mac_table_entry_element"]:
                iface = self.get_interface_by_key(key=mac["port_id"])
                if iface:
                    iface.add_learned_ethernet_address(eth_address=mac["mac_address"], vlan_id=mac["vlan_id"])
                    self.eth_addr_count += 1

        #
        # get IPV4 ARP data - NOT implemented
        #

        #
        # get IPV6 ND (aka Neighbors) - NOT implemented
        #

        #
        # LLDP neighbors
        #

        # lldp_status = self._get(path="lldp")
        # if lldp_status:
        #     dprint("lldp to be parsed...")

        # lldp status of local ports, ie transmitting lldp or not, etc.
        # lldp_ports = self._get(path="lldp/local-port")
        # if lldp_ports:
        #     dprint("lldp/local-port to be parsed...")

        # this gives some more details about the local device
        # lldp_local_info = self._get(path="lldp/local_device/info")
        # if lldp_local_info:
        #     dprint("lldp/local_device/info to be parsed...")

        lldp_remote_ports = self._get(path="lldp/remote-device")
        if lldp_remote_ports:
            count = 0
            for nb in lldp_remote_ports["lldp_remote_device_element"]:
                iface = self.get_interface_by_key(key=nb["local_port"])
                if iface:
                    count += 1
                    neighbor = NeighborDevice(lldp_index=count)

                    if nb["chassis_type"] == "RCT_MAC_ADDRESS":
                        # chassis mac address, sent with spaces (go figure!)
                        chassis_addr = nb["chassis_id"].replace(" ", "-")
                        neighbor.set_chassis_string(chassis_addr)
                        neighbor.set_chassis_type(LLDP_CHASSIC_TYPE_ETH_ADDR)
                    else:
                        # not sure what this is...
                        neighbor.set_chassis_string(nb["chassis_id"])

                    neighbor.set_sys_name(nb["system_name"])
                    neighbor.port_name = nb["port_id"]
                    neighbor.port_descr = nb["port_description"]
                    neighbor.set_sys_description(nb["system_description"])
                    # parse capabilities
                    for capability, enabled in nb["capabilities_enabled"].items():
                        if enabled:
                            match capability:
                                case "bridge":
                                    neighbor.set_capability(LLDP_CAPABILITIES_BRIDGE)
                                case "router":
                                    neighbor.set_capability(LLDP_CAPABILITIES_ROUTER)
                                case "station_only":
                                    neighbor.set_capability(LLDP_CAPABILITIES_STATION)
                                case "telephone":
                                    neighbor.set_capability(LLDP_CAPABILITIES_PHONE)
                                case "wlan_access_point":
                                    neighbor.set_capability(LLDP_CAPABILITIES_WLAN)
                                case "cable_device":
                                    neighbor.set_capability(LLDP_CAPABILITIES_DOCSIS)
                                case "repeater":
                                    neighbor.set_capability(LLDP_CAPABILITIES_REPEATER)
                                case _:
                                    neighbor.set_capability(LLDP_CAPABILITIES_OTHER)
                                    self.add_warning(
                                        f"WARNING: Unknown neighbor capability on {iface.name} from {nb['system_name']}: {capability}"
                                    )

                    # parse remote management address:
                    for remote_addr in nb["remote_management_address"]:
                        match remote_addr["type"]:
                            case "AFM_IP4":
                                neighbor.management_address_v4 = remote_addr["address"]
                            case "AFM_IP6":
                                neighbor.management_address_v6 = remote_addr["address"]
                            case _:
                                self.add_warning(
                                    f"WARNING: Unknown neighbor mgmt address on {iface.name} from {nb['system_name']}: {remote_addr}"
                                )

                    # add neighbor to interface:
                    iface.add_neighbor(neighbor=neighbor)
                    self.neighbor_count += 1

        # to prevent the device from running out of REST ticket resources, close REST session
        self._close_device()

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
        dprint(f"Aruba_AOSS_RestConnector.set_interface_admin_status() for {interface.name} to {bool(new_state)}")

        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        # body data
        data = {
            "id": interface.key,
            "is_port_enabled": new_state,
        }

        try:
            resp = self._put(path=f"ports/{interface.key}", data=json.dumps(data))
            self._close_device()
            if resp:
                # all OK, now do the book keeping
                super().set_interface_admin_status(interface=interface, new_state=new_state)
                return True
            # error ?
            self.error.status = True
            self.error.description = "Error changing interface state!"
            self.error.details = "We're not sure what happened (?)"
            return False
        except Exception as err:
            self._close_device()
            self.error.status = True
            self.error.description = "Error changing interface state!"
            self.error.details = format(err)
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
        dprint(f"Aruba_AOSS_RestConnector.set_interface_description() for {interface.name} to '{description}'")

        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        # body data
        data = {
            "id": interface.key,
            "name": description,
        }

        try:
            resp = self._put(path=f"ports/{interface.key}", data=json.dumps(data))
            self._close_device()
            if resp:
                # all OK, now do the book keeping
                super().set_interface_description(interface=interface, description=description)
                return True
            # error ?
            self.error.status = True
            self.error.description = "Error setting description!"
            self.error.details = "We're not sure what happened (?)"
            return False
        except Exception as err:
            self._close_device()
            self.error.status = True
            self.error.description = "Error setting description!"
            self.error.details = format(err)
            return False

    # def set_interface_poe_status(self, interface: Interface, new_state: int) -> bool:
    #     """
    #     set the interface Power-over-Ethernet status as given
    #     interface = Interface() object for the requested port

    #     Args:
    #         interface: the Interface to modify
    #         new_state = POE_PORT_ADMIN_ENABLED or POE_PORT_ADMIN_DISABLED

    #     Returns:
    #         True on success, False on error and set self.error variables
    #     """
    #     dprint(f"Aruba_AOSS_RestConnector.set_interface_poe_status() for {interface.name} to {new_state}")

    #     if not interface.poe_entry:
    #         # this should never happen!
    #         dprint("PoE change requested, but interface does not support PoE!!!")
    #         self.error.status = True
    #         self.error.description = "PoE change requested, but interface does not support PoE!!!"
    #         self.error.details = ""
    #         return False

    #     if interface.poe_entry.pse_id < 0:
    #         # this should never happen!
    #         dprint("PoE change requested, but invalid Power Suply ID found!")
    #         self.error.status = True
    #         self.error.description = "PoE change requested, but invalid Power Suply ID found!"
    #         self.error.details = ""
    #         return False

    #     if not self._open_device():
    #         dprint("_open_device() failed!")
    #         return False

    #     if new_state == POE_PORT_ADMIN_ENABLED:
    #         state = True     # True=PoE enabled, False=disabled
    #     else:
    #         state = False

    #     # body data
    #     data = {
    #         "id": interface.key,
    #         "is_power_enabled": state,
    #     }

    #     # go set PoE state
    #     try:
    #         resp = self._put(path=f"/ports/poe/{interface.key}", data=json.dumps(data))
    #         self._close_device()
    #         if resp:
    #             # all OK, now do the book keeping
    #             super().set_interface_poe_status(interface, new_state)
    #             return True
    #         # error ?
    #         self.error.status = True
    #         self.error.description = f"Error setting PoE state to {status_name}!"
    #         self.error.details = "We're not sure what happened (?)"
    #         return False
    #     except Exception as err:
    #         self._close_device()
    #         self.error.status = True
    #         self.error.description = f"Error setting PoE to {status_name}!"
    #         self.error.details = format(err)
    #         return False

    def set_interface_untagged_vlan(self, interface: Interface, new_vlan_id: int) -> bool:
        """
        Override the VLAN change
        return True on success, False on error and set self.error variables
        """
        dprint(
            f"Aruba_AOSS_RestConnector().set_interface_untagged_vlan() port {interface.name} to {new_vlan_id} ({type(new_vlan_id)})"
        )

        # validate new vlan
        new_vlan = self.get_vlan_by_id(new_vlan_id)
        if not new_vlan:
            self.error.status = True
            self.error.description = f"Cannot find Vlan object for vlan {new_vlan_id} for port '{interface.name}'"
            self.error.details = ""
            return False

        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        # for tagged interface where the new pvid/untagged is part of the tagged vlans:
        # first remove the tagged (new pvid) vlan!
        if interface.is_tagged and new_vlan_id in interface.vlans:
            dprint(f"REMOVING vlan {new_vlan_id} as TAGGED VLAN")
            try:
                resp = self._delete(path=f"vlans-ports/{new_vlan_id}-{interface.key}")
            except Exception as err:
                self._close_device()
                self.error.status = True
                self.error.description = f"Error removing vlan {new_vlan_id} as tagged vlan!"
                self.error.details = format(err)
                return False

        # Now set the untagged vlan
        data = {
            "port_id": interface.key,  # note: this uses port_id, instead of id. Likely as this can only be real switch ports!
            "vlan_id": new_vlan_id,
            "port_mode": "POM_UNTAGGED",
        }
        try:
            resp = self._post(path="vlans-ports", data=json.dumps(data))
            self._close_device()
            if resp:
                # all OK, now do the book keeping
                super().set_interface_untagged_vlan(interface=interface, new_vlan_id=new_vlan_id)
                return True
            # error ?
            self.error.status = True
            self.error.description = f"Error setting vlan {new_vlan_id}!"
            self.error.details = "We're not sure what happened (?)"
            return False
        except Exception as err:
            self._close_device()
            self.error.status = True
            self.error.description = f"Error setting vlan to {new_vlan_id}!"
            self.error.details = format(err)
            return False

    # def set_interface_vlans(self, interface: Interface, untagged_vlan: int, tagged_vlans: list[int], allow_all: bool = False) -> bool:
    #     """
    #     Set the interface to the untagged and tagged vlans.

    #     Args:
    #         interface = Interface() object for the requested port
    #         untagged_vlan = an integer with the requested untagged vlan
    #         tagged_vlans = a list() of integer vlan id's that should be allowed as 802.1q tagged vlans.

    #     Returns:
    #         True on success, False on error and set self.error variables
    #     """
    #     dprint(
    #         f"Aruba_AOSS_RestConnector.set_interface_vlans() for {interface.name} to untagged {untagged_vlan}, tagged {tagged_vlans}, allow_all={allow_all}"
    #     )

    #     if not self._open_device():
    #         dprint("_open_device() failed!")
    #         return False

    #     if not tagged_vlans and not allow_all:
    #         # no tagged vlan, ie "access mode".
    #         dprint("ACCESS mode set vlan")
    #         # POST data to change the PVID / untagge vlan.
    #         data = {
    #             "id": interface.key,
    #             "port_mode": "POM_UNTAGGED",
    #             "vlan_id": untagged_vlan,
    #         }
    #         try:
    #             resp = self._post(path="vlans-ports", data=json.dumps(data))
    #             if resp:
    #                 # all OK, now do the book keeping
    #                 super().set_interface_untagged_vlan(interface=interface, new_vlan_id=untagged_vlan)
    #         except Exception as err:
    #             self._close_device()
    #             dprint("ERROR setting untagged vlan: {err}")
    #             self.error.status = True
    #             self.error.description = "Error setting untagged vlan (pvid)! Interface is now in UNKNOWN state!"
    #             self.error.details = format(err)
    #             return False

    #         if interface.is_tagged:
    #             # change mode as well
    #             dprint("  Changing to ACCESS")
    #             data['LinkType'] = 1    # 1 = Access
    #         else:
    #             dprint("Already Access mode!")
    #     else:
    #         # trunk mode, setup mode and native vlan:
    #         dprint("TAGGED mode set vlans")
    #         mode = "tagged"
    #         if not interface.is_tagged:
    #             # change mode as well
    #             dprint("  Changing to TRUNK")
    #             data['LinkType'] = 2    # 2 = Trunk
    #         else:
    #             dprint("Already Trunk mode!")

    #     # and make the API call for the Access/Trunk setting:
    #     try:
    #         dprint(f"Setting Mode to {mode}")
    #         resp = self._put(path="vlans-ports", data=json.dumps(data))
    #         if resp:
    #             dprint("  mode set OK!")
    #             # mode set OK. If tagged, add this interface to desired vlans:
    #             if allow_all or len(tagged_vlans):
    #                 dprint("Adding VLANs to TRUNK.")
    #                 trunk_vlan_list = []
    #                 for vlan_id in self.vlans:
    #                     dprint(f"Checking vlan_id {vlan_id} = {type(vlan_id)}")
    #                     if allow_all or vlan_id in tagged_vlans:
    #                         dprint(f"CW REST TRUNK SET: TRUNK ADDING Vlan {vlan_id}")
    #                         # for api call, we need a comma-separated list, created using .join(), so we need str() !
    #                         trunk_vlan_list.append(str(vlan_id))

    #                 # now use "VLAN/TrunkInterfaces" api endpoint to set trunk vlans.
    #                 # query parameters has index to interface
    #                 params = {
    #                     "index": f"IfIndex={interface.key}",
    #                 }

    #                 # body data has the list of allowed vlans
    #                 data = {
    #                     "IfIndex": int(interface.key),
    #                     "PermitVlanList": ','.join(trunk_vlan_list),
    #                 }

    #                 try:
    #                     success = self._put(path="VLAN/TrunkInterfaces", params=params, data=json.dumps(data))
    #                     if not success:
    #                         # not sure what happened!
    #                         self.error.status = True
    #                         self.error.description = "Error adding vlans to trunk! Interface is now in UNKNOWN state!"
    #                         self.error.details = ""
    #                         return False
    #                 except Exception as err:
    #                     self.error.status = True
    #                     self.error.description = "Error adding vlans to trunk! Interface is now in UNKNOWN state!"
    #                     self.error.details = format(err)
    #                     return False
    #             # all OK, now do the book keeping
    #             dprint("Calling Bookkeeping...")
    #             super().set_interface_vlans(interface=interface, untagged_vlan=untagged_vlan, tagged_vlans=tagged_vlans, allow_all=allow_all)
    #             return True
    #         # error ?
    #         self.error.status = True
    #         self.error.description = f"Error setting untagged vlan and {mode} mode!"
    #         self.error.details = "We're not sure what happened (?)"
    #         return False
    #     except Exception as err:
    #         self.error.status = True
    #         self.error.description = f"Error setting untagged vlan and {mode} mode"
    #         self.error.details = format(err)
    #         return False

    def vlan_create(self, vlan_id: int, vlan_name: str) -> bool:
        """
        Create a new vlan on this device. Upon success, this then needs to call the base class for book keeping!

        Args:
            id (int): the vlan id
            name (str): the name of the vlan

        Returns:
            True on success, False on error and set self.error variables.
        """
        dprint(f"Aruba_AOSS_RestConnector.vlan_create() for vlan {vlan_id} = '{vlan_name}'")

        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        # new vlan attributes in POST body data
        data = {
            "vlan_id": vlan_id,
            "name": vlan_name,
        }

        try:
            # create requires a HTTP POST
            success = self._post(path="vlans", data=json.dumps(data))
            self._close_device()
            if success:
                # all OK, now do the book keeping
                super().vlan_create(vlan_id=vlan_id, vlan_name=vlan_name)
                return True
            # error ?
            self.error.status = True
            self.error.description = "Error creating vlan!"
            self.error.details = f"We're not sure what happened (?) Http return code {self.response.status_code}"
            return False
        except Exception as err:
            self._close_device()
            self.error.status = True
            self.error.description = "Error creating vlan!"
            self.error.details = format(err)
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
        dprint(f"Aruba_AOSS_RestConnector.vlan_edit() for vlan {vlan_id} = '{vlan_name}'")

        vlan = self.get_vlan_by_id(vlan_id)
        if not vlan:
            self.error.status = True
            self.error.description = f"Vlan {vlan_id} does not exist!"
            self.error.details = ""
            return False

        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        # and body data with the updated values.
        data = {
            "vlan_id": vlan_id,
            "name": vlan_name,
        }

        try:
            # create requires a HTTP POST
            success = self._put(path=f"vlans/{vlan_id}", data=json.dumps(data))
            self._close_device()
            if success:
                # all OK, now do the book keeping
                super().vlan_edit(vlan_id=vlan_id, vlan_name=vlan_name)
                return True
            # error ?
            self.error.status = True
            self.error.description = "Error editing vlan!"
            self.error.details = f"We're not sure what happened (?) Http return code {self.response.status_code}"
            return False
        except Exception as err:
            self._close_device()
            self.error.status = True
            self.error.description = "Error editing vlan!"
            self.error.details = format(err)
            return False

    def vlan_delete(self, vlan_id: int) -> bool:
        """
        Delete the vlan. Upon success, this then needs to call the base class for book keeping!

        Args:
            id (int): the vlan id to delete

        Returns:
            True on success, False on error and set self.error variables.
        """
        dprint(f"Aruba_AOSS_RestConnector.vlan_delete() for vlan {vlan_id}")

        vlan = self.get_vlan_by_id(vlan_id)
        if not vlan:
            self.error.status = True
            self.error.description = f"Vlan {vlan_id} does not exist!"
            self.error.details = ""
            return False

        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        # this is a simple HTTP DELETE call, with vlan ID as url extension
        try:
            success = self._delete(path=f"vlans/{vlan_id}")
            self._close_device()
            if success:
                # all OK, now do the book keeping
                super().vlan_delete(vlan_id=vlan_id)
                return True
            # error ?
            self.error.status = True
            self.error.description = "Error deleting vlan!"
            self.error.details = f"We're not sure what happened (?) Http return code {self.response.status_code}"
            return False
        except Exception as err:
            self._close_device()
            self.error.status = True
            self.error.description = "Error deleting vlan!"
            self.error.details = format(err)
            return False

    def save_running_config(self) -> bool:
        """
        save the current config to startup. Note this uses SSH (Netmiko), as this is NOT supported via the REST API.

        Returns:
            (bool) - True if this succeeds, False on failure. self.error() will be set in that case
        """
        dprint("Aruba_AOSS_RestConnector().save_running_config()")

        # Not implemented in API, so run the save command with _execute_command(), which uses Netmiko / SSH
        return self._execute_command(command="write mem")

    #
    # here we override the SSH command execution using Netmiko,
    # and implement it using the API.
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
        dprint(f"Aruba_AOSS_RestConnector()._execute_command() '{command}'")

        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        # see https://github.com/aruba/arubaos-switch-api-python/blob/master/src/common.py

        # POST data contain the cli command to execute
        data = {
            "cmd": command,
        }

        try:
            success = self._post(path="cli", data=json.dumps(data))
            if success:
                # Body return data looks like:
                # {"uri":"/cli","cmd":"display interface 1","result_base64_encoded":"IDEgY3Vy..."}
                #
                # the base64 decoded value is a byte string, so convert that to ascii (or unicode?)
                #
                # set the expect return field with command text:
                try:
                    text = base64.b64decode(self.response.json()["result_base64_encoded"]).decode('utf-8')
                    dprint(f"Command return text:\n{text}")
                    self.netmiko_output = text
                except Exception as err:
                    self.netmiko_output = f"Error converting command text returned:\n{format(err)}"

                self._close_device()
                return True
            # error ?
            self.error.status = True
            self.error.description = "Error running command!"
            self.error.details = f"We're not sure what happened (?) Http return code {self.response.status_code}"
            self._close_device()
            return False
        except Exception as err:
            self._close_device()
            self.error.status = True
            self.error.description = "Error running command!"
            self.error.details = format(err)
            return False
