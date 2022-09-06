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
from netaddr import *
import pprint
import re
import traceback

from switches.utils import dprint
from switches.connect.constants import *
from switches.connect.classes import *
from switches.connect.connector import *
from switches.connect.junos_pyez.utils import *

'''
Basic Junos PyEZ connector. This uses the documented PyEZ library, which uses Netconf underneath.
https://www.juniper.net/documentation/us/en/software/junos-pyez/junos-pyez-developer/index.html
'''
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import *


class PyEZConnector(Connector):
    '''
    This class implements a Connector() to get switch information from Junos devices supported by the PyEz library.
    '''
    def __init__(self, request=False, group=False, switch=False):
        '''
        Initialize the PyEZ Connector() object

        Args:
            request: Django http request object
            group:  Group() object for switch membership
            switch: Switch() object that is the device.

        Returns:
            none
        '''
        dprint("PyEZConnector() __init__")
        super().__init__(request, group, switch)
        self.description = 'Junos PyEZ Netconf driver'
        self.switch.read_only = False

        # current capabilities of the PyEZ drivers:
        self.can_change_admin_status = True
        self.can_change_vlan = True
        self.can_change_poe_status = True
        self.can_change_description = True
        self.can_save_config = False    # save not needed after commit in Junos!
        self.can_reload_all = True      # if true, we can reload all our data (and show a button on screen for this)

        # this will be the pyJunosPyEZ driver session object
        self.device = False
        # and we dont want to cache this:
        self.set_do_not_cache_attribute('device')

    def get_my_basic_info(self):
        '''
        load 'basic' list of interfaces with status.

        Args:
            none

        Returns:
            True on success, False on error and set self.error variables
        '''
        dprint("PyEZConnector().get_my_basic_info()")
        if not self._open_device():
            dprint("  _open_device() failed!")
            self.add_warning("Error connecting to device!")
            # self.error already set!
            return False

        # if first time for this device (or changed), update hostname
        if self.switch.hostname != self.device.facts['hostname']:
            self.switch.hostname = self.device.facts['hostname']
            self.switch.save()

        self.add_more_info('System', 'Hostname', self.device.facts['hostname'])
        self.add_more_info('System', 'Model', self.device.facts['model'])
        self.add_more_info('System', 'Version', self.device.facts['version'])
        if self.device.facts['domain']:  # this is None when not set!
            self.add_more_info('System', 'Domain Name', self.device.facts['domain'])
        else:
            self.add_more_info('System', 'Domain Name', '')
        self.add_more_info('System', 'Uptime', self.device.facts['RE0']['up_time'])
        self.add_more_info('System', 'Personality', self.device.facts['personality'])

        # now we use rpc calls for interfaces, PoE, etc.

        # first get interface information:
        dprint("INTERFACES:")
        '''
        This RPC is cli equivalent of "show interfaces extensive"
        '''
        intf_data = self.device.rpc.get_interface_information(extensive=False)
        interfaces = intf_data.findall('.//physical-interface')
        for intf in interfaces:
            name = intf.find('.//name').text
            dprint(f"\n  Name: {name}")
            # create new OpenL2M Interface() object
            iface = Interface(name)
            iface.name = name

            # try several fields to figure out what kind of interface this is:
            try:
                type = intf.find('.//link-level-type').text
                dprint(f"  link-level-type = {type}")
                iface.type = junos_parse_if_type(type)
            except Exception as error:
                try:
                    if_type = intf.find('.//if-type').text
                    dprint(f"  if-type = {if_type}")
                    iface.type = junos_parse_if_type(if_type)
                except Exception as error:
                    # leave at default!
                    dprint("  unknown port type!")

            try:
                description = intf.find('.//description').text
            except Exception as error:
                description = ''
            iface.description = description

            admin_status = intf.find('.//admin-status').text
            if admin_status == 'up':
                iface.admin_status = True

            oper_status = intf.find('.//oper-status').text
            if oper_status == 'up':
                iface.oper_status = True

            try:
                mtu = intf.find('.//mtu').text
            except Exception as error:
                mtu = 0
            try:
                iface.mtu = int(mtu)
            except Exception as error:
                iface.mtu = 0

            try:
                speed = intf.find('.//speed').text
            except Exception as error:
                speed = '0'     # make sure this is a string object!
            iface.speed = junos_speed_to_mbps(speed)

            # look at all Address Families:
            families = intf.findall('.//address-family')
            for af in families:
                af_name = af.find('.//address-family-name').text
                dprint(f"  AF Name: {af_name}")
                if af_name == 'eth-switch':
                    dprint("  type = switch port")
                    iface.type = IF_TYPE_ETHERNET
                elif af_name == 'inet':  # IPv4 interface
                    dprint("  type = inet v4 routed interface!")
                    iface.is_routed = True
                    # some inet interfaces do NOT have ip address fields:
                    try:
                        ip4_address = af.find('.//ifa-local').text
                        if ip4_address:   # this has an IPv4 address:
                            dprint(f"  IPv4 ADDR = {ip4_address}")
                            ip4_net = af.find('.//ifa-destination').text
                            try:
                                dprint(f"  IPv4 NET = {ip4_net}")
                                net = IPNetwork(ip4_net)
                                prefixlen = net.prefixlen
                            except Exception as error:
                                # not found, so lets assume a /32
                                prefixlen = 32
                            iface.add_ip4_network(ip4_address, prefix_len=prefixlen)
                    except Exception as error:
                        dprint(f"  NO ipv4 address found! Error={error}")
                elif af_name == 'inet6':
                    dprint("  type = inet v6 routed interface!")
                    iface.is_routed = True
                    # some do not have ipv6 address:
                    try:
                        ip6_address = af.find('.//ifa-local').text
                        if ip6_address:   # this has an IPv4 address:
                            dprint(f"  IPv6 ADDR = {ip6_address}")
                            try:
                                ip6_net = af.find('.//ifa-destination').text
                                dprint(f"  IPv6 NET = {ip6_net}")
                                net6 = IPNetwork(ip6_net)
                                prefixlen = net6.prefixlen
                            except Exception as error:
                                # not found, let's assume /128
                                prefixlen = 128
                            iface.add_ip6_network(ip6_address, prefix_len=prefixlen)
                    except Exception as error:
                        dprint(f"  NO ipv6 address found! Error={error}")
                elif af_name == 'aenet':
                    # aggregated ethernet!
                    ae_interface = af.find('.//ae-bundle-name').text
                    dprint(f" Aggregate Member of {ae_interface}!")
                    iface.lacp_type = LACP_IF_TYPE_MEMBER
                    iface.lacp_master_name = junos_remove_unit(ae_interface)
                    iface.lacp_master_index = 1     # anything > 0 is fine.
                    # and add as member to the master interface:

            try:
                min_ag = intf.find('.//minimum-links-in-aggregate').text
                iface.type = IF_TYPE_LAGG
            except Exception as error:
                dprint("  not an aggregate.")
            dprint(f"  Final type = {iface.type}")
            self.add_interface(iface)

        # fix up some things that are not known at time of interface discovery,
        # such as LACP master interfaces:
        self._map_lacp_members_to_logical()

        # Now get PoE power supply info:
        try:
            '''
            This RPC is cli equivalent of "show poe controller"
            '''
            ps_data = self.device.rpc.get_poe_controller_information()
            # check that there is PoE info:
            controllers = ps_data.findall('.//controller-information')
            if controllers:
                dprint("POE Supplie(s) found:")
                for controller in controllers:
                    self._parse_powersupply(controller)

                # and get PoE Interface info:
                try:
                    '''
                    This RPC is cli equivalent of "show poe interface"
                    '''
                    poe_data = self.device.rpc.get_poe_interface_information()
                except Exception as error:
                    dprint(f"dev.rpc.get_poe_interface_information() error: {error}")
                    self.add_warning(f"ERROR: Cannot get interface PoE info - {error}")

                # find all poe interfaces:
                dprint("POE Interfaces found:")
                interfaces = poe_data.findall('.//interface-information')
                for interface in interfaces:
                    self._parse_poe_interface(interface)

        except Exception as error:
            print(f"dev.rpc.get_poe_controller_information() error: {error}")
            self.add_warning(f"ERROR: Cannot get PoE supply info - {error}")

        # get vlan info. this includes port membership!
        dprint("\nVLANS:")
        try:
            '''
            This RPC is cli equivalent of "show vlans extensive"
            '''
            vlan_response = self.device.rpc.get_vlan_information(extensive=True)
            vlans = vlan_response.findall('.//l2ng-l2ald-vlan-instance-group')
            for v in vlans:
                name = v.find('.//l2ng-l2rtb-vlan-name').text
                id = v.find('.//l2ng-l2rtb-vlan-tag').text
                self.add_vlan_by_id(int(id), name)
                # and parse the interfaces on this vlan:
                members = v.findall('.//l2ng-l2rtb-vlan-member')
                for member in members:
                    if_name = member.find('.//l2ng-l2rtb-vlan-member-interface').text
                    phys_if_name = junos_remove_unit(if_name)
                    tagness = member.find('.//l2ng-l2rtb-vlan-member-tagness').text
                    try:
                        mode = member.find('.//l2ng-l2rtb-vlan-member-interface-mode').text
                    except Exception as err:
                        mode = ''
                    dprint(f"Vlan {id}-{name} member {phys_if_name} {tagness} {mode}")
                    iface = self.get_interface_by_key(phys_if_name)
                    if iface:
                        if tagness == 'tagged':
                            iface.add_tagged_vlan(int(id))
                        else:
                            iface.untagged_vlan = int(id)
                        if mode == 'trunk':
                            iface.is_tagged = True

        except Exception as error:
            dprint(f"dev.rpc.get_vlan_information() error: {error}")
            self.add_warning(f"ERROR: Cannot get vlans - {error}")

        # done with PyEZ connection:
        self._close_device()

        return True

    def get_my_client_data(self):
        '''
        read mac addressess, and lldp neigbor info.

        Args:
            none
        Return:
            True on success, False on error and set self.error variables
        '''
        dprint("PyEZConnector().get_my_client_data()")
        if not self._open_device():
            dprint("_open_device() failed!")
            self.add_warning("Erroring connecting to device!")
            return False
        # get mac address table
        # TBD
        #
        dprint("\nMAC ADDRESSESS:")
        '''
        This RPC is cli equivalent of "show ethernet-switching table extensive"
        '''
        mac_data = self.device.rpc.get_ethernet_switching_table_information(extensive=True)
        macs = mac_data.findall('.//l2ng-l2ald-mac-entry-vlan')
        for mac in macs:
            mac_address = mac.find('.//l2ng-l2-mac-address').text
            vlan_id = int(mac.find('.//l2ng-l2-vlan-id').text)
            if_name = mac.find('.//l2ng-l2-mac-logical-interface').text
            phys_if_name = junos_remove_unit(if_name)
            dprint(f"  Found: {mac_address}, on vlan {vlan_id}, interface {phys_if_name}")
            self.add_learned_ethernet_address(if_name=phys_if_name, eth_address=mac_address, vlan_id=vlan_id)

        dprint("\nARP:")
        '''
        This RPC is cli equivalent of "show arp no-resolve"
        '''
        arp_data = self.device.rpc.get_arp_table_information(no_resolve=True)
        arp_entries = arp_data.findall('.//arp-table-entry')
        # compile the IRB matching reg-ex for performance:
        irb_regex = re.compile(r"^irb\.\d+\s+\[([\w\-\.\/]+)\]$")
        for arp in arp_entries:
            mac_address = arp.find('.//mac-address').text
            ip_address = arp.find('.//ip-address').text
            if_name = arp.find('.//interface-name').text
            dprint(f"  {mac_address} = {ip_address}, on {if_name}")
            # if found on routed interface, if_name could be formed as "irb.nnn [if_name]"
            m = re.match(irb_regex, if_name)
            if m:
                if_name = junos_remove_unit(m.group(1))
                dprint(f"     Matched IRB, real interface = {if_name}")
            else:
                # maybe this is a 'regular' interface with unit:
                if_name = junos_remove_unit(if_name)
            dprint(f"   Final real interface: {if_name}")
            self.add_learned_ethernet_address(if_name=if_name, eth_address=mac_address, ip4_address=ip_address)

        dprint("\nLLDP:")
        '''
        Most details come from the RPC call to
            get_lldp_interface_neighbors(interface_device=<name>)
        This RPC is cli equivalent of "show lldp neigbor interface <name>"
        So we are going to loop through all interfaces:
        '''
        for iface in self.interfaces.values():
            dprint(f"  Interface:{iface.name}")
            try:
                '''
                This RPC is cli equivalent of "show lldp neigbor interface <interface-name>"
                '''
                lldp_data = self.device.rpc.get_lldp_interface_neighbors(interface_device=iface.name)
                neighbors = lldp_data.findall('.//lldp-neighbor-information')
                for nb in neighbors:
                    dprint("    Found neighbor:")
                    # we know this already, since we are running lldp neigbor on <iface.name> :
                    # local_port = nb.find('.//lldp-local-interface').text
                    remote_chassis_id_subtype = nb.find('.//lldp-remote-chassis-id-subtype').text
                    remote_chassis_id = nb.find('.//lldp-remote-chassis-id').text
                    # remote_description = nb.find('.//lldp-remote-port-description').text
                    sys_name = nb.find('.//lldp-remote-system-name').text
                    sys_description = nb.find('.//lldp-remote-system-description').text
                    capabilities = nb.find('.//lldp-remote-system-capabilities-enabled').text
                    dprint(f"    Neighbor: {sys_name}")
                    neighbor = NeighborDevice(remote_chassis_id)
                    neighbor.set_sys_name(sys_name)
                    neighbor.set_sys_description(sys_description)
                    # neighbor.set_port_name()
                    # neighbor.set_port_description()
                    neighbor.set_chassis_string(remote_chassis_id)
                    if remote_chassis_id_subtype == 'Mac address':
                        neighbor.set_chassis_type(LLDP_CHASSIC_TYPE_ETH_ADDR)
                    # parse capabilities:
                    if 'Bridge' in capabilities:
                        neighbor.set_capability(LLDP_CAPABILITIES_BRIDGE)
                    if 'Router' in capabilities:
                        neighbor.set_capability(LLDP_CAPABILITIES_ROUTER)
                    # Following NOT tested; we are assuming the following two are correct:
                    if 'Wlan' in capabilities:
                        neighbor.set_capability(LLDP_CAPABILITIES_WLAN)
                    if 'Phone' in capabilities:
                        neighbor.set_capability(LLDP_CAPABILITIES_PHONE)
                    self.add_neighbor_object(iface.name, neighbor)
            except Exception as err:
                # not all interfaces can show lldp neighbor!
                dprint(f"RPC call failed for '{iface.name}': {err}")

        self._close_device()
        return True

    def _parse_powersupply(self, supply):
        '''
        Parse out XML data with power suply information, and update
        device inforation.

        Args:
            supply: the XML entity with the power supply 'controller' information.

        Returns:
            none
        '''
        id = supply.find('.//controller-number').text
        dprint(f"Power Supply id {id}")
        max_power = junos_parse_power(supply.find('.//controller-maxpower').text)
        dprint(f"  max {max_power} Watts")
        pse = self.add_poe_powersupply(id, max_power)
        # set additional data:
        consumed_power = junos_parse_power(supply.find('.//controller-power').text)
        dprint(f"  used {consumed_power} Watts")
        pse.set_consumed_power(consumed_power)
        return

    def _parse_poe_interface(self, intf):
        '''
        Parse the data for a PoE interface into the Interface() object.

        Args:
            intf: the XML entity for the PoE interface

        Returns:
            none
        '''
        name = intf.find('.//interface-name').text
        dprint(f"  {name}")
        iface = self.get_interface_by_key(name)
        available = junos_parse_power(intf.find('.//interface-power-limit').text, milliwatts=True)
        dprint(f"    available: {available} mW")
        # call base class for bookkeeping.
        super().set_interface_poe_available(iface, available)
        if intf.find('.//interface-status').text == 'Disabled':
            dprint("    Admin Disabled!")
            # call base class for bookkeeping.
            super().set_interface_poe_status(iface, POE_PORT_ADMIN_DISABLED)
        else:
            # PoE is admin UP, call base class for bookkeeping.
            super().set_interface_poe_status(iface, POE_PORT_ADMIN_ENABLED)
            if intf.find('.//interface-status').text == 'OFF':
                # enabled, but no power used:
                dprint("  Up but Off (Searching)!")
                # call base class for bookkeeping.
                super().set_interface_poe_detect_status(iface, POE_PORT_DETECT_SEARCHING)
            else:   # elif intf['interface-status'] == 'OFF':
                consumed = junos_parse_power(intf.find('.//interface-power').text, milliwatts=True)
                dprint(f" consumed: {consumed} mW")
                # call base class for bookkeeping.
                super().set_interface_poe_consumed(iface, consumed)

    def set_interface_admin_status(self, interface, new_state):
        '''
        Set the interface to the requested state (up or down)

        Args:
            interface: the Interface() object for the requested port
            new_state (boolean): new state, True = enabled, False = disabled

        Returns:
            (boolean) True on success, False on error and set self.error variables
        '''
        dprint(f"PyEZCOnnector.set_interface_admin_status() for {interface.name} to {bool(new_state)}")
        if not self._open_device():
            dprint("_open_device() failed!")
            return False
        commands = []
        if new_state:
            commands.append(f"delete interfaces {interface.name} disable")
        else:
            commands.append(f"set interfaces {interface.name} disable")
        if self.execute_commands(commands=commands):
            # now do the bookkeeping:
            super().set_interface_admin_status(interface=interface, new_state=new_state)
            self._close_device()
            dprint("  change OK!")
            return True
        self._close_device()
        dprint("  change FAILED!")
        return False

    def set_interface_poe_status(self, interface, new_state):
        '''
        Set the interface Power-over-Ethernet status to the requested state (up or down)

        Args:
            interface = the Interface() object for the requested port
            new_state (int): POE_PORT_ADMIN_ENABLED or POE_PORT_ADMIN_DISABLED

        Returns:
            (boolean) True on success, False on error and set self.error variables
        '''
        dprint(f"PyEZCOnnector.set_interface_poe_status() for {interface.name} to {new_state}")
        if not self._open_device():
            dprint("_open_device() failed!")
            return False
        commands = []
        if new_state == POE_PORT_ADMIN_ENABLED:   # "on"
            commands.append(f"delete poe interface {interface.name} disable")
        else:   # "off"
            commands.append(f"set poe interface {interface.name} disable")
        if self.execute_commands(commands=commands):
            # call the super class for bookkeeping.
            super().set_interface_poe_status(interface, new_state)
            self._close_device()
            dprint("  change OK!")
            return True
        self._close_device()
        dprint("  change FAILED!")
        return False

    def set_interface_untagged_vlan(self, interface, new_pvid):
        '''
        Set the interface untagged vlan to the given vlan

        Args:
            interface: the Interface() object for the requested port
            new_pvid(int): the requested untagged vlan

        Returns:
            (boolean) True on success, False on error and set self.error variables
        '''
        dprint(f"PyEZCOnnector.set_interface_untagged_vlan() for {interface.name} to vlan {new_pvid}")
        if not self._open_device():
            dprint("_open_device() failed!")
            return False
        commands = []
        if interface.is_tagged:     # "vlan trunk"
            commands.append(f"set interfaces {interface.name} native-vlan-id {new_pvid}")
        else:   # "plain untagged"
            # need vlan by name, not number!
            vlan = self.get_vlan_by_id(new_pvid)
            if not vlan:
                # cannot find pvid vlan (should not happen!)
                self.error.status = True
                self.error.description = f"Unknown vlan {new_pvid}"
                return False
            commands.append(f"delete interfaces {interface.name} unit 0 family ethernet-switching vlan")
            commands.append(f"set interfaces {interface.name} unit 0 family ethernet-switching vlan members {vlan.name}")
        if self.execute_commands(commands=commands):
            # call the super class for bookkeeping.
            super().set_interface_untagged_vlan(interface=interface, new_pvid=new_pvid)
            self._close_device()
            dprint("  change OK!")
            return True
        self._close_device()
        dprint("  change FAILED!")
        return False

    def set_interface_description(self, interface, description):
        '''
        Set the interface description (aka. description) to the string

        Args:
            interface = Interface() object for the requested port
            new_description = a string with the requested text

        Returns:
            (boolean) True on success, False on error and set self.error variables
        '''
        dprint(f"PyEZCOnnector.set_interface_description() for {interface.name} to '{description}'")
        if not self._open_device():
            dprint("_open_device() failed!")
            return False
        commands = []
        if description:
            commands.append(f'set interfaces {interface.name} description "{description}"')
        else:   # "off"
            commands.append(f"delete interfaces {interface.name} description")
        if self.execute_commands(commands=commands):
            # call the super class for bookkeeping.
            super().set_interface_description(interface=interface, description=description)
            self._close_device()
            dprint("  change OK!")
            return True
        self._close_device()
        dprint("  change FAILED!")
        return False

    def execute_commands(self, commands, format='set'):
        '''
        Execute a list of command string(s) on the device. Defaults to 'set' format.

        Args:
            commands(list): the command list of strings to execute.
            format(str): the command format, default = 'set'

        Returns:
            (boolean) True on success, False on error and set self.error variables
        '''
        dprint(f"PyEZ.execute_commands(): format={format}, '{commands}'")
        try:
            conf = Config(self.device)  # we assume this is open!
            conf.lock()
            for command in commands:
                conf.load(command, format=format)
            dprint(f"Config Diff: {conf.diff()}")
            if conf.commit_check():
                dprint("commit_check() OK")
                conf.commit()
                ret_val = True
            else:
                dprint("commit_check() FAILED!")
                conf.rollback()
                self.error.status = True
                self.error.description = "Commit-Check failed! Not executing command."
                self.error.details = ''
                ret_val = False
            conf.unlock()
            return ret_val
        except RpcError as err:
            self.error.status = True
            self.error.description = "Network Communications Error, change was NOT applied!"
            self.error.details = f"Error: '{err}', commands '{commands}'"
            return False
        except ConfigLoadError as err:
            self.error.status = True
            self.error.description = "Error loading config, change was NOT applied!"
            self.error.details = f"Error: '{err}', commands '{commands}'"
            return False
        except CommitError as err:
            self.error.status = True
            self.error.description = "Commit-Check failed, change was NOT applied!"
            self.error.details = f"Error: '{err}', commands '{commands}'"
            return False
        except LockError as err:
            self.error.status = True
            self.error.description = "Cannot get lock, change was NOT applied!"
            self.error.details = f"Error: '{err}', commands '{commands}'"
            return False
        except UnlockError:
            self.error.status = True
            self.error.description = "Cannot release lock, but change was applied!"
            self.error.details = f"Error: '{err}', commands '{commands}'"
            return False
        except ValueError as err:
            self.error.status = True
            self.error.description = "Invalid Rollback ID, change was NOT applied!"
            self.error.details = f"Error: '{err}', commands '{commands}'"
            return False
        except Exception as err:
            self.error.status = True
            self.error.description = "Unknown error occured, change was NOT applied!"
            self.error.details = f"Error: '{err}', command was '{commands}'"
            return False

    def _open_device(self):
        '''
        get a pyJunosPyEZ "driver" and open a "connection" to the device
        return True on success, False on failure, and will set self.error
        '''
        dprint("Junos PyEZ _open_device()")
        if self.device:
            dprint("   Already open!")
            return True

        if not self.switch.netmiko_profile:
            self.error.status = True
            self.error.description = "Please configure a Credentials Profile to be able to connect to this device!"
            dprint("  _open_device: No Credentials!")
            return False

        self.device = Device(host=self.switch.primary_ip4,
                             user=self.switch.netmiko_profile.username,
                             password=self.switch.netmiko_profile.password,
                             normalize=True)    # normalize removed trailing/ending \n and spaces.
        try:
            self.device.open()
        except Exception as error:
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot open Junos PyEZ NetConf session: {format(error)}"
            dprint("  _open_device: Device.open() failed!")
            return False

        return True

    def _close_device(self):
        '''
        make sure we properly close the Junos PyEZ Session
        '''
        dprint("Junos PyEZ _close_device()")
        self.device.close()
        self.device = False
        return True
