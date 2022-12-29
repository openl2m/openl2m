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
import pyaoscx
import traceback

from switches.connect.classes import *
from switches.connect.connector import *
from switches.connect.utils import interface_name_to_long

"""
Basic Aruba AOS-CX connector. This uses the documented REST API, and allows us to handle
any device supported by the Aruba Python "pyaoscx" library.
See more at https://github.com/aruba/pyaoscx/
and https://developer.arubanetworks.com/aruba-aoscx/docs/python-getting-started

For clarity, and to avoid namespace collisions with our own internal classes,
we import all AOS-CX classes as AosCx<original-name>
"""
from pyaoscx.session import Session as AosCxSession
from pyaoscx.device import Device as AosCxDevice
from pyaoscx.vlan import Vlan as AosCxVlan
from pyaoscx.mac import Mac as AosCxMac
from pyaoscx.interface import Interface as AosCxInterface
from pyaoscx.poe_interface import PoEInterface as AosCxPoEInterface
# used to disable unknown SSL cert warnings:
import urllib3

API_VERSION = '10.08'   # '10.08' or '10.04'


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

        # this is a read-write driver:
        self.switch.read_only = False
        # this will be the pyaoscx driver session object
        self.aoscx_session = False
        # this will contain the requests.Session() object that has the actual cookies, etc.
        # once the AOS-CX Session is open...
        self.requests_session = False
        # and we dont want to cache this:
        self.set_do_not_cache_attribute('aoscx_session')

        # capabilities of current driver:
        self.can_change_admin_status = True
        self.can_change_vlan = True
        self.can_change_poe_status = True
        self.can_change_description = True
        self.can_save_config = False  # not needed.
        self.can_reload_all = False

    def get_my_basic_info(self):
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
            self.add_warning(f"Cannot read device information: {repr(error)} ({str(type(error))}) => {traceback.format_exc()}")
            return False

        # the create call (__init__()) already calls get_firmware_version
        # firmware = device.get_firmware_version()

        # if first time for this device (or changed), update hostname
        if self.switch.hostname != aoscx_device.hostname:
            self.switch.hostname = aoscx_device.hostname
            self.switch.save()

        self.add_more_info('System', 'Version', aoscx_device.software_version)
        if 'build_date' in aoscx_device.software_info:
            self.add_more_info('System', 'Software Info', f"Build date: {aoscx_device.software_info['build_date']}")
        # this is typically the same as software_version:
        # self.add_more_info('System', 'Firmware', aoscx_device.firmware_version)
        self.add_more_info('System', 'Platform', aoscx_device.platform_name)
        if aoscx_device.hostname:    # this is None when not set!
            self.add_more_info('System', 'Hostname', aoscx_device.hostname)
        else:
            self.add_more_info('System', 'Hostname', '')
        if aoscx_device.domain_name:    # this is None when not set!
            self.add_more_info('System', 'Domain Name', aoscx_device.domain_name)
        else:
            self.add_more_info('System', 'Domain Name', '')
        # print(f"\nCapabilities = {aoscx_device.capabilities}")
        # print(f"\nCapacities = {aoscx_device.capacities}")
        # print(f"\nBoot time = {aoscx_device.boot_time}")
        if aoscx_device.boot_time:
            boot_time = datetime.datetime.fromtimestamp(aoscx_device.boot_time)
            self.add_more_info('System', 'Boot Time', boot_time)
        # print(f"\nOther Config = {aoscx_device.other_config}")
        # print(f"\nMgmt Intf Status = {aoscx_device.mgmt_intf_status}")

        if 'system_contact' in aoscx_device.other_config and aoscx_device.other_config['system_contact']:
            self.add_more_info('System', 'Contact', aoscx_device.other_config['system_contact'])
        if 'system_location' in aoscx_device.other_config and aoscx_device.other_config['system_location']:
            self.add_more_info('System', 'Location', aoscx_device.other_config['system_location'])
        if 'system_contact' in aoscx_device.other_config and aoscx_device.other_config['system_description']:
            self.add_more_info('System', 'Description', aoscx_device.other_config['system_description'])

        # not sure what to get here yet:
        # aoscx_device.get_subsystems()
        # for key in device.subsystems:
        #    print(f"        attribute: {key}")

        # get the VLAN info
        try:
            aoscx_vlans = AosCxVlan.get_facts(session=self.aoscx_session)
        except Exception as error:
            self._close_device()
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot read device vlans: {format(error)}"
            dprint("  get_my_basic_info(): AosCxVlan.get_facts() failed!")
            return False

        for id in aoscx_vlans:
            vlan = aoscx_vlans[id]
            dprint(f"Vlan {id}: {vlan['name']}")
            # is this vlan enabled?
            self.add_vlan_by_id(int(id), vlan['name'])
            if not vlan['admin'] == 'up' and not vlan['oper_state'] == 'up':
                dprint("  VLAN is down!")

        # and get the interfaces:
        try:
            aoscx_interfaces = AosCxInterface.get_facts(session=self.aoscx_session)
        except Exception as error:
            self._close_device()
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot read device interfaces: {format(error)}"
            dprint("  get_my_basic_info(): AosCxInterface.get_facts() failed!")
            return False
        for if_name in aoscx_interfaces:
            dprint(f"AosCxInterface: {if_name}")
            aoscx_interface = aoscx_interfaces[if_name]
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
                    if 'link_speed' in aoscx_interface:   # better be :-)
                        if not aoscx_interface['link_speed'] is None:
                            # iface.speed is in 1Mbps increments:
                            iface.speed = int(aoscx_interface['link_speed']) / 1000000
                else:
                    iface.oper_status = False
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
            # find the untagged vlan:
            if 'vlan_tag' in aoscx_interface and not aoscx_interface['vlan_tag'] is None:
                for id in aoscx_interface['vlan_tag']:
                    # there is only 1:
                    iface.untagged_vlan = int(id)
            # see if there are vlans on the trunk:
            # vlan_mode = native-untagged
            # vlan_trunks = {'500': '/rest/v10.04/system/vlans/500', '504': '/rest/v10.04/system/vlans/504'}
            if 'vlan_trunks' in aoscx_interface:
                for id in aoscx_interface['vlan_trunks']:
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
                    iface.speed = int(aoscx_interface['bond_status']['bond_speed']) / 1000000

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
        self._close_device()

        # the REST API gives responses in alphbetic order, eg 1/1/10 before 1/1/2.
        # sort this to the human natural order we expect:
        self.set_interfaces_natural_sort_order()

        # fix up some things that are not known at time of interface discovery,
        # such as LACP master interfaces:
        self._map_lacp_members_to_logical()

        return True

    def get_my_client_data(self):
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
                v = AosCxVlan(session=self.aoscx_session, vlan_id=vlan_id)
                v.get()
                if hasattr(v, 'name'):
                    # vlan 1 does not typically have a name!
                    print(f"  VLAN {v.name}")
            except Exception as err:
                dprint(f"v = Vlan() error: {err}")
                description = f"Cannot get ethernet table for vlan {vlan_id}"
                details = f"pyaoscx Vlan() Error: {repr(err)} ({str(type(err))})\n{traceback.format_exc()}"
                self.add_warning(description)
                log = Log(group=self.group,
                          switch=self.switch,
                          ip_address=get_remote_ip(self.request),
                          type=LOG_TYPE_ERROR,
                          action=LOG_AOSCX_ERROR_GENERIC,
                          description=details)
                continue
            # this gets ethernet addresses by vlan:
            vlan_macs = AosCxMac.get_all(session=self.aoscx_session, parent_vlan=v)
            for mac in vlan_macs.values():
                mac.get()   # materialize the object from the device
                dprint(f"  MAC Address: {mac} -> {mac.port}")
                # for name in mac.__dict__:
                #    dprint(f"      attribute: {name} = {mac.__dict__[name]}")
                # add this to the known addressess:
                a = self.add_learned_ethernet_address(mac.port.name, mac.mac_address)
                # dprint("ethernet added, setting vlan!")
                if a:
                    # dprint("about to set vlan")
                    a.set_vlan(vlan_id)

        # done...
        self._close_device()
        return True

    def set_interface_admin_status(self, interface, new_state):
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
        self._close_device()
        if changed:
            dprint(f"  Interface change '{state}' OK!")
            # call the super class for bookkeeping.
            super().set_interface_admin_status(interface, new_state)
            return True
        else:
            dprint(f"   Interface change '{state}' FAILED!")
            # we need to add error info here!!!
            return False

    def set_interface_description(self, interface, description):
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
        self._close_device()
        if changed:
            dprint("   Descr OK!")
            # call the super class for bookkeeping.
            super().set_interface_description(interface, description)
            return True
        else:
            dprint("   Descr FAILED!")
            # we need to add error info here!!!
            return False

    def set_interface_poe_status(self, interface, new_state):
        """
        set the interface Power-over-Ethernet status as given
        interface = Interface() object for the requested port

        Args:
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
            self._close_device()
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

    def set_interface_untagged_vlan(self, interface, new_pvid):
        """
        set the interface untagged vlan to the given vlan
        interface = Interface() object for the requested port
        new_pvid = an integer with the requested untagged vlan
        return True on success, False on error and set self.error variables
        """
        dprint(f"AosCxConnector.set_interface_untagged_vlan() for {interface.name} to vlan {new_pvid}")
        if not self._open_device():
            dprint("_open_device() failed!")
            return False
        try:
            aoscx_interface = AosCxInterface(session=self.aoscx_session, name=interface.name)
            aoscx_interface.get()
            dprint(f"  AosCxInterface.get() OK: {aoscx_interface.name}")
        except Exception as error:
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot read device interface: {format(error)}"
            dprint("  set_interface_untagged_vlan(): AosCxInterface.get() failed!")
            self._close_device()
            return False

        dprint("  Get AosCxVlan()")
        aoscx_vlan = AosCxVlan(session=self.aoscx_session, vlan_id=new_pvid)
        # aoscx_vlan.get()
        dprint("  set_untagged_vlan()")
        changed = aoscx_interface.set_untagged_vlan(aoscx_vlan)
        # change = aoscs_vlan.apply()
        self._close_device()
        if changed:
            dprint("   Vlan Change OK!")
            # call the super class for bookkeeping.
            super().set_interface_untagged_vlan(interface, new_pvid)
            return True
        else:
            dprint("   Vlan Change FAILED!")
            # we need to add error info here!!!
            return False

    def _open_device(self):
        '''
        get a pyaoscx "driver" and open a "connection" to the device
        return True on success, False on failure, and will set self.error
        '''
        dprint("AOS-CX _open_device()")
        if not self.switch.netmiko_profile:
            self.error.status = True
            self.error.description = "Please configure a Credentials Profile to be able to connect to this device!"
            dprint("  _open_device: No Credentials!")
            return False

        # do we want to check SSL certificates ?
        if not self.switch.netmiko_profile.verify_hostkey:
            # disable unknown cert warnings
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            # or all warnings:
            # urllib3.disable_warnings()

        if self.requests_session:
            # previous cached request.Session(), so get an AosCx Session() based on that!
            dprint("Using existing requests.Session() info!")
            try:
                self.aoscx_session = AosCxSession.from_session(
                    req_session=self.requests_session,
                    base_url=f"https://{self.switch.primary_ip4}/rest/v{API_VERSION}/",
                    # credentials={
                    #    'username': self.switch.netmiko_profile.username,
                    #    'password': self.switch.netmiko_profile.password,
                    # },
                )
                dprint("  session OK!")
                return True
            except Exception as error:
                self.error.status = True
                self.error.description = "Error rebuilding connection from session!"
                self.error.details = f"Cannot recreate REST session with AosCxSession.from_session(): {format(error)}"
                dprint(f"  _open_device: AosCxSession.from_session() failed: {format(error)}")
                return False
        else:
            # first connection", we need to authenticate:
            try:
                dprint(f"Creating AosCxSession(ip_address={self.switch.primary_ip4}, api={API_VERSION})")
                self.aoscx_session = AosCxSession(ip_address=self.switch.primary_ip4, api=API_VERSION)
                dprint(f"Calling session.open(username={self.switch.netmiko_profile.username}, password={self.switch.netmiko_profile.password})")
                self.aoscx_session.open(username=self.switch.netmiko_profile.username, password=self.switch.netmiko_profile.password)
                dprint("  session OK!")
                # save the requests.Session() with cookies, etc.
                # DISABLED FOR NOW:
                # self.requests_session = self.aoscx_session.s
                return True
            except Exception as error:
                self.error.status = True
                self.error.description = "Error establishing connection!"
                self.error.details = f"Cannot open REST session: {format(error)}"
                dprint(f"  _open_device: AosCxSession.open() failed: {format(error)}")
                return False

    def _close_device(self):
        '''
        make sure we properly close the AOS-CX REST Session
        '''
        dprint("AOS-CX _close_device()")
        self.aoscx_session.close()
        self.aoscx_session = False
        return True
