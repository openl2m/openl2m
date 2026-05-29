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
import datetime
import json
import traceback
import urllib.parse

# This is a custom AOS-CX REST connector that performs significantly faster then the
# "pyaoscx" package, which also appears to be not thread-safe when running with gunicorn.py
#
# This uses the documented REST API, and allows us to handle any AOS-CX device.
# see https://developer.arubanetworks.com/aruba-aoscx/docs/python-getting-started
# a good API doc is at
# https://arubanetworking.hpe.com/techdocs/AOS-CX/10.16/PDF/rest_v10-0x.pdf
#
# Here are how the AOS-CX REST api uses the various HTTP methods (from the REST API docs):
#
# The GET method is a read method that gets the resource specified by the URI. Data is returned
# in JSON format in the response body. Using GET on a resource collection results in a list of
# URIs. Each URI in the list corresponds to a specific resource in the collection.
# Using GET on a specific resource returns the attributes of that resource.
#
# The POST method creates an instance of a resource in the collection specified by the URI.
#
# The PUT method updates an instance of a resource by replacing the existing resource
# with the resource provided in the request body.
#
# The PATCH method updates values in an existing resource using only the desired values
# in the request body.

from switches.utils import dprint, dvar
from switches.constants import LOG_TYPE_ERROR, LOG_DEVICE_REST_OPEN, LOG_DEVICE_REST_CLOSE, LOG_DEVICE_REST_GET

from switches.connect.restconnector import RESTConnector
from switches.connect.classes import Interface, PoePort, Transceiver, NeighborDevice
from switches.connect.aruba_aoscx.utils import aoscx_parse_duplex
from switches.connect.constants import (
    POE_PORT_ADMIN_DISABLED,
    POE_PORT_ADMIN_ENABLED,
    VLAN_ADMIN_DISABLED,
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
    # IANA_TYPE_OTHER,
    # IANA_TYPE_IPV4,
    # IANA_TYPE_IPV6,
)

#####################################################################
# NOTE: each function call is enclosed by an open / close API call, #
# in order to avoid token time out and resource overload.           #
#####################################################################


