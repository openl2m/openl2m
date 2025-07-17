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

#
# Basic Napalm connector. This allows us to handle any device supported by
# the Napalm Library, at least in read-only mode.
#

import traceback

from django.http.request import HttpRequest

from napalm import get_network_driver

from switches.models import Switch, SwitchGroup
from switches.utils import dprint, uptime_to_string
from switches.constants import (
    LOG_TYPE_ERROR,
    LOG_NAPALM_ERROR_FACTS,
    LOG_NAPALM_ERROR_INTERFACES,
    LOG_NAPALM_ERROR_VLANS,
    LOG_NAPALM_ERROR_IF_IP,
    LOG_NAPALM_ERROR_MAC,
    LOG_NAPALM_ERROR_ARP,
    LOG_NAPALM_ERROR_LLDP,
    LOG_NAPALM_ERROR_DRIVER,
    LOG_NAPALM_ERROR_OPEN,
)
from switches.connect.classes import Interface, NeighborDevice
from switches.connect.connector import Connector
from switches.connect.utils import interface_name_to_long
from switches.connect.constants import (
    IF_TYPE_ETHERNET,
    LLDP_CAPABILITIES_REPEATER,
    LLDP_CAPABILITIES_BRIDGE,
    LLDP_CAPABILITIES_ROUTER,
    LLDP_CAPABILITIES_WLAN,
    LLDP_CAPABILITIES_PHONE,
    LLDP_CAPABILITIES_DOCSIS,
    LLDP_CAPABILITIES_STATION,
    LLDP_CAPABILITIES_OTHER,
)
from switches.connect.junos_pyez.utils import junos_get_real_ifname


