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
import traceback

from switches.utils import dprint, dvar
from switches.constants import LOG_TYPE_ERROR, LOG_AOSCX_ERROR_GENERIC
from switches.connect.classes import Interface, PoePort, NeighborDevice
from switches.connect.connector import Connector
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
    #   IANA_TYPE_OTHER,
    IANA_TYPE_IPV4,
    #   IANA_TYPE_IPV6,
)


"""
Basic Aruba AOS-CX connector. This uses the documented REST API, and allows us to handle
any device supported by the Aruba Python "pyaoscx" library.
See more at https://github.com/aruba/pyaoscx/
and https://developer.arubanetworks.com/aruba-aoscx/docs/python-getting-started

For clarity, and to avoid namespace collisions with our own internal classes,
we import all AOS-CX classes as AosCx<original-name>
"""
from pyaoscx.session import Session as AosCxSession

# from pyaoscx.configuration import Configuration as AosCxConfiguration
from pyaoscx.device import Device as AosCxDevice
from pyaoscx.vlan import Vlan as AosCxVlan
from pyaoscx.mac import Mac as AosCxMac
from pyaoscx.interface import Interface as AosCxInterface
from pyaoscx.poe_interface import PoEInterface as AosCxPoEInterface
from pyaoscx.lldp_neighbor import LLDPNeighbor as AosCxLLDPNeighbor


# used to disable unknown SSL cert warnings:
import urllib3

API_VERSION = '10.08'  # '10.08' or '10.04'