class AosCxConnector(RESTConnector):
    """
    This class implements a Connector() to get switch information from Aruba AOS-CX devices.
    """

    def __init__(self, request=False, group=False, switch=False):
        """
        Initialize the object
        """
        dprint("AosCxConnector() __init__")
        super().__init__(request, group, switch)
        self.description = "Aruba AOS-CX REST API driver"
        self.vendor_name = "Aruba Networks"

        # Netmiko is used for SSH connections. Here are some defaults a class can set.
        #
        # device_type:
        # if set, will be a value that will override (ie. hardcode) values from the
        # "Credentials Profile" (aka the NetmikoProfile() object)
        self.netmiko_device_type = "aruba_aoscx"
        # no need to override default of netmiko_valid_device_types[]
        # also no need to set the 'disable paging' command.
        # even though there is now a Netmiko 'aruba_aoscx' driver, we still see prompt time-outs.
        # setting this to True disables prompt checking, and uses send_command_timing() calls.
        self.netmiko_ignore_prompt = True

        # we can override the settings calculated from switch.read_only, group.ready_only and user.profile.read_only
        # but we should only do this to create a Read-Only driver!
        # self.read_only = True

        # REST driver settings
        self.api_prefix = ""  # rest uri prefix, ie. "/rest/v10.13"
        self.latest_api_version = ""  # the latest version supported by thye device
        self.aoscx_session = False  # no open REST session

        # capabilities of current driver:
        self.can_change_admin_status = True
        # self.can_change_vlan = True
        self.can_edit_vlans = True
        self.can_change_poe_status = True
        self.can_change_description = True
        # self.can_save_config = True
        self.can_reload_all = True
        # self.can_edit_tags = True  # True if this driver can edit 802.1q tagged vlans on interfaces

    def __del__(self):
        """when we close the object, release the REST ticket, so the switch does not run out of resources!"""
        self._close_device()

    def get_my_basic_info(self) -> bool:
        """
        load 'basic' list of interfaces with status.
        return True on success, False on error and set self.error variables
        """
        dprint("AosCxConnector().get_my_basic_info()")

        if not self._open_device():
            dprint("  _open_device() failed!")
            # self.error already set!
            return False

        ##############################################
        # get system facts first, ie OS, model, etc. #
        ##############################################
        try:
            system = self._get(path="system?depth=1", message="Get Systems")
        except Exception as error:
            dprint(f"  get_my_basic_info(): error getting system info: {format(error)}")
            self.error.status = True
            self.error.description = "Error getting system info!"
            self.error.details = ""
            self.add_warning(
                warning=f"Error getting system info!\n{repr(error)} ({str(type(error))}) => {traceback.format_exc()}"
            )
            return False

        self.add_more_info("System", "Firmware Version", system["software_version"])
        self.set_driver_info("os_version", system["software_version"])
        # this is typically the same as software_version:
        # self.add_more_info('System', 'Firmware Version', system["firmware_version"])
        if "build_date" in system["software_info"]:
            self.add_more_info("System", "Firmware Info", f"Build date: {system['software_info']['build_date']}")

        # this same info is in 'Type' above:
        # self.add_more_info('System', 'Platform', system["platform_name"])

        if "hostname" in system:
            self.hostname = system["hostname"]
            self.add_more_info('System', 'Hostname', self.hostname)
            self.set_driver_info("hostname", self.hostname)
        else:
            self.add_more_info('System', 'Hostname', '<not set>')

        # system["domain_name"]
        #     self.add_more_info('System', 'Domain Name', system["domain_name"])
        # else:
        #     self.add_more_info('System', 'Domain Name', '')

        if "boot_time" in system:
            boot_time = datetime.datetime.fromtimestamp(system["boot_time"])
            self.add_more_info("System", "Boot Time", boot_time)

        # if 'system_contact' in system["other_config"] and system["other_config"]['system_contact']:
        #     self.add_more_info('System', 'Contact', system["other_config"]['system_contact'])
        # if 'system_location' in in system["other_config"] and system["other_config"]['system_location']:
        #     self.add_more_info('System', 'Location', system["other_config"]['system_location'])
        # if 'system_contact' in in system["other_config"] and system["other_config"]['system_description']:
        #     self.add_more_info('System', 'Description', system["other_config"]['system_description'])

        #######################
        # get sub-system info #
        #######################
        # try:
        #     subsystems = self._get(path="system/subsystems?depth=2", message="Get Sub-Systems")
        # except Exception as error:
        #     dprint(f"  get_my_basic_info(): error geting subsystem info: {format(error)}")
        #     self.error.status = True
        #     self.error.description = "Error getting subsystem info!"
        #     self.error.details = ""
        #     self.add_warning(
        #         warning=f"Error getting subsystem info!\n{repr(error)} ({str(type(error))}) => {traceback.format_exc()}"
        #     )
        #     return False

        # # this has info about each subsystem in the environment:
        # ps_id = 1  # power supply ID, starting at 1
        # for name, subsystem in subsystems.items():
        #     # format is 'subsys-name,unit-id'
        #     subsys_name, subsys_id = name.split(",", 1)  # split once, we want just 2 components.
        #     if subsys_name == "chassis":
        #         if subsystem["product_info"]["part_number"]:
        #             # this is an existing chassis, not an empty "data slot"
        #             dprint(f"  Found CHASSIS #{subsys_id}")
        #             # for the first chassis, add some info:
        #             if int(subsys_id) == 1:
        #                 self.add_more_info(
        #                     "System",
        #                     "Type",
        #                     f"{subsystem['product_info']['product_name']} ({subsystem['product_info']['part_number']})",
        #                 )
        #                 self.add_more_info("System", "Serial", subsystem["product_info"]["serial_number"])

        #                 self.set_driver_info(
        #                     "model",
        #                     f"{subsystem['product_info']['product_name']} ({subsystem['product_info']['part_number']})",
        #                 )
        #                 self.set_driver_info("serial_number", subsystem["product_info"]["serial_number"])

        #             # we also want 'power_supplies' information for this chassis:
        #             if "power_supplies" in subsystem:
        #                 for ps_name, ps in subsystem["power_supplies"].items():
        #                     dprint(f"\n  FOUND PS INFO for {ps_name}\n{ps}\n")
        #                     if ps["status"] == "ok":
        #                         # get used and max power:
        #                         power_used = int(ps["characteristics"]["instantaneous_power"])
        #                         power_max = int(ps["characteristics"]["maximum_power"])
        #                         dprint("  MAX: {power_max} W, used {power_used} W")
        #                         new_ps = self.add_poe_powersupply(id=ps_id, power_available=power_max)
        #                         new_ps.set_consumed_power(power=power_used)
        #                         self.poe_power_consumed += power_used  # total value
        #                         ps_id += 1
        #                         # set a few more attributes, currently not displayed yet (9/2024)
        #                         new_ps.name = ps["name"]
        #                         new_ps.description = ps["identity"]["description"]
        #                         new_ps.model = ps["identity"]["model_number"]
        #                         new_ps.part_number = ps["identity"]["product_name"]
        #                         new_ps.serial = ps["identity"]["serial_number"]

        #####################
        # get the VLAN info #
        #####################
        try:
            vlans = self._get(path="system/vlans?depth=2", message="Get VLANs")
        except Exception as error:
            dprint("  get_my_basic_info(): error getting Vlans!")
            self.error.status = True
            self.error.description = "Error getting Vlans!"
            self.error.details = f"Cannot read device vlans: {format(error)}"
            self._close_device()
            return False

        for vid, vlan in vlans.items():
            dvar(var=vlan, header=f"VLAN: {vid}")
            vlan_id = int(vid)
            self.add_vlan_by_id(vlan_id=vlan_id, vlan_name=vlan["name"])
            v = self.vlans[vlan_id]
            # is this vlan enabled?
            if not vlan["admin"] == "up" and not vlan["oper_state"] == "up":
                dprint("  VLAN is disabled!")
                v.admin_status = VLAN_ADMIN_DISABLED
            if "voice" in vlan and vlan["voice"]:
                dprint(f"Voice Vlan = '{vlan['voice']}' {type(vlan['voice'])})")
                v.voice = True
            # mac/ethernet info found at "macs", eg. "macs": "/rest/v10.13/system/vlans/1/macs"
            # and "static_macs": "/rest/v10.13/system/vlans/1/static_macs"
            # set several REST uri's for additional vlan data
            v.vlan_uri = vlan["macs"]
            v.macs_uri = vlan["macs"]
            v.static_macs_uri = vlan["static_macs"]

        ###########################
        # get any VRF information #
        ###########################
        try:
            vrfs = self._get(path="system/vrfs?depth=2", message="Get VRFs")
        except Exception as error:
            dprint("  get_my_basic_info(): error getting VRFs!")
            self.error.status = True
            self.error.description = "Error getting VRFs!"
            self.error.details = f"Cannot read device VRFs: {format(error)}"
            self._close_device()
            return False

        for name, vrf in vrfs.items():
            dvar(var=vrf, header="VRF:")
            v = self.get_vrf_by_name(name=name)
            v.rd = vrf["rd"]
            # for VRF address families, get "system/vrfs/<vrf_name>/vrf_address_families"
            # af = self._get(path=f"system/vrfs/{name}/vrf_address_families?depth=2", message=f"Get Address Family for VRF {name}")
            # dvar(var=af, header="Address Families:")

        ######################
        # get the interfaces #
        ######################
        try:
            interfaces = self._get(path="system/interfaces?depth=2", message="Get Interfaces")
        except Exception as error:
            self.error.status = True
            self.error.description = "Error getting interfaces!"
            self.error.details = f"Cannot read device interfaces: {format(error)}"
            dprint("  get_my_basic_info(): error getting interfaces!")
            self._close_device()
            return False

        for if_name, interface in interfaces.items():
            dprint(f"--- {if_name} ---")
            # see the attributes available:
            # dvar(var=interface, header=f"Interface: {if_name}")

            # add an OpenL2M Interface() object
            iface = Interface(if_name)
            iface.name = if_name
            iface.type = IF_TYPE_ETHERNET  # unless we learn differently later
            if interface["description"]:  # when not set, this is None, so catch that!
                iface.description = interface["description"]

            # this is Admin Up/Down:
            # note that defaults are admin_status = oper_status = False (ie Down)
            # here are the values that appear to indicate admin and operational state:
            # Admin shutdown:
            #     "admin": "down",
            #     "admin_state": "down",
            #     "link_speed": 0,
            #     "link_state": "down",
            #     "hw_intf_info": {
            #         ...
            #         "max_speed": "5000",

            # Admin no shutdown, port down:
            #     "admin": null,
            #     "admin_state": "down",
            #     "link_speed": 0,
            #     "link_state": "down",
            #     "hw_intf_info": {
            #         ...
            #         "max_speed": "5000",

            # Admin no shutdown, port up:

            #     "admin": null,
            #     "admin_state": "up",
            #     "link_speed": 1000000000,
            #     "link_state": "up",

            if "link_state" in interface:
                if interface["link_state"] == "up":  # operationally up
                    # dprint("LINK_STATE UP!")
                    iface.admin_status = True
                    iface.oper_status = True
                    if "link_speed" in interface:  # for physicl ports, better be :-)
                        if interface["link_speed"] is not None:
                            # iface.speed is in 1Mbps increments:
                            iface.speed = int(int(interface["link_speed"]) / 1000000)
                else:  # not up, we can get port speed from hw_info
                    # dprint("LINK_STATE NOT UP!")
                    if "hw_intf_info" in interface and "max_speed" in interface["hw_intf_info"]:
                        iface.speed = int(interface["hw_intf_info"]["max_speed"])  # already in Mbps !

            # interface not up, so just down, or admin shutdown?
            if not iface.oper_status:
                # dprint("LINK NOT UP, CHECKING ADMIN STATE")
                if "admin" in interface and not interface["admin"]:
                    dprint("ADMIN STATE UP!")
                    iface.admin_status = True

            # read some other interface attributes...
            if "duplex" in interface:
                iface.duplex = aoscx_parse_duplex(interface["duplex"])
            if "ip_mtu" in interface:
                iface.mtu = interface["ip_mtu"]
            if "mvrp_enable" in interface:
                iface.gvrp_enabled = interface["mvrp_enable"]
            if "routing" in interface:
                iface.is_routed = interface["routing"]

            # get details about the port type:
            if "type" in interface:
                match interface["type"]:
                    case "vlan":
                        dprint("VLAN interface")
                        iface.type = IF_TYPE_VIRTUAL
                    case "system":  # regular ethernet
                        iface.type = IF_TYPE_ETHERNET
                    case "lag":
                        dprint("LACP virtual interface")
                        iface.type = IF_TYPE_LAGG
                        iface.lacp_type = LACP_IF_TYPE_AGGREGATOR
                        # 'bond_status': {'bond_speed': 10000000000, 'state': 'up'} shows for virtual LACP interfaces:
                        if "bond_status" in interface and "state" in interface["bond_status"]:
                            if interface["bond_status"]["state"] == "up":
                                iface.oper_status = True
                                dprint(f"LACP speed found: {interface['bond_status']['bond_speed']}")
                                # iface.speed is in 1Mbps increments:
                                iface.speed = int(int(interface["bond_status"]["bond_speed"]) / 1000000)
                            else:
                                # down interface
                                iface.open_status = False

                            # LACP members are stored in "interfaces"
                            # 'interfaces': {'1/1/16': '/rest/v10.09/system/interfaces/1%2F1%2F16'},
                            if "interfaces" in interface:
                                for if_name in interface["interfaces"]:
                                    iface.lacp_members[if_name] = if_name

            #
            # Find VLAN Info for interface:
            # set in "applied_vlan_mode", "applied_vlan_tag" and "applied_vlan_trunks"
            #
            if "applied_vlan_tag" in interface and interface["applied_vlan_tag"] is not None:
                # the untagged vlan
                for vid in interface["applied_vlan_tag"]:
                    # there is only 1:
                    iface.untagged_vlan = int(vid)
            if "applied_vlan_mode" in interface:
                if interface["applied_vlan_mode"] == "access":
                    iface.is_tagged = False
                elif interface["applied_vlan_mode"] == "native-untagged":
                    iface.is_tagged = True
                    # see if there are vlans on the trunk (untagged vlan is set above)
                    # vlan_trunks = {'500': '/rest/v10.04/system/vlans/500', '504': '/rest/v10.04/system/vlans/504'}
                    if "applied_vlan_trunks" in interface:
                        for vid in interface["applied_vlan_trunks"]:
                            iface.add_tagged_vlan(int(vid))

            # this is from an older API version, no longer in v10.09
            # check LACP 'stuff':
            # if "lacp" in interface and interface["lacp"] == "active":
            #     dprint("LAG interface")
            #     iface.type = IF_TYPE_LAGG
            #     iface.lacp_type = LACP_IF_TYPE_AGGREGATOR
            #     # LACP members are stored in "interfaces"
            #     # 'interfaces': {'1/1/16': '/rest/v10.09/system/interfaces/1%2F1%2F16'},
            #     if "interfaces" in interface:
            #         for if_name in interface["interfaces"]:
            #             iface.lacp_members[if_name] = if_name
            #     # get speed
            #     if "bond_status" in interface:
            #         dprint(f"Bond Status found: {interface['bond_status']['bond_speed']}")
            #         # iface.speed is in 1Mbps increments:
            #         iface.speed = int(int(interface["bond_status"]["bond_speed"]) / 1000000)
            #
            # elif "lacp_current" in interface and interface["lacp_current"]:
            #     # lacp member interface:
            #     iface.lacp_type = LACP_IF_TYPE_MEMBER
            #     lacp_actor = int(interface["lacp_status"]["actor_key"])
            #     iface.lacp_master_index = lacp_actor
            #     iface.lacp_master_name = f"lag{lacp_actor}"
            #     # we don't have the LAG interface yet, so cannot add member there!

            # Check for LACP membership:
            if "other_config" in interface and "lacp-aggregation-key" in interface["other_config"]:
                # lacp member interface:
                iface.lacp_type = LACP_IF_TYPE_MEMBER
                lacp_actor = int(interface["other_config"]["lacp-aggregation-key"])
                iface.lacp_master_index = lacp_actor
                iface.lacp_master_name = f"lag{lacp_actor}"
                # we don't have the LAG interface yet, so cannot add member there!

            if "ip4_address" in interface:
                if interface["ip4_address"]:
                    dprint(f"   IPv4 = {interface['ip4_address']}")
                    iface.add_ip4_network(address=interface["ip4_address"])
                    if "ip4_address_secondary" in interface:
                        dprint(f"   IPv4(2nd) = {interface['ip4_address_secondary']}")

            # check VRF membership
            if "vrf" in interface:
                if interface["vrf"] is not None:
                    vrf_name = interface["vrf"]
                    if iface.name not in self.vrfs[vrf_name].interfaces:
                        self.vrfs[vrf_name].interfaces.append(iface.name)
                    # assing this vrf name to the interface:
                    iface.vrf_name = vrf_name

            # check plugable modules for optics info
            if "pm_info" in interface:
                if "connector" in interface["pm_info"] and interface["pm_info"]["connector"] != "absent":
                    dprint(f"Optics info found:\n{interface['pm_info']}\n")
                    trx = Transceiver()
                    if "external_connector" in interface["pm_info"]:
                        trx.connector = interface["pm_info"]["external_connector"]

                    if "xcvr_desc" in interface["pm_info"]:
                        trx.type = interface["pm_info"]["xcvr_desc"]
                    else:  # see if we can goble something from speed and connector info:
                        if "speed" in interface["pm_info"]:
                            gig_speed = int(interface["pm_info"]["speed"]) / 1000
                            trx.type = f"{gig_speed}g {interface['pm_info']['connector']}"

                    if "vendor_name" in interface["pm_info"]:
                        trx.vendor = interface["pm_info"]["vendor_name"]

                    if "wavelength" in interface["pm_info"]:
                        trx.wavelength = interface["pm_info"]["wavelength"]
                    iface.transceiver = trx

            # check if this has PoE Capabilities
            if "poe_interface" in interface:
                # this does not mean PoE is available for this interface. Let's check...
                poe_info = self._get(uri=interface["poe_interface"])
                if poe_info:
                    dprint(f"--- POE found for {if_name} ---")
                    # there is probably a more 'global' system/device way to see if PoE capabilities exist:
                    self.poe_capable = True
                    self.poe_enabled = True

                    # assign an OpenL2M PoePort() object
                    if poe_info["config"]["admin_disable"]:
                        poe_status = POE_PORT_ADMIN_DISABLED
                    else:
                        poe_status = POE_PORT_ADMIN_ENABLED
                    iface.poe_entry = PoePort(index=if_name, admin_status=poe_status)

                    # get power used. Listed in watts, convert to milliwatts:
                    consumed = int(poe_info["measurements"]["power_drawn"] * 1000)
                    if consumed > 0:
                        super().set_interface_poe_consumed(iface, consumed)

            # save the various lldp and cdp URI's
            if "ip6_addresses" in interface:
                iface.ipv6_uri = interface["ip6_addresses"]
            if "ip6_autoconfigured_addresses" in interface:
                iface.ipv6_link_local_uri = interface["ip6_autoconfigured_addresses"]
            if "cdp_neighbors" in interface:
                iface.cdp_uri = interface["cdp_neighbors"]
            if "lldp_neighbors" in interface:
                iface.lldp_uri = interface["lldp_neighbors"]

            # add finally add this interface!
            self.add_interface(iface)

        # fix up some things that are not known at time of interface discovery,
        # such as LACP master interfaces:
        self._map_lacp_members_to_logical()

        self.save_driver_info()

        self._close_device()
        return True

    def get_my_hardware_details(self) -> bool:
        """
        TBD: Placeholder to read more hardware details of the AOS-CX device.
        """
        return True

    def get_my_client_data(self) -> bool:
        """
        read mac addressess, and lldp neigbor info.
        Not yet fully supported in AOS-CX API.
        return True on success, False on error and set self.error variables
        """
        dprint("AosCxConnector.get_my_client_data()")

        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        # get mac address table, this is based on vlans:
        dprint("Getting MAC table per VLAN:")
        for vlan in self.vlans.values():
            # dvar(var=vlan, header="VLAN OBJECT")
            dprint(f"Vlan {vlan.id}:")
            for uri in (vlan.macs_uri, vlan.static_macs_uri):
                try:
                    macs = self._get(uri=f"{uri}?depth=2", message="ETH INFO")
                    # now get details for each mac address
                    for mac_addr, mac in macs.items():
                        mac_if_name = next(iter(mac["port"]))  # we use first element only!
                        dprint(f"  MAC Address: {mac_addr} -> {mac_if_name}")
                        # add this to the known addressess:
                        self.add_learned_ethernet_address(
                            if_name=mac_if_name, eth_address=mac["mac_addr"], vlan_id=int(vlan.id)
                        )

                except Exception as err:
                    dprint(f"Vlan get macs error: {err}")
                    description = f"Cannot get ethernet table for vlan {vlan.id}"
                    details = f"Error: {repr(err)} ({str(type(err))})\n{traceback.format_exc()}"
                    self.add_warning(warning=description)
                    self.add_log(type=LOG_TYPE_ERROR, action=LOG_DEVICE_REST_GET, description=details)

        dprint("Getting LLDP data per INTERFACE:")

        for iface in self.interfaces.values():
            dprint(f"  Interface {iface.name}:")
            try:
                neighbors = self._get(uri=f"{iface.lldp_uri}?depth=2", message="LLDP INFO")
                for nb_name, lldp_nb in neighbors.items():
                    dprint(f"LLDP FOUND: {nb_name}")
                    neighbor = NeighborDevice(lldp_nb["chassis_id"])
                    nb = lldp_nb["neighbor_info"]  # this is where the "real" info resides!
                    neighbor.set_sys_name(nb["chassis_name"])
                    neighbor.set_sys_description(nb["chassis_description"])
                    # remote device port info:
                    neighbor.port_name = nb["port_description"]
                    neighbor.set_port_description(nb["port_description"])
                    # remote chassis info:
                    neighbor.set_chassis_string(lldp_nb["chassis_id"])
                    if nb["chassis_id_subtype"] == "link_local_addr":
                        neighbor.set_chassis_type(LLDP_CHASSIC_TYPE_ETH_ADDR)
                    # parse capabilities:
                    capabilities = nb["chassis_capability_enabled"].lower()
                    dprint(f"  Capabilities: {capabilities}")
                    if "bridge" in capabilities:
                        neighbor.set_capability(LLDP_CAPABILITIES_BRIDGE)
                    if "router" in capabilities:
                        neighbor.set_capability(LLDP_CAPABILITIES_ROUTER)
                    # Following NOT tested; we are assuming the following two are correct:
                    if "wlan" in capabilities:
                        neighbor.set_capability(LLDP_CAPABILITIES_WLAN)
                    if "phone" in capabilities:
                        neighbor.set_capability(LLDP_CAPABILITIES_PHONE)
                    # remote device management address, this is a list(), take first entry
                    if len(nb["mgmt_ip_list"]) > 0:
                        # hardcoding to IPv4 for now...
                        neighbor.set_management_address_v4(address=nb["mgmt_ip_list"])
                    # add to device interface, we need to do this on the Connector (ie self.)
                    # to track lldp count:
                    self.add_neighbor_object(if_name=iface.name, neighbor=neighbor)

            except Exception as err:
                dprint(f"ERROR getting lldp neighbors: {err}")
                description = f"Cannot get LLDP table for interface '{iface.name}'"
                details = f"Error getting '{iface.lldp_uri}': {repr(err)} ({str(type(err))})\n{traceback.format_exc()}"
                self.add_warning(warning=description)
                self.add_log(type=LOG_TYPE_ERROR, action=LOG_DEVICE_REST_GET, description=details)
                continue

        # done...
        self._close_device()
        return True

    def set_interface_admin_status(self, interface: Interface, new_state: bool) -> bool:
        """
        set the interface to the requested state (up or down)
        interface = Interface() object for the requested port
        new_state = True / False  (enabled/disabled)
        return True on success, False on error and set self.error variables
        """
        # interface.admin_status = new_state
        dprint(f"AosCxConnector.set_interface_admin_status() for {interface.name} to {bool(new_state)}")

        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        if new_state:
            state = "up"
        else:
            state = "down"
        data = {"admin": state}

        # encode the / in the interface to a url format:
        if_name_url = urllib.parse.quote(interface.name, safe="")

        try:
            success = self._patch(
                path=f"system/interfaces/{if_name_url}", data=json.dumps(data), message="Set Interface Status"
            )
        except Exception as err:
            self.error.status = True
            self.error.description = "Exception error changing interface status!"
            self.error.details = f"Info: {format(err)}"
            dprint(f"ERROR: set_interface_admin_status() failed!\n{format(err)}")
            self._close_device()
            return False

        self._close_device()

        if not success:
            dprint(f"   Interface change to '{state}' FAILED!")
            self.error.status = True
            self.error.description = "Error returned changing interface status!"
            if self.response.text:
                self.error.details = f"Response text: {self.response.text}"
            else:
                self.error.details = "We're not sure what happened, sorry... :-("
            dprint("ERROR: set_interface_admin_status() failed, not sure why?")
            # we need to add error info here!!!
            return False

        dprint(f"  Interface change to '{state}' OK!")
        # call the super class for bookkeeping.
        super().set_interface_admin_status(interface, new_state)
        return True

    def set_interface_description(self, interface: Interface, description: str) -> bool:
        """
        set the interface description (aka. description) to the string
        interface = Interface() object for the requested port
        new_description = a string with the requested text
        return True on success, False on error and set self.error variables
        """
        dprint(f"AosCxConnector.set_interface_description() for {interface.name} to '{description}'")

        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        data = {"description": description}

        # encode the / in the interface to a url format:
        if_name_url = urllib.parse.quote(interface.name, safe="")

        try:
            success = self._patch(
                path=f"system/interfaces/{if_name_url}", data=json.dumps(data), message="Set Interface Description"
            )
        except Exception as err:
            self.error.status = True
            self.error.description = "Exception error changing interface description!"
            self.error.details = f"Info: {format(err)}"
            dprint(f"ERROR: set_interface_description() exception!\n{format(err)}")
            self._close_device()
            return False

        self._close_device()

        if not success:
            dprint("ERROR: Interface description change FAILED, not sure why?")
            # we need to add error info here!!!
            self.error.status = True
            self.error.description = "Error changing interface description!"
            if self.response.text:
                self.error.details = f"Response text: {self.response.text}"
            else:
                self.error.details = "We're not sure what happened, sorry... :-("
            return False

        dprint("   Descr Set OK!")
        # call the super class for bookkeeping.
        super().set_interface_description(interface, description)
        self._close_device()
        return True

    def set_interface_poe_status(self, interface: Interface, new_state: int) -> bool:
        """
        set the interface Power-over-Ethernet status as given
        interface = Interface() object for the requested port

        Args:
            interface: the Interface to modify
            new_state = POE_PORT_ADMIN_ENABLED or POE_PORT_ADMIN_DISABLED

        Returns:
            True on success, False on error and set self.error variables
        """
        dprint(f"AosCxConnector.set_interface_poe_status() for {interface.name} to {new_state}")

        if not interface.poe_entry:
            # this should never happen!
            dprint("PoE change requested, but interface does not support PoE!!!")
            self.error.status = True
            self.error.description = "PoE change requested, but interface does not support PoE!!!"
            self.error.details = ""
            return False

        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        # entry is "admin_disable", so "opposite" logic!
        if new_state == POE_PORT_ADMIN_ENABLED:
            state = False
        else:
            state = True

        data = {
            "config": {
                "admin_disable": state,
            },
        }

        # encode the / in the interface to a url format:
        if_name_url = urllib.parse.quote(interface.name, safe="")

        try:
            success = self._patch(
                path=f"system/interfaces/{if_name_url}/poe_interface",
                data=json.dumps(data),
                message="Set Interface PoE Status",
            )
        except Exception as err:
            self.error.status = True
            self.error.description = "Exception error changing interface PoE!"
            self.error.details = f"Info: {format(err)}"
            dprint(f"  set_interface_poe_status() exception!\n{format(err)}")
            self._close_device()
            return False

        self._close_device()

        if not success:
            dprint("   Interface PoE change FAILED, not sure why?")
            # we need to add error info here!!!
            self.error.status = True
            self.error.description = "Error changing interface PoE!"
            if self.response.text:
                self.error.details = f"Response text: {self.response.text}"
            else:
                self.error.details = "We're not sure what happened, sorry... :-("
            return False

        dprint("   PoE change OK!")
        # call the super class for bookkeeping.
        super().set_interface_poe_status(interface, new_state)
        self._close_device()
        return True

    # def set_interface_untagged_vlan(self, interface: Interface, new_vlan_id: int) -> bool:
    #     """
    #     set the interface untagged vlan to the given vlan
    #     interface = Interface() object for the requested port
    #     new_vlan_id = an integer with the requested untagged vlan
    #     return True on success, False on error and set self.error variables
    #     """
    #     dprint(f"AosCxConnector.set_interface_untagged_vlan() for {interface.name} to vlan {new_vlan_id}")

    #     if not self._open_device():
    #         dprint("_open_device() failed!")
    #         return False

    #     # get AosCxInterface:
    #     try:
    #         aoscx_interface = AosCxInterface(session=self.aoscx_session, name=interface.name)
    #         aoscx_interface.get()  # we need a fully "populated" AosCxInterface() object
    #         dprint(f"  AosCxInterface.get() OK: {aoscx_interface.name}")
    #         dvar(var=aoscx_interface, header="\n\nINTERFACE:")
    #         dvar(var=aoscx_interface.vlan_trunks, header="\n\n  TRUNK VLANS")
    #     except Exception as err:
    #         dprint(f"  set_interface_untagged_vlan(): AosCxInterface.get() failed!\n{traceback.format_exc()}")
    #         self.error.status = True
    #         self.error.description = "Error establishing connection!"
    #         self.error.details = f"Cannot read device interface: {format(err)}\n{traceback.format_exc()}"
    #         self._close_device()
    #         return False

    #     # 802.1q-tagged or untagged?
    #     if interface.is_tagged:
    #         # this needs to set the native vlan!
    #         dprint("  tagged port: calling aoscx.set_native_vlan()")

    #         try:
    #             # Note:
    #             # here we work around a possible bug in the pyaoscx module,
    #             # where 'trunk vlan allow all' translates into an empty aoscx_interface.vlans_trunks list
    #             # this causes the new vlan to be the only one allowed on the trunk.
    #             # Work around by explicityly setting the trunk allows vlans.
    #             # also see https://github.com/aruba/pyaoscx/issues/36
    #             vlan_trunks = []
    #             for vlan_id in interface.vlans:
    #                 v = AosCxVlan(session=self.aoscx_session, vlan_id=vlan_id)
    #                 vlan_trunks.append(v)
    #             aoscx_interface.vlan_trunks = vlan_trunks
    #             # and now set the new native vlan
    #             changed = aoscx_interface.set_native_vlan(vlan=int(new_vlan_id), tagged=False)
    #         except Exception as err:
    #             dprint(f"ERROR in aoscx_interface.set_untagged_vlan() object: {err}")
    #             self.error.status = True
    #             self.error.description = "Error setting untagged vlan on trunk port!"
    #             self.error.details = f"ERROR in aoscx_interface.set_native_vlan(): {format(err)}"
    #             self._close_device()
    #             return False
    #         if changed:
    #             dprint("   Vlan Change OK!")
    #             # call the super class for bookkeeping.
    #             super().set_interface_untagged_vlan(interface, new_vlan_id)
    #             self._close_device()
    #             return True

    #         dprint("   Vlan Change FAILED for Unknown Reasons!")
    #         # we need to add error info here!!!
    #         self.error.status = True
    #         self.error.description = "Error setting untagged vlan!"
    #         self.error.details = "UNKNOWN ERROR in aoscx_interface.set_native_vlan()!"
    #         self._close_device()
    #         return False

    #     # untagged, ie set access mode vlan
    #     dprint("  access mode port: calling aoscx.set_untagged_vlan()")
    #     try:
    #         changed = aoscx_interface.set_untagged_vlan(vlan=int(new_vlan_id))
    #     except Exception as err:
    #         dprint(f"ERROR in aoscx_interface.set_untagged_vlan() object: {err}")
    #         self.error.status = True
    #         self.error.description = "Error setting access vlan!"
    #         self.error.details = f"ERROR in aoscx_interface.set_untagged_vlan(): {format(err)}"
    #         self._close_device()
    #         return False
    #     if changed:
    #         dprint("   Vlan Change OK!")
    #         # call the super class for bookkeeping.
    #         super().set_interface_untagged_vlan(interface, new_vlan_id)
    #         self._close_device()
    #         return True

    #     dprint("   Vlan Change FAILED for Unknown Reasons!")
    #     # we need to add error info here!!!
    #     self.error.status = True
    #     self.error.description = "Error setting access vlan!"
    #     self.error.details = "UNKNOWN ERROR in aoscx_interface.set_untagged_vlan()!"
    #     self._close_device()
    #     return False

    # def set_interface_vlans(
    #     self, interface: Interface, untagged_vlan: int, tagged_vlans: list[int], allow_all: bool = False
    # ) -> bool:
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
    #         f"AosCxConnector.set_interface_vlans() for {interface.name} to untagged {untagged_vlan}, tagged {tagged_vlans}, allow_all={allow_all}"
    #     )

    #     if not self._open_device():
    #         dprint("_open_device() failed!")
    #         return False

    #     # get AosCxInterface:
    #     try:
    #         aoscx_interface = AosCxInterface(session=self.aoscx_session, name=interface.name)
    #         aoscx_interface.get()  # we need a fully "populated" AosCxInterface() object
    #         dprint(f"  AosCxInterface.get() OK: {aoscx_interface.name}")
    #         dvar(var=aoscx_interface, header="\n\nINTERFACE:")
    #         dvar(var=aoscx_interface.vlan_trunks, header="\n\n  TRUNK VLANS")
    #     except Exception as err:
    #         dprint(f"  set_interface_untagged_vlan(): AosCxInterface.get() failed!\n{traceback.format_exc()}")
    #         self.error.status = True
    #         self.error.description = "Error establishing connection!"
    #         self.error.details = f"Cannot read device interface: {format(err)}\n{traceback.format_exc()}"
    #         self._close_device()
    #         return False

    #     # now set mode and vlans
    #     try:
    #         if not tagged_vlans and not allow_all:
    #             # no tagged vlan, ie "access mode".
    #             dprint("  access mode.")
    #             aoscx_interface.set_vlan_mode("access")
    #             aoscx_interface.set_untagged_vlan(vlan=int(untagged_vlan))

    #         else:
    #             dprint("  trunk mode.")
    #             # trunk mode, setup mode and native vlan:
    #             aoscx_interface.set_vlan_mode("native-untagged")
    #             # Note:
    #             # here we work around a possible bug in the pyaoscx module,
    #             # where 'trunk vlan allow all' translates into an empty aoscx_interface.vlans_trunks list
    #             # this causes the new vlan to be the only one allowed on the trunk.
    #             # Work around by explicityly setting the trunk allows vlans.
    #             # also see https://github.com/aruba/pyaoscx/issues/36

    #             # loop through all vlans, and see if they are allowed
    #             allow = []  # list of AosCx Vlan() objects!
    #             for vid in self.vlans:
    #                 if allow_all or vid in tagged_vlans:
    #                     # allowed!
    #                     v = AosCxVlan(session=self.aoscx_session, vlan_id=vid)
    #                     allow.append(v)
    #             # add these to the trunk config
    #             aoscx_interface.vlan_trunks = allow
    #             # set the new native vlan
    #             aoscx_interface.set_native_vlan(vlan=int(untagged_vlan), tagged=False)

    #     except Exception as err:
    #         # some error triggered
    #         dprint(f"ERROR in aoscx_interface() setting mode and vlans: {err}")
    #         self.error.status = True
    #         self.error.description = "Error setting vlans!"
    #         self.error.details = f"ERROR in aoscx_interface.set_interface_vlans(): {format(err)}"
    #         self._close_device()
    #         return False

    #     dprint("ALL OK!")

    #     # call the base Connector() for bookkeeping:
    #     super().set_interface_vlans(
    #         interface=interface, untagged_vlan=untagged_vlan, tagged_vlans=tagged_vlans, allow_all=allow_all
    #     )
    #     self._close_device()
    #     return True

    def vlan_create(self, vlan_id: int, vlan_name: str) -> bool:
        """
        Create a new vlan on this device. Upon success, this then needs to call the base class for book keeping!

        Args:
            id (int): the vlan id
            name (str): the name of the vlan

        Returns:
            True on success, False on error and set self.error variables.
        """
        dprint(f"AosCxConnector.vlan_create() for vlan {vlan_id} = '{vlan_name}'")
        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        data = {
            "name": f"{vlan_name}",
            "id": vlan_id,
            "type": "static",
            "admin": "up",
        }
        try:
            success = self._post(path="system/vlans", data=json.dumps(data), message="Create VLAN")
        except Exception as err:
            self.error.status = True
            self.error.description = "Error creating new vlan!"
            self.error.details = f"POST ERROR: {err}"
            return False

        if not success:
            self.error.status = True
            self.error.description = "Error creating new vlan!"
            self.error.details = f"POST returned {self.response.status_code}"
            return False

        # all OK, now do the book keeping
        super().vlan_create(vlan_id=vlan_id, vlan_name=vlan_name)
        self._close_device()
        return True

    def vlan_edit(self, vlan_id: int, vlan_name: str) -> bool:
        """
        Edit the vlan name. Upon success, this then needs to call the base class for book keeping!

        Args:
            id (int): the vlan id to edit
            name (str): the new name of the vlan

        Returns:
            True on success, False on error and set self.error variables.
        """
        dprint(f"AosCxConnector.vlan_edit() for vlan {vlan_id} = '{vlan_name}'")
        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        data = {
            "name": f"{vlan_name}",
            # "id": vlan_id,
        }

        try:
            success = self._patch(path=f"system/vlans/{vlan_id}", data=json.dumps(data), message="VLAN Update")
        except Exception as err:
            self.error.status = True
            self.error.details = f"Error trapped while updating vlan {vlan_id} name to '{vlan_name}': {err}"
            self._close_device()
            return False

        if not success:
            self.error.status = True
            self.error.details = f"Error updating vlan {vlan_id} name to '{vlan_name}' (not sure what happened!)"
            self._close_device()
            return False

        # all OK, now do the book keeping
        super().vlan_edit(vlan_id=vlan_id, vlan_name=vlan_name)
        self._close_device()
        return True

    def vlan_delete(self, vlan_id: int) -> bool:
        """
        Delete the vlan. Upon success, this then needs to call the base class for book keeping!

        Args:
            id (int): the vlan id to edit

        Returns:
            True on success, False on error and set self.error variables.
        """
        dprint(f"AosCxConnector.vlan_delete() for vlan {vlan_id}")
        if not self._open_device():
            dprint("_open_device() failed!")
            return False
        try:
            success = self._delete(path=f"system/vlans/{vlan_id}", message="VLAN Delete")
        except Exception as err:
            self.error.status = True
            self.error.details = f"Error trapped while deleting vlan {vlan_id}: {err}"
            self._close_device()
            return False

        if not success:
            self.error.status = True
            self.error.details = f"Error deleting vlan {vlan_id} (not sure what happened!)"
            self._close_device()
            return False

        # all OK, now do the book keeping
        super().vlan_delete(vlan_id=vlan_id)
        self._close_device()
        return True

    # def save_running_config(self) -> bool:
    #     """
    #     save the current config to startup via api.

    #     Returns:
    #         (bool) - True if this succeeds, False on failure. self.error() will be set in that case
    #     """
    #     dprint("AosCxConnector().save_running_config()")

    #     if not self._open_device():
    #         dprint("_open_device() failed!")
    #         return False

    #     # see https://github.com/aruba/pyaoscx/blob/master/pyaoscx/device.py
    #     try:
    #         aoscx_device = AosCxDevice(session=self.aoscx_session)
    #         # Create a Configuration Object
    #         config = aoscx_device.configuration()
    #         config.create_checkpoint("running-config", "startup-config")
    #     except Exception as error:
    #         dprint(f"  save_running_config(): save config failed: {format(error)}")
    #         self._close_device()
    #         self.error.status = True
    #         self.error.description = "Error saving configuration!"
    #         self.error.details = f"Error details: {format(error)}"
    #         self.add_warning(
    #             warning=f"Cannot save configuration: {repr(error)} ({str(type(error))}) => {traceback.format_exc()}"
    #         )
    #         self._close_device()
    #         return False

    #     self._close_device()
    #     return True

    def _open_device(self) -> bool:
        """
        get a pyaoscx "driver" and open a "connection" to the device
        return True on success, False on failure, and will set self.error
        """
        dprint("AOS-CX _open_device()")

        if self.aoscx_session:
            dprint("  AOS-CX Session already OPEN!")
            return True

        # do we have creds set?
        if not self.switch.netmiko_profile:
            self.error.status = True
            self.error.description = "Please configure a Credentials Profile to be able to connect to this device!"
            dprint("  _open_device: No Credentials!")
            return False

        # first check to see what the latest API version supported is
        if not self.latest_api_version:
            self._set_base_url(base_url=f"https://{self.switch.primary_ip4}/")
            # get the "rest" uri to see what versions are supported:
            response = self._get(path="rest")
            self.latest_api_version = response['latest']['version']
            self.api_prefix = response['latest']['prefix']
            self.add_more_info("System", "API Version", self.latest_api_version)
            dprint(f"  Using API version '{self.latest_api_version}'")
            dprint(f"  API documentation is at: {response['latest']['doc']}")

        # start using lastest API:
        self._set_base_url(base_url=f"https://{self.switch.primary_ip4}{self.api_prefix}/")

        # Authenticate
        headers = {
            "Accept": "*/*",
            "x-use-csrf-token": "true",
        }
        try:
            # auth data is sent in a form post
            data = {
                "username": f"{self.switch.netmiko_profile.username}",
                "password": f"{self.switch.netmiko_profile.password}",
            }
            retval = self._post(path="login", data=data, headers=headers, message="API LOGIN")
        except Exception as err:
            dprint(f"Authentication Error: {err}\nTrace:{traceback.format_exc()}")
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot open REST session: {format(err)}\n{traceback.format_exc()}"
            self.add_log(
                description=f"Cannot open REST session: {format(err)}\n{traceback.format_exc()}",
                type=LOG_TYPE_ERROR,
                action=LOG_DEVICE_REST_OPEN,
            )
            return False

        if not retval:
            dprint("  _open_device(): FAILED!")
            return False

        # parse the CSRF token and set as header for requests
        if "X-Csrf-Token" in self.response.headers:
            headers["x-csrf-token"] = self.response.headers["X-Csrf-Token"]

        self._set_headers(headers=headers)

        # and set the session cookie(s)
        self._set_cookies(cookies=self.response.cookies)

        self.aoscx_session = True

        dprint("  _open_device(): OK!")
        return True

    def _close_device(self) -> bool:
        """
        make sure we properly close the AOS-CX REST Session
        """
        dprint("AOS-CX _close_device()")
        if self.aoscx_session:
            # logout
            try:
                self._post(path="logout", message="API LOGOUT")
                self.aoscx_session = False
                dprint(("  session close OK!"))
            except Exception as err:
                dprint(f"Session Close Error!!!\n{err}\nTrace:{traceback.format_exc()}")
                # add some logging:
                self.add_log(
                    description=f"Session Close Error: {traceback.format_exc()}",
                    type=LOG_TYPE_ERROR,
                    action=LOG_DEVICE_REST_CLOSE,
                )
        else:
            dprint("  NOT Needed (no session!)")

        # no matter what, we return True
        return True