class NapalmConnector(Connector):
    """
    This class implements a "Napalm" connector to get switch information.
    """

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        """
        Initialize the object
        """
        dprint("NapalmConnector() __init__")
        super().__init__(request, group, switch)
        self.description = 'Napalm library (R/O) driver'
        self.vendor_name = "Napalm Library"
        # force READ-ONLY for now! We have not implemented changing settings.
        self.read_only = True

        self.add_more_info('Connection', 'Type', f"Napalm Connector for '{self.switch.napalm_device_type}'")
        self.napalm_device = False  # this will be the Napalm driver connection
        # and we dont want to cache this:
        self.set_do_not_cache_attribute('napalm_device')

    def get_my_basic_info(self) -> bool:
        '''
        load 'basic' list of interfaces with status.
        return True on success, False on error and set self.error variables
        '''
        if not self._open_device():
            return False
        # get facts of device first, ie OS, model, etc.!
        try:
            facts = self.napalm_device.get_facts()
        except Exception as e:
            self.error.status = True
            self.error.description = "Cannot get device facts"
            self.error.details = f"Napalm Error: {repr(e)} ({str(type(e))})\n{traceback.format_exc()}"
            dprint(f"   napalm.device.get_facts() Exception: {e.__class__.__name__}\n{self.error.details}\n")
            self.add_warning(warning="Napalm error in get_facts() - Likely not implemented!")
            self.add_log(type=LOG_TYPE_ERROR, action=LOG_NAPALM_ERROR_FACTS, description=f"ERROR: {self.error.details}")
            return False
        dprint(f"facts = \n{facts}\n")

        self.hostname = facts['hostname']
        self.add_more_info('System', 'Hostname', self.hostname)
        self.add_more_info('System', 'Vendor', facts['vendor'])
        self.add_more_info('System', 'OS', facts['os_version'])
        self.add_more_info('System', 'Model', facts['model'])
        self.add_more_info('System', 'Uptime', uptime_to_string(int(facts['uptime'])))

        # now load the interfaces:
        try:
            interface_list = self.napalm_device.get_interfaces()
        except Exception as e:
            self.error.status = True
            self.error.description = "Cannot get interface list"
            self.error.details = f"Napalm Error: {repr(e)} ({str(type(e))})\n{traceback.format_exc()}"
            dprint(f"   napalm.device.get_interfaces() Exception: {e.__class__.__name__}\n{self.error.details}\n")
            self.add_warning(warning="Napalm error in get_interfaces() - Likely not implemented!")
            self.add_log(
                type=LOG_TYPE_ERROR, action=LOG_NAPALM_ERROR_INTERFACES, description=f"ERROR: {self.error.details}"
            )
            return False
        dprint(f"\nINTERFACES = \n{interface_list}\n")
        # parse
        for if_name, if_data in interface_list.items():
            dprint(f"\nInterface: {if_name}")

            iface = Interface(if_name)
            iface.name = if_name
            iface.type = IF_TYPE_ETHERNET
            iface.admin_status = if_data['is_enabled']
            iface.oper_status = if_data['is_up']
            iface.description = if_data['description']
            iface.speed = if_data['speed']
            iface.mtu = if_data['mtu']
            # iface.mac_address = interface_list[if_name]['mac_address']
            # iface.last_flapped = interface_list[if_name]['last_flapped']
            self.add_interface(iface)

        # now load the vlan data:
        try:
            vlan_list = self.napalm_device.get_vlans()
        except Exception as e:
            self.error.status = True
            self.error.description = "Cannot get vlan list"
            self.error.details = f"Napalm Error: {repr(e)} ({str(type(e))})\n{traceback.format_exc()}"
            dprint(f"   napalm.device.get_vlans() Exception: {e.__class__.__name__}\n{self.error.details}\n")
            self.add_warning(warning="Napalm error in get_vlans() - Likely not implemented!")
            self.add_log(type=LOG_TYPE_ERROR, action=LOG_NAPALM_ERROR_VLANS, description=f"ERROR: {self.error.details}")
            return False
        # dprint(f"\nVLANS = \n{vlan_list}\n")
        # parse
        for vlan_id, vlan_data in vlan_list.items():
            dprint(f"\nVlan {vlan_id}: {vlan_data}")
            self.add_vlan_by_id(vlan_id, vlan_data['name'])
            # add this vlan to the specified interfaces:
            for if_name in vlan_data['interfaces']:
                dprint(f"\nInterface {if_name} = vlan {vlan_id}")
                iface = self.get_interface_by_key(if_name)
                if iface.untagged_vlan > -1:
                    # untagged already set, so this must be a trunked/dot1q port.
                    # note that Napalm API does not properly read the actual PVID !
                    # so we "assume" first vlan id found is correct untagged.
                    # this is likely frequently wrong!!!
                    dprint("   --> tagged")
                    iface.is_tagged = True
                    self.add_interface_tagged_vlan(iface, vlan_id)
                else:
                    iface.untagged_vlan = int(vlan_id)

        # now load the per-interface vlan data, implemented in some drivers ?

        #
        # try:
        #     iface_list = self.napalm_device.get_interface_vlans()
        # except Exception as e:
        #     self.error.status = True
        #     self.error.description = "Cannot get interface vlan list"
        #     self.error.details = f"Napalm Error: {repr(e)} ({str(type(e))})\n{traceback.format_exc()}"
        #     dprint(f"   napalm.device.get_interface_vlan() Exception: {e.__class__.__name__}\n{self.error.details}\n")
        #     self.add_warning(warning="Napalm error in get_interface_vlan() - Likely not implemented!")
        #     self.add_log(type=LOG_TYPE_ERROR, action=LOG_NAPALM_ERROR_VLANS, description=f"ERROR: {self.error.details}")
        #     return False
        # dprint(f"interface_vlans = \n{iface_list}\n")
        #

        # now load the interface ipv4 data:
        try:
            ip_list = self.napalm_device.get_interfaces_ip()
        except Exception as e:
            self.error.status = True
            self.error.description = "Cannot get interfaces ip list"
            self.error.details = f"Napalm Error: {repr(e)} ({str(type(e))})\n{traceback.format_exc()}"
            dprint(f"   napalm.device.get_interfaces_ip() Exception: {e.__class__.__name__}\n{self.error.details}\n")
            self.add_warning(warning="Napalm error in get_interfaces_ip() - Likely not implemented!")
            self.add_log(type=LOG_TYPE_ERROR, action=LOG_NAPALM_ERROR_IF_IP, description=f"ERROR: {self.error.details}")
            return False
        dprint(f"IPs = \n{ip_list}\n")
        # parse
        for if_name, if_data in ip_list.items():
            # dprint(f"IF {if_name}: {if_data}")
            iface = self.get_interface_by_key(if_name)
            # get the IP's for this interface
            if 'ipv4' in if_data.keys():
                for ipv4, values in if_data['ipv4'].items():
                    prefix_len = values['prefix_length']
                    # dprint(f"IP: {ipv4}/{prefix_len}")
                    iface.add_ip4_network(address=ipv4, prefix_len=prefix_len)
            if 'ipv6' in if_data.keys():
                for ipv6, values in if_data['ipv6'].items():
                    prefix_len = values['prefix_length']
                    # dprint(f"IP: {ipv6}/{prefix_len}")
                    iface.add_ip6_network(address=ipv6, prefix_len=prefix_len)

        return True

    def get_my_vrfs(self) -> bool:
        '''Fill the list of VRFs on this device, if any

        Args:
            none

        Returns:
            (bool): True on success, False on failure
        '''
        try:
            vrf_table = self.napalm_device.get_network_instances()
            dprint(f"VRF table:\n{vrf_table}")
            for vrf_name, vrf in vrf_table.items():
                if vrf['type'] == 'DEFAULT_INSTANCE':  # ignore, the default (ie non-VRF) routing table
                    continue
                # create OpenL2M Vrf() object:
                dprint(f"  New VRF: {vrf_name}")
                this_vrf = self.get_vrf_by_name(name=vrf_name)
                # parse the RD
                if 'state' in vrf and 'route_distinguisher' in vrf['state']:
                    this_vrf.rd = vrf['state']['route_distinguisher']
                # parse member interfaces:
                if 'interfaces' in vrf and 'interface' in vrf['interfaces']:
                    for if_name in vrf['interfaces']['interface']:
                        dprint(f"    Found interface: {if_name}")
                        # find OpenL2M Interface():
                        iface = self.get_interface_by_key(key=if_name)
                        if iface:
                            # get the Interface() object:
                            dprint("    Interface() found!")
                            # add to the list of interfaces for this vrf
                            if iface.name not in self.vrfs[vrf_name].interfaces:
                                self.vrfs[vrf_name].interfaces.append(iface.name)
                            # adding this vrf name to the interface:
                            iface.vrf_name = vrf_name

        except Exception as e:
            self.error.status = True
            self.error.description = "Cannot get VRF table"
            self.error.details = f"Napalm Error: {repr(e)} ({str(type(e))})\n{traceback.format_exc()}"
            dprint(
                f"   napalm.device.get_network_instances() Exception: {e.__class__.__name__}\n{self.error.details}\n"
            )
            self.add_warning(warning="Napalm error in get_network_instances() - Likely not implemented!")
            self.add_log(type=LOG_TYPE_ERROR, action=LOG_NAPALM_ERROR_MAC, description=f"ERROR: {self.error.details}")

        return True

    def get_my_client_data(self) -> bool:
        '''
        return list of interfaces with static_egress_portlist
        return True on success, False on error and set self.error variables
        '''
        if not self._open_device():
            return False
        # get mac address table
        try:
            mac_table = self.napalm_device.get_mac_address_table()
            dprint(f"mac_table = \n{mac_table}\n")
            for info in mac_table:
                if_name = info['interface']
                if if_name:
                    # it is possible that the 'short' form of the interface name is used,
                    # convert to long ...
                    if_name = interface_name_to_long(if_name)
                    a = self.add_learned_ethernet_address(if_name, info['mac'])
                    if a:
                        a.set_vlan(info['vlan'])
        except Exception as e:
            self.error.status = True
            self.error.description = "Cannot get arp table"
            self.error.details = f"Napalm Error: {repr(e)} ({str(type(e))})\n{traceback.format_exc()}"
            dprint(
                f"   napalm.device.get_mac_address_table() Exception: {e.__class__.__name__}\n{self.error.details}\n"
            )
            self.add_warning(warning="Napalm error in get_mac_address_table() - Likely not implemented!")
            self.add_log(type=LOG_TYPE_ERROR, action=LOG_NAPALM_ERROR_MAC, description=f"ERROR: {self.error.details}")

        # get arp table
        try:
            arp_table = self.napalm_device.get_arp_table(vrf='')
            dprint(f"arp_table = \n{arp_table}\n")
            for info in arp_table:
                if_name = info['interface']
                if if_name:
                    # it is possible that the 'short' form of the interface name is used,
                    # convert to long ...
                    if_name = interface_name_to_long(if_name)
                    a = self.add_learned_ethernet_address(
                        if_name=if_name, eth_address=info['mac'], ip4_address=info['ip']
                    )
        except Exception as e:
            self.error.status = True
            self.error.description = "Cannot get arp table"
            self.error.details = f"Napalm Error: {repr(e)} ({str(type(e))})\n{traceback.format_exc()}"
            dprint(f"   napalm.device.get_arp_table() Exception: {e.__class__.__name__}\n{self.error.details}\n")
            self.add_warning(warning="Napalm error in get_arp_table() - Likely not implemented!")
            self.add_log(type=LOG_TYPE_ERROR, action=LOG_NAPALM_ERROR_ARP, description=f"ERROR: {self.error.details}")

        # get IPv6 neighbors
        try:
            nd_table = self.napalm_device.get_ipv6_neighbors_table()
            dprint(f"nd_table = \n{nd_table}\n")
            for neighbor in nd_table:
                if_name = neighbor['interface']
                if if_name:
                    # if irb.xx, parse out the physical interface:
                    if_name = junos_get_real_ifname(if_name=if_name)
                    # it is possible that the 'short' form of the interface name is used,
                    # convert to long ...
                    if_name = interface_name_to_long(if_name)
                    a = self.add_learned_ethernet_address(if_name, neighbor['mac'])
                    if a:
                        a.add_ip6_address(neighbor['ip'])
        except Exception as e:
            self.error.status = True
            self.error.description = "Cannot get arp table"
            self.error.details = f"Napalm Error: {repr(e)} ({str(type(e))})\n{traceback.format_exc()}"
            dprint(
                f"   napalm.device.get_ipv6_neighbors_table() Exception: {e.__class__.__name__}\n{self.error.details}\n"
            )
            self.add_warning(warning="Napalm error in get_ipv6_neighbors_table() - Likely not implemented!")
            self.add_log(type=LOG_TYPE_ERROR, action=LOG_NAPALM_ERROR_ARP, description=f"ERROR: {self.error.details}")

        # get lldp details
        try:
            lldp_details = self.napalm_device.get_lldp_neighbors_detail()
            dprint(f"lldp_details = \n{lldp_details}\n")
            # parse
            for if_name, lldp_data in lldp_details.items():
                # dprint(f"IF {if_name}: {if_data}")
                # lldp_data is a dict:
                for device in lldp_data:
                    device_id = device['remote_chassis_id']
                    neighbor = NeighborDevice(device_id)
                    neighbor.sys_name = device['remote_system_name']
                    neighbor.sys_descr = device['remote_system_description']
                    neighbor.port_name = device['remote_port']
                    neighbor.port_descr = device['remote_port_description']
                    # and the enabled capabilities:
                    for cap in device['remote_system_enable_capab']:
                        if cap == 'bridge':
                            neighbor.capabilities += LLDP_CAPABILITIES_BRIDGE
                        elif cap == 'repeater':
                            neighbor.capabilities += LLDP_CAPABILITIES_REPEATER
                        elif cap == 'wlan-access-point':
                            neighbor.capabilities += LLDP_CAPABILITIES_WLAN
                        elif cap == 'router':
                            neighbor.capabilities += LLDP_CAPABILITIES_ROUTER
                        elif cap == 'telephone':
                            neighbor.capabilities += LLDP_CAPABILITIES_PHONE
                        elif cap == 'docsis-cable-device':
                            neighbor.capabilities += LLDP_CAPABILITIES_DOCSIS
                        elif cap == 'station':
                            neighbor.capabilities += LLDP_CAPABILITIES_STATION
                        elif cap == 'other':
                            neighbor.capabilities += LLDP_CAPABILITIES_OTHER
                    self.add_neighbor_object(if_name, neighbor)
        except Exception as e:
            self.error.status = True
            self.error.description = "Cannot get lldp details"
            self.error.details = f"Napalm Error: {repr(e)} ({str(type(e))})\n{traceback.format_exc()}"
            dprint(
                f"   napalm.device.get_lldp_neighbors_detail() Exception: {e.__class__.__name__}\n{self.error.details}\n"
            )
            self.add_warning(warning="Napalm error in get_lldp_neighbors_detail() - Likely not implemented!")
            self.add_log(type=LOG_TYPE_ERROR, action=LOG_NAPALM_ERROR_LLDP, description=f"ERROR: {self.error.details}")

        return True

    def _open_device(self) -> bool:
        '''
        get a Napalm 'driver' and open connection to the device
        return True on success, False on failure, and will set self.error
        '''
        # first, get the proper driver
        driver = False
        try:
            driver = get_network_driver(self.switch.napalm_device_type)
        except Exception as e:
            self.error.status = True
            self.error.description = "Cannot get Napalm network driver"
            self.error.details = f"Napalm Error: {repr(e)} ({str(type(e))})\n{traceback.format_exc()}"
            dprint(f"   napalm.get_network_driver() Exception: {e.__class__.__name__}\n{self.error.details}\n")
            self.add_warning(warning="Napalm error in get_network_driver()!")
            self.add_log(
                type=LOG_TYPE_ERROR, action=LOG_NAPALM_ERROR_DRIVER, description=f"ERROR: {self.error.details}"
            )
            return False

        # next open connection
        self.napalm_device = driver(
            hostname=self.switch.primary_ip4,
            username=self.switch.netmiko_profile.username,
            password=self.switch.netmiko_profile.password,
            optional_args={
                "port": self.switch.netmiko_profile.tcp_port,
            },
        )
        try:
            self.napalm_device.open()
        except Exception as e:
            self.error.status = True
            self.error.description = "Cannot get Napalm connection"
            self.error.details = f"Napalm Error: {repr(e)} ({str(type(e))})\n{traceback.format_exc()}"
            dprint(f"   napalm.device.open() Exception: {e.__class__.__name__}\n{self.error.details}\n")
            self.add_warning(warning="Napalm error in open()!")
            self.add_log(type=LOG_TYPE_ERROR, action=LOG_NAPALM_ERROR_OPEN, description=f"ERROR: {self.error.details}")
            return False

        return True