class AosCxConnector(Connector):
    """
    This class implements a Connector() to get switch information from Aruba AOS-CX devices.
    """

    def __init__(self, request=False, group=False, switch=False):
        """
        Initialize the object
        """
        dprint("AosCxConnector() __init__")
        super().__init__(request, group, switch)
        self.description = "Aruba AOS-CX API driver"
        self.vendor_name = "Aruba Networks"

        # this is a read-write driver:
        self.switch.read_only = False
        # this will be the pyaoscx driver session object
        self.aoscx_session = False
        # this can now be cached!
        # self.set_do_not_cache_attribute('aoscx_session')

        # capabilities of current driver:
        self.can_change_admin_status = True
        self.can_change_vlan = True
        self.can_edit_vlans = True
        self.can_change_poe_status = True
        self.can_change_description = True
        self.can_save_config = False  # not needed.
        self.can_reload_all = False

    def get_my_basic_info(self) -> bool:
        '''
        load 'basic' list of interfaces with status.
        return True on success, False on error and set self.error variables
        '''
        dprint("AosCxConnector().get_my_basic_info()")
        if not self._open_device():
            dprint("  _open_device() failed!")
            # self.error already set!
            return False

        # get facts of device first, ie OS, model, etc.!
        # see https://github.com/aruba/pyaoscx/blob/master/pyaoscx/device.py
        try:
            aoscx_device = AosCxDevice(session=self.aoscx_session)
            aoscx_device.get()
        except Exception as error:
            dprint(f"  get_my_basic_info(): AosCxDevice.get() failed: {format(error)}")
            self._close_device()
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot read device information: {format(error)}"
            self.add_warning(
                f"Cannot read device information: {repr(error)} ({str(type(error))}) => {traceback.format_exc()}"
            )
            return False

        # dobject(aoscx_device, "AosCxDevice:")

        # aoscx_config = AosCxConfiguration(session=self.aoscx_session)
        # dobject(aoscx_config, "AosCxConfiguration:")

        # self.hostname = aoscx_device.hostname
        # # if first time for this device (or changed), update hostname
        # if self.switch.hostname != aoscx_device.hostname:
        #     self.switch.hostname = aoscx_device.hostname
        #     self.switch.save()

        self.add_more_info('System', 'Firmware Version', aoscx_device.software_version)
        # this is typically the same as software_version:
        # self.add_more_info('System', 'Firmware Version', aoscx_device.firmware_version)
        if 'build_date' in aoscx_device.software_info:
            self.add_more_info('System', 'Firmware Info', f"Build date: {aoscx_device.software_info['build_date']}")
        self.add_more_info('System', 'Platform', aoscx_device.platform_name)

        # if aoscx_device.hostname:  # this is None when not set!
        #     self.add_more_info('System', 'Hostname', self.hostname)
        # else:
        #     self.add_more_info('System', 'Hostname', '')

        # if aoscx_device.domain_name:  # this is None when not set!
        #     self.add_more_info('System', 'Domain Name', aoscx_device.domain_name)
        # else:
        #     self.add_more_info('System', 'Domain Name', '')

        # dprint(f"\nCapabilities = {aoscx_device.capabilities}")
        # dprint(f"\nCapacities = {aoscx_device.capacities}")
        # dprint(f"\nBoot time = {aoscx_device.boot_time}")
        if aoscx_device.boot_time:
            boot_time = datetime.datetime.fromtimestamp(aoscx_device.boot_time)
            self.add_more_info('System', 'Boot Time', boot_time)
        # dprint(f"\nOther Config = {aoscx_device.other_config}")
        # dprint(f"\nMgmt Intf Status = {aoscx_device.mgmt_intf_status}")

        # if 'system_contact' in aoscx_device.other_config and aoscx_device.other_config['system_contact']:
        #     self.add_more_info('System', 'Contact', aoscx_device.other_config['system_contact'])
        # if 'system_location' in aoscx_device.other_config and aoscx_device.other_config['system_location']:
        #     self.add_more_info('System', 'Location', aoscx_device.other_config['system_location'])
        # if 'system_contact' in aoscx_device.other_config and aoscx_device.other_config['system_description']:
        #     self.add_more_info('System', 'Description', aoscx_device.other_config['system_description'])

        # not sure what to get here yet:
        # aoscx_device.get_subsystems()
        # for key in device.subsystems:
        #    print(f"        attribute: {key}")

        # get the VLAN info, this get class objects pyaoscx.vlan.Vlan()
        try:
            aoscx_vlans = AosCxVlan.get_facts(session=self.aoscx_session)
        except Exception as error:
            self._close_device()
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot read device vlans: {format(error)}"
            dprint("  get_my_basic_info(): AosCxVlan.get_facts() failed!")
            return False

        for id, vlan in aoscx_vlans.items():
            dvar(f"VLAN(): {vlan}")
            # dprint(f"Vlan {id}: {vlan['name']}")
            vlan_id = int(id)
            self.add_vlan_by_id(vlan_id=vlan_id, vlan_name=vlan['name'])
            # is this vlan enabled?
            if not vlan['admin'] == 'up' and not vlan['oper_state'] == 'up':
                dprint("  VLAN is disabled!")
                self.vlans[vlan_id].admin_status = VLAN_ADMIN_DISABLED
            if 'voice' in vlan and vlan['voice']:
                dprint(f"Voice Vlan = '{vlan['voice']}' {type(vlan['voice'])})")
                self.vlans[vlan_id].voice = True

        # and get the interfaces:
        try:
            # get_facts() returns Interface() items as dictionaries, not classes!
            aoscx_interfaces = AosCxInterface.get_facts(session=self.aoscx_session)
            # get_all() return a proper class pyaoscx.interface.Interface() ...
            # aoscx_interfaces2 = AosCxInterface.get_all(session=self.aoscx_session)
        except Exception as error:
            self._close_device()
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot read device interfaces: {format(error)}"
            dprint("  get_my_basic_info(): AosCxInterface.get_facts() failed!")
            return False

        # if you use the class object, and want to get a fully materialized (ie. flushed-out) object,
        # you need to call .get() on each Interface() object first!
        # for if_name, aoscx_interface in aoscx_interfaces2.items():
        #     try:
        #         aoscx_interface.get()
        #         dobject(aoscx_interface, f"\n\n=== AosCxInterface() CLASS: {if_name} ===")
        #     except Exception as err:
        #         dprint(f"Error '{if_name}'.get(): {err}")
        # return True

        for if_name, aoscx_interface in aoscx_interfaces.items():
            dprint(f"AosCxInterface[]: {if_name}")
            # see the attributes available:
            # dvar(aoscx_interface, f"AosCxInterface[]: {if_name}")

            # add an OpenL2M Interface() object
            iface = Interface(if_name)
            iface.name = if_name
            iface.type = IF_TYPE_ETHERNET
            if aoscx_interface['description']:  # when not set, this is None, so catch that!
                iface.description = aoscx_interface['description']
            # this is Admin Up/Down:
            if 'admin' in aoscx_interface and aoscx_interface['admin'] == 'down':
                iface.admin_status = False
                iface.oper_status = False
            else:
                # Admin UP, but do we have link?
                iface.admin_status = True
                if 'admin_state' in aoscx_interface and aoscx_interface['admin_state'] == 'up':
                    iface.oper_status = True
                    if 'link_speed' in aoscx_interface:  # better be :-)
                        if not aoscx_interface['link_speed'] is None:
                            # iface.speed is in 1Mbps increments:
                            iface.speed = int(int(aoscx_interface['link_speed']) / 1000000)
                else:
                    iface.oper_status = False
            if 'duplex' in aoscx_interface:
                iface.duplex = aoscx_parse_duplex(aoscx_interface['duplex'])
            if 'ip_mtu' in aoscx_interface:
                iface.mtu = aoscx_interface['ip_mtu']
            if 'mvrp_enable' in aoscx_interface:
                iface.gvrp_enabled = aoscx_interface['mvrp_enable']
            if 'routing' in aoscx_interface:
                iface.is_routed = aoscx_interface['routing']
            if 'type' in aoscx_interface:
                if aoscx_interface['type'] == 'vlan':
                    dprint("VLAN interface")
                    iface.type = IF_TYPE_VIRTUAL

            #
            # Find VLAN Info for interface:
            # set in "applied_vlan_mode", "applied_vlan_tag" and "applied_vlan_trunks"
            #
            if 'applied_vlan_tag' in aoscx_interface and aoscx_interface['applied_vlan_tag'] is not None:
                # the untagged vlan
                for id in aoscx_interface['applied_vlan_tag']:
                    # there is only 1:
                    iface.untagged_vlan = int(id)
            if 'applied_vlan_mode' in aoscx_interface:
                if aoscx_interface['applied_vlan_mode'] == 'access':
                    iface.is_tagged = False
                elif aoscx_interface['applied_vlan_mode'] == 'native-untagged':
                    iface.is_tagged = True
                    # see if there are vlans on the trunk (untagged vlan is set above)
                    # vlan_trunks = {'500': '/rest/v10.04/system/vlans/500', '504': '/rest/v10.04/system/vlans/504'}
                    if 'applied_vlan_trunks' in aoscx_interface:
                        for id in aoscx_interface['applied_vlan_trunks']:
                            iface.add_tagged_vlan(int(id))

            # check LACP 'stuff':
            if 'lacp' in aoscx_interface and aoscx_interface['lacp'] == 'active':
                dprint("LAG interface")
                iface.type = IF_TYPE_LAGG
                iface.lacp_type = LACP_IF_TYPE_AGGREGATOR
                # get speed
                if 'bond_status' in aoscx_interface:
                    dprint(f"Bond Status found: {aoscx_interface['bond_status']['bond_speed']}")
                    # iface.speed is in 1Mbps increments:
                    iface.speed = int(int(aoscx_interface['bond_status']['bond_speed']) / 1000000)

            elif 'lacp_current' in aoscx_interface and aoscx_interface['lacp_current']:
                # lacp member interface:
                iface.lacp_type = LACP_IF_TYPE_MEMBER
                lacp_actor = int(aoscx_interface['lacp_status']['actor_key'])
                iface.lacp_master_index = lacp_actor
                iface.lacp_master_name = f"lag{lacp_actor}"

            if 'ip4_address' in aoscx_interface:
                if aoscx_interface['ip4_address']:
                    dprint(f"   IPv4 = {aoscx_interface['ip4_address']}")
                    iface.add_ip4_network(aoscx_interface['ip4_address'])
                    if 'ip4_address_secondary' in aoscx_interface:
                        dprint(f"   IPv4(2nd) = {aoscx_interface['ip4_address_secondary']}")

            # check if this has PoE Capabilities
            try:
                # go get PoE info:
                aoscx_iface = AosCxInterface(session=self.aoscx_session, name=if_name)
                aoscx_poe_iface = AosCxPoEInterface(session=self.aoscx_session, parent_interface=aoscx_iface)
                # get both configuration data (which has poe enable/disable status)
                aoscx_poe_iface.get(selector='status')
                # as well as status data, which has power usage:
                aoscx_poe_iface.get(selector='configuration')

                dprint(f"   +++ POE Exists for {if_name} ===")
                # there is probably a more 'global' system/device way to see if PoE capabilities exist:
                self.poe_capable = True
                self.poe_enabled = True
                # assign an OpenL2M PoePort() object
                # dprint(f"POE: config.admin_disabled={aoscx_poe.config['admin_disable']}")
                if aoscx_poe_iface.config['admin_disable']:
                    poe_status = POE_PORT_ADMIN_DISABLED
                else:
                    poe_status = POE_PORT_ADMIN_ENABLED
                poe_entry = PoePort(index=if_name, admin_status=poe_status)
                iface.poe_entry = poe_entry
                # get power used. Listed in watts, convert to milliwatts:
                consumed = int(aoscx_poe_iface.measurements['power_drawn'] * 1000)
                if consumed > 0:
                    super().set_interface_poe_consumed(iface, consumed)

            except Exception as error:
                dprint(f"   +++ NO PoE! - exception: {format(error)}")

            self.add_interface(iface)

        # done with REST connection:
        # self._close_device()

        # the REST API gives responses in alphbetic order, eg 1/1/10 before 1/1/2.
        # sort this to the human natural order we expect:
        self.set_interfaces_natural_sort_order()

        # fix up some things that are not known at time of interface discovery,
        # such as LACP master interfaces:
        self._map_lacp_members_to_logical()

        return True

    def get_my_hardware_details(self) -> bool:
        '''
        TBD: Placeholder to read more hardware details of the AOS-CX device.
        '''
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
        # get mac address table, this is based on vlans:
        dprint("Getting MAC table per VLAN:")
        for vlan_id in self.vlans.keys():
            dprint(f"Vlan {vlan_id}:")
            try:
                v = AosCxVlan(session=self.aoscx_session, vlan_id=int(vlan_id))
                v.get()
                if hasattr(v, 'name'):
                    # vlan 1 does not typically have a name!
                    dprint(f"  VLAN {v.name}")
            except Exception as err:
                dprint(f"v = Vlan() error: {err}")
                description = f"Cannot get ethernet table for vlan {vlan_id}"
                details = f"pyaoscx Vlan() Error: {repr(err)} ({str(type(err))})\n{traceback.format_exc()}"
                self.add_warning(description)
                self.add_log(type=LOG_TYPE_ERROR, action=LOG_AOSCX_ERROR_GENERIC, description=details)
                continue
            try:
                # this gets ethernet addresses by vlan:
                vlan_macs = AosCxMac.get_all(session=self.aoscx_session, parent_vlan=v)
            except Exception as err:
                dprint(f"ERROR in AosCxMac.get_all(): {err}")
            else:
                # now get details for each mac address
                for mac in vlan_macs.values():
                    try:  # this occasionally fails!
                        mac.get()  # materialize the object from the device
                        dprint(f"  MAC Address: {mac} -> {mac.port}")
                        # for name in mac.__dict__:
                        #    dprint(f"      attribute: {name} = {mac.__dict__[name]}")
                        # add this to the known addressess:
                        self.add_learned_ethernet_address(
                            if_name=mac.port.name, eth_address=mac.mac_address, vlan_id=int(vlan_id)
                        )
                    except Exception as err:
                        dprint(f"ERROR in mac.get(): {err}")
                    # just try the next one...

        dprint("Getting LLDP data per INTERFACE:")
        for if_name in self.interfaces.keys():
            dprint(f"  Interface {if_name}:")
            try:
                aoscx_iface = AosCxInterface(session=self.aoscx_session, name=if_name)
                neighbors = AosCxLLDPNeighbor.get_all(session=self.aoscx_session, parent_interface=aoscx_iface)
                for nb_name, nb in neighbors.items():
                    dprint(f"AOS-CX LLDP FOUND: on {if_name} => {nb_name} -> {nb}")
                    try:  # this occasionally fails!
                        nb.get()
                        # for attrib, value in nb.__dict__.items():
                        #    dprint(f"  {attrib} -> {value}")
                        # get an OpenL2M NeighborDevice()
                        neighbor = NeighborDevice(nb.chassis_id)
                        neighbor.set_sys_name(nb.neighbor_info['chassis_name'])
                        neighbor.set_sys_description(nb.neighbor_info['chassis_description'])
                        # remote device port info:
                        neighbor.port_name = nb.port_id
                        neighbor.set_port_description(nb.neighbor_info['port_description'])
                        # remote chassis info:
                        neighbor.set_chassis_string(nb.chassis_id)
                        if nb.neighbor_info['chassis_id_subtype'] == 'link_local_addr':
                            neighbor.set_chassis_type(LLDP_CHASSIC_TYPE_ETH_ADDR)
                        # parse capabilities:
                        capabilities = nb.neighbor_info['chassis_capability_enabled'].lower()
                        dprint(f"  Capabilities: {capabilities}")
                        if 'bridge' in capabilities:
                            neighbor.set_capability(LLDP_CAPABILITIES_BRIDGE)
                        if 'router' in capabilities:
                            neighbor.set_capability(LLDP_CAPABILITIES_ROUTER)
                        # Following NOT tested; we are assuming the following two are correct:
                        if 'wlan' in capabilities:
                            neighbor.set_capability(LLDP_CAPABILITIES_WLAN)
                        if 'phone' in capabilities:
                            neighbor.set_capability(LLDP_CAPABILITIES_PHONE)
                        # remote device management address, this is a list(), take first entry
                        if len(nb.neighbor_info['mgmt_ip_list']) > 0:
                            # hardcoding to IPv4 for now...
                            neighbor.set_management_address(
                                address=nb.neighbor_info['mgmt_ip_list'], type=IANA_TYPE_IPV4
                            )
                        # add to device interface:
                        self.add_neighbor_object(if_name, neighbor)

                    except Exception as err:
                        dprint(f"ERROR in neighbor.get(): {err}")
                    # just try the next one...
            except Exception as err:
                dprint(f"neighbors = AosCxLLDPNeighbor.get_all() error: {err}")
                description = f"Cannot get LLDP table for interface '{if_name}'"
                details = f"pyaoscx LLDPNeighbor() Error: {repr(err)} ({str(type(err))})\n{traceback.format_exc()}"
                self.add_warning(description)
                self.add_log(type=LOG_TYPE_ERROR, action=LOG_AOSCX_ERROR_GENERIC, description=details)
                continue

        # done...
        # self._close_device()
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
        try:
            aoscx_interface = AosCxInterface(session=self.aoscx_session, name=interface.name)
            aoscx_interface.get()
        except Exception as error:
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot read device interface: {format(error)}"
            dprint(f"  set_interface_admin_status(): AosCxInterface.get() failed!\n{format(error)}")
            self._close_device()
            return False

        if new_state:
            state = "up"
        else:
            state = "down"
        # changed = aoscx_interface.set_state(state=state)
        aoscx_interface.admin_state = state
        changed = aoscx_interface.apply()
        # self._close_device()
        if changed:
            dprint(f"  Interface change '{state}' OK!")
            # call the super class for bookkeeping.
            super().set_interface_admin_status(interface, new_state)
            return True
        else:
            dprint(f"   Interface change '{state}' FAILED!")
            # we need to add error info here!!!
            return False

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
        try:
            aoscx_interface = AosCxInterface(session=self.aoscx_session, name=interface.name)
            aoscx_interface.get()
        except Exception as error:
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot read device interface: {format(error)}"
            dprint("  set_interface_description(): AosCxInterface.get() failed!")
            self._close_device()
            return False

        aoscx_interface.description = description
        changed = aoscx_interface.apply()
        # self._close_device()
        if changed:
            dprint("   Descr OK!")
            # call the super class for bookkeeping.
            super().set_interface_description(interface, description)
            return True
        else:
            dprint("   Descr FAILED!")
            # we need to add error info here!!!
            return False

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
        if interface.poe_entry:
            if not self._open_device():
                dprint("_open_device() failed!")
                return False
            # go get PoE info:
            try:
                aoscx_interface = AosCxInterface(session=self.aoscx_session, name=interface.name)
                aoscx_poe = AosCxPoEInterface(session=self.aoscx_session, parent_interface=aoscx_interface)
                aoscx_poe.get()
            except Exception as error:
                self.error.status = True
                self.error.description = "Error establishing connection!"
                self.error.details = f"Cannot read device interface: {format(error)}"
                dprint("  set_interface_poe_status(): AosCxInterface or AosCxPoEInterface.get() failed!")
                self._close_device()
                return False

            dprint(f"  +++ POE Exists for {interface.name} ===")
            if new_state == POE_PORT_ADMIN_ENABLED:
                aoscx_poe.power_enabled = True
                changed = aoscx_poe.apply()
            else:
                aoscx_poe.power_enabled = False
                changed = aoscx_poe.apply()
            # self._close_device()
            if changed:
                dprint("   PoE change OK!")
                # call the super class for bookkeeping.
                super().set_interface_poe_status(interface, new_state)
                return True
            else:
                dprint("   PoE change FAILED!")
                # we need to add error info here!!!
                return False
        else:
            # this should never happen!
            dprint("PoE change requested, but interface does not support PoE!!!")
            self.error.status = True
            self.error.description = "PoE change requested, but interface does not support PoE!!!"
            self.error.details = ""
            return False

    def set_interface_untagged_vlan(self, interface: Interface, new_vlan_id: int) -> bool:
        """
        set the interface untagged vlan to the given vlan
        interface = Interface() object for the requested port
        new_vlan_id = an integer with the requested untagged vlan
        return True on success, False on error and set self.error variables
        """
        dprint(f"AosCxConnector.set_interface_untagged_vlan() for {interface.name} to vlan {new_vlan_id}")
        if not self._open_device():
            dprint("_open_device() failed!")
            return False
        try:
            aoscx_interface = AosCxInterface(session=self.aoscx_session, name=interface.name)
            aoscx_interface.get()
            dprint(f"  AosCxInterface.get() OK: {aoscx_interface.name}")
        except Exception as err:
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot read device interface: {format(err)}"
            dprint("  set_interface_untagged_vlan(): AosCxInterface.get() failed!")
            self._close_device()
            return False

        dprint("  Get AosCxVlan()")
        try:
            aoscx_vlan = AosCxVlan(session=self.aoscx_session, vlan_id=new_vlan_id)
        except Exception as err:
            dprint(f"ERROR getting AosCxVlan() object: {err}")
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = f"ERROR getting AosCxVlan() object: {format(err)}"
            self._close_device()
            return False
        else:
            # aoscx_vlan.get()
            dprint("  set_untagged_vlan()")
            try:
                changed = aoscx_interface.set_untagged_vlan(aoscx_vlan)
            except Exception as err:
                dprint(f"ERROR in aoscx_interface.set_untagged_vlan() object: {err}")
                self.error.status = True
                self.error.description = "Error establishing connection!"
                self.error.details = f"ERROR in aoscx_interface.set_untagged_vlan(): {format(err)}"
                self._close_device()
                return False
            else:
                # change = aoscs_vlan.apply()
                # self._close_device()
                if changed:
                    dprint("   Vlan Change OK!")
                    # call the super class for bookkeeping.
                    super().set_interface_untagged_vlan(interface, new_vlan_id)
                    return True
                else:
                    dprint("   Vlan Change FAILED!")
                    # we need to add error info here!!!
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
        dprint(f"AosCxConnector.vlan_create() for vlan {vlan_id} = '{vlan_name}'")
        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        new_vlan = AosCxVlan(session=self.aoscx_session, vlan_id=vlan_id, name=vlan_name, voice=False)
        try:
            new_vlan.apply()
        except Exception as err:
            self.error.status = True
            self.error.details = f"Error creating new vlan {vlan_id}: {err}"
            return False

        # all OK, now do the book keeping
        super().vlan_create(vlan_id=vlan_id, vlan_name=vlan_name)
        return True

    def vlan_edit(self, vlan_id: int, vlan_name: str) -> bool:
        '''
        Edit the vlan name. Upon success, this then needs to call the base class for book keeping!

        Args:
            id (int): the vlan id to edit
            name (str): the new name of the vlan

        Returns:
            True on success, False on error and set self.error variables.
        '''
        dprint(f"AosCxConnector.vlan_edit() for vlan {vlan_id} = '{vlan_name}'")
        if not self._open_device():
            dprint("_open_device() failed!")
            return False
        try:
            vlan = AosCxVlan(session=self.aoscx_session, vlan_id=vlan_id)
            vlan.get()
            vlan.name = vlan_name
            changed = vlan.apply()
        except Exception as err:
            self.error.status = True
            self.error.details = f"Error trapped while updating vlan {vlan_id} name to '{vlan_name}': {err}"
            return False

        if not changed:
            self.error.status = True
            self.error.details = f"Error updating vlan {vlan_id} name to '{vlan_name}' (not sure what happened!)"
            return False
        # all OK, now do the book keeping
        super().vlan_edit(vlan_id=vlan_id, vlan_name=vlan_name)
        return True

    def vlan_delete(self, vlan_id: int) -> bool:
        '''
        Delete the vlan. Upon success, this then needs to call the base class for book keeping!

        Args:
            id (int): the vlan id to edit

        Returns:
            True on success, False on error and set self.error variables.
        '''
        dprint(f"AosCxConnector.vlan_delete() for vlan {vlan_id}")
        if not self._open_device():
            dprint("_open_device() failed!")
            return False
        try:
            vlan = AosCxVlan(session=self.aoscx_session, vlan_id=vlan_id)
            vlan.delete()
            # changed = vlan.apply()  # is this needed ?
        except Exception as err:
            self.error.status = True
            self.error.details = f"Error trapped while deleting vlan {vlan_id}: {err}"
            return False
        # all OK, now do the book keeping
        super().vlan_delete(vlan_id=vlan_id)
        return True

    def _open_device(self) -> bool:
        '''
        get a pyaoscx "driver" and open a "connection" to the device
        return True on success, False on failure, and will set self.error
        '''
        dprint("AOS-CX _open_device()")

        # do we want to check SSL certificates ?
        if not self.switch.netmiko_profile.verify_hostkey:
            dprint("  Cert warnings disabled in urllib3!")
            # disable unknown cert warnings
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            # or all warnings:
            # urllib3.disable_warnings()

        if self.aoscx_session:
            dprint("  AOS-CX Session FOUND!")
            return True

        # first "connection", we need to authenticate:
        if not self.switch.netmiko_profile:
            self.error.status = True
            self.error.description = "Please configure a Credentials Profile to be able to connect to this device!"
            dprint("  _open_device: No Credentials!")
            return False

        try:
            dprint(f"  Creating AosCxSession(ip_address={self.switch.primary_ip4}, api={API_VERSION})")
            self.aoscx_session = AosCxSession(ip_address=self.switch.primary_ip4, api=API_VERSION)
            self.aoscx_session.open(
                username=self.switch.netmiko_profile.username, password=self.switch.netmiko_profile.password
            )
            dprint("  session OK!")
            # dprint(f"  SESSION.cookies():\n{self.aoscx_session.cookies()}")
            # dprint(f"  SESSION.s:\n{self.aoscx_session.s}")
            # dprint(f"  SESSION.s(pformat):\n{pprint.pformat(self.aoscx_session.s)}")

            return True
        except Exception as err:
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot open REST session: {format(err)}"
            dprint(f"  _open_device: AosCxSession.open() failed: {format(err)}")
            return False

    def _close_device(self) -> bool:
        '''
        make sure we properly close the AOS-CX REST Session
        '''
        dprint("AOS-CX _close_device()")
        # do we want to check SSL certificates ?
        if not self.switch.netmiko_profile.verify_hostkey:
            dprint("  Cert warnings disabled in urllib3!")
            # disable unknown cert warnings
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            # or all warnings:
            # urllib3.disable_warnings()
        self.aoscx_session.close()
        self.aoscx_session = False
        return True
