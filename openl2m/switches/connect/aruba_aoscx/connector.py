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
import pyaoscx
import pprint

from switches.connect.classes import *
from switches.connect.connector import *
from switches.connect.utils import interface_name_to_long

"""
Basic Aruba AOS-CX connector. This uses the documented REST API, and allows us to handle
any device supported by the Aruba Python "pyaoscx" library.
See more at https://github.com/aruba/pyaoscx/
and https://developer.arubanetworks.com/aruba-aoscx/docs/python-getting-started

For clarity, and to avoid namespace collisions with our own internal classes,
we import all AOS-CX classes as Aos<original-name>
"""
from pyaoscx.session import Session as AosSession
from pyaoscx.device import Device as AosDevice
from pyaoscx.vlan import Vlan as AosVlan
from pyaoscx.mac import Mac as AosMac
from pyaoscx.interface import Interface as AosInterface
from pyaoscx.poe_interface import PoEInterface as AosPoEInterface
# used to disable unknown SSL cert warnings:
import urllib3

API_VERSION = '10.04'


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
        self.name = "AOS-CX REST API Connector"
        # force READ-ONLY for now! We have not implemented changing settings.
        self.switch.read_only = False
        self.add_more_info('System', 'Type', f"AOS-CX REST Connector for '{self.switch.name}'")

        # this will be the pyaoscx driver session object
        self.aoscx_session = False
        # and we dont want to cache this:
        self.set_do_not_cache_attribute('aoscx_session')
        self.switch.read_only = False

    def get_my_basic_info(self):
        '''
        load 'basic' list of interfaces with status.
        return True on success, False on error and set self.error variables
        '''
        dprint("AosCxConnector().get_my_basic_info()")
        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        # get facts of device first, ie OS, model, etc.!
        # see https://github.com/aruba/pyaoscx/blob/master/pyaoscx/device.py
        try:
            device = AosDevice(session=self.aoscx_session)
            device.get()
        except Exception as error:
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot read device information: {format(error)}"
            dprint("  get_my_basic_info(): AosDevice.get() failed!")
            return False

        # the create call (__init__()) already calls get_firmware_version
        # firmware = device.get_firmware_version()

        # if first time for this device (or changed), update hostname
        if self.switch.hostname != device.hostname:
            self.switch.hostname = device.hostname
            self.switch.save()

        self.add_more_info('System', 'Version', device.software_version)
        self.add_more_info('System', 'Software Info',  device.software_info)
        self.add_more_info('System', 'Firmware', device.firmware_version)
        self.add_more_info('System', 'Platform', device.platform_name)
        self.add_more_info('System', 'Hostname', device.hostname)
        self.add_more_info('System', 'Domain Name', device.domain_name)
        # print(f"\nCapabilities = {device.capabilities}")
        # print(f"\nCapacities = {device.capacities}")
        # print(f"\nBoot time = {device.boot_time}")
        # print(f"\nOther Config = {device.other_config}")
        # print(f"\nMgmt Intf Status = {device.mgmt_intf_status}")

        # not sure what to get here yet:
        # device.get_subsystems()
        # for key in device.subsystems:
        #    print(f"        attribute: {key}")

        # get the VLAN info
        try:
            vlans = AosVlan.get_facts(session=self.aoscx_session)
        except Exception as error:
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot read device vlans: {format(error)}"
            dprint("  get_my_basic_info(): AosVlan.get_facts() failed!")
            return False

        for id in vlans:
            vlan = vlans[id]
            dprint(f"Vlan {id}: {vlan['name']}")
            # is this vlan enabled?
            if vlan['admin'] == 'up' and vlan['oper_state'] == 'up':
                self.add_vlan_by_id(int(id), vlan['name'])
            else:
                dprint("  VLAN is down!")

        # and get the interfaces:
        try:
            aos_interfaces = AosInterface.get_facts(session=self.aoscx_session)
        except Exception as error:
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot read device interfaces: {format(error)}"
            dprint("  get_my_basic_info(): AosInterface.get_facts() failed!")
            return False
        for if_name in aos_interfaces:
            dprint(f"Interface: {if_name}")
            aos_interface = aos_interfaces[if_name]
            # add an OpenL2M Interface() object
            iface = Interface(if_name)
            iface.name = if_name
            iface.type = IF_TYPE_ETHERNET
            iface.description = aos_interface['description']
            # this is Admin Up/Down:
            if 'admin' in aos_interface and aos_interface['admin'] == 'down':
                iface.admin_status = False
                iface.oper_status = False
            else:
                # Admin UP, but do we have link?
                iface.admin_status = True
                if 'admin_state' in aos_interface and aos_interface['admin_state'] == 'up':
                    iface.oper_status = True
                    if 'link_speed' in aos_interface:   # better be :-)
                        if not aos_interface['link_speed'] is None:
                            # iface.speed is in 1Mbps increments:
                            iface.speed = int(aos_interface['link_speed']) / 1000000
                else:
                    iface.oper_status = False
            if 'ip_mtu' in aos_interface:
                iface.mtu = aos_interface['ip_mtu']
            if 'mvrp_enable' in aos_interface:
                iface.gvrp_enabled = aos_interface['mvrp_enable']
            if 'routing' in aos_interface:
                iface.is_routed = aos_interface['routing']
            if 'type' in aos_interface:
                if aos_interface['type'] == 'vlan':
                    dprint("VLAN interface")
                    iface.type = IF_TYPE_VIRTUAL
            # find the untagged vlan:
            if 'vlan_tag' in aos_interface and not aos_interface['vlan_tag'] is None:
                for id in aos_interface['vlan_tag']:
                    # there is only 1:
                    iface.untagged_vlan = int(id)
            # see if there are vlans on the trunk:
            # vlan_mode = native-untagged
            # vlan_trunks = {'500': '/rest/v10.04/system/vlans/500', '504': '/rest/v10.04/system/vlans/504'}
            if 'vlan_trunks' in aos_interface:
                for id in aos_interface['vlan_trunks']:
                    iface.add_tagged_vlan(int(id))
            # check LACP 'stuff':
            if 'lacp' in aos_interface and aos_interface['lacp'] == 'active':
                dprint("LAG interface")
                iface.type = IF_TYPE_LAGG
                iface.lacp_type = LACP_IF_TYPE_AGGREGATOR
                # get speed
                if 'bond_status' in aos_interface:
                    dprint(f"Bond Status found: {aos_interface['bond_status']['bond_speed']}")
                    # iface.speed is in 1Mbps increments:
                    iface.speed = int(aos_interface['bond_status']['bond_speed']) / 1000000

            elif 'lacp_current' in aos_interface and aos_interface['lacp_current']:
                # lacp member interface:
                iface.lacp_type = LACP_IF_TYPE_MEMBER
                lacp_actor = int(aos_interface['lacp_status']['actor_key'])
                iface.lacp_master_index = lacp_actor
                iface.lacp_master_name = f"lag{lacp_actor}"

            if 'ip4_address' in aos_interface:
                if aos_interface['ip4_address']:
                    dprint(f"   IPv4 = {aos_interface['ip4_address']}")
                    iface.add_ip4_network(aos_interface['ip4_address'])
                    dprint(f"   IPv4(2nd) = {aos_interface['ip4_address_secondary']}")

            # check if this has PoE Capabilities
            try:
                # go get PoE info:
                aos_iface = AosInterface(session=self.aoscx_session, name=if_name)
                aos_poe = AosPoEInterface(session=self.aoscx_session, parent_interface=aos_iface)
                aos_poe.get()
                dprint(f"   +++ POE Exists for {if_name} ===")
                # there is probably a more 'global' system/device way to see if PoE capabilities exist:
                self.poe_capable = True
                self.poe_enabled = True
                # assign an OpenL2M PoePort() object
                # dprint(f"POE: config.admin_disabled={aos_poe.config['admin_disable']}")
                poe = PoePort(index=if_name, admin_status=not aos_poe.config['admin_disable'])
                # we also have poe.config['priority'] is textual values: 'low'
                iface.poe_entry = poe

                # this is a PoEInterface attribute:
                if aos_poe['_Interface__is_special_type']:
                    dprint("   SPECIAL Interface!")

            except Exception as error:
                dprint(f"   +++ NO PoE! - exception: {format(error)}")

            self.add_interface(iface)

        self._close_device()

        # the REST API gives responses in alphbetic order, eg 1/1/10 before 1/1/2.
        # sort this to the human natural order we expect:
        self.set_interfaces_natural_sort_order()

        # fix up some things that are not known at time of interface discovery,
        # such as LACP master interfaces:
        for name, iface in self.interfaces.items():
            if iface.lacp_type == LACP_IF_TYPE_MEMBER:
                lag_iface = self.get_interface_by_key(key=iface.lacp_master_name)
                if lag_iface:
                    # add the member to the aggregator interface:
                    lag_iface.lacp_members[iface.name] = iface.name
                else:
                    dprint(f"Cannot find LAG interface {iface.lacp_master_name} for {iface.name}")

        return True

    def get_my_client_data(self):
        '''
        return list of interfaces with static_egress_portlist
        return True on success, False on error and set self.error variables
        '''
        if not self._open_device():
            dprint("_open_device() failed!")
            return False
        # get mac address table
        # TBD
        #
        self._close_device()
        return False

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
            aoscx_interface = AosInterface(session=self.aoscx_session, name=interface.name)
            aoscx_interface.get()
        except Exception as error:
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot read device interface: {format(error)}"
            dprint("  set_interface_admin_status(): AosInterface.get() failed!")
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
            aoscx_interface = AosInterface(session=self.aoscx_session, name=interface.name)
            aoscx_interface.get()
        except Exception as error:
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot read device interface: {format(error)}"
            dprint("  set_interface_description(): AosInterface.get() failed!")
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
        new_state = POE_PORT_ADMIN_ENABLED or POE_PORT_ADMIN_DISABLED
        return True on success, False on error and set self.error variables
        """
        dprint(f"AosCxConnector.set_interface_poe_status() for {interface.name} to {new_state}")
        if interface.poe_entry:
            if not self._open_device():
                dprint("_open_device() failed!")
                return False
            # go get PoE info:
            try:
                aoscx_interface = AosInterface(session=self.aoscx_session, name=interface.name)
                aoscx_poe = AosPoEInterface(session=self.aoscx_session, parent_interface=aoscx_interface)
                aoscx_poe.get()
            except Exception as error:
                self.error.status = True
                self.error.description = "Error establishing connection!"
                self.error.details = f"Cannot read device interface: {format(error)}"
                dprint("  set_interface_poe_status(): AosInterface or AosPoEInterface.get() failed!")
                self._close_device()
                return False

            dprint(f"  +++ POE Exists for {ifname} ===")
            changed = aoscx_poe.set_power(state=new_state)
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
            aoscx_interface = AosInterface(session=self.aoscx_session, name=interface.name)
            aoscx_interface.get()
        except Exception as error:
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot read device interface: {format(error)}"
            dprint("  set_interface_untagged_vlan(): AosInterface.get() failed!")
            self._close_device()
            return False

        aoscx_vlan = AosVlan(session=self.aoscx_session, vlan_id=504)
        # aoscx_vlan.get()
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
        get a pyaoscx 'driver' and open a "connection" to the device
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
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            # or all warnings:
            # urllib3.disable_warnings()

        self.aoscx_session = AosSession(self.switch.primary_ip4, API_VERSION)
        try:
            dprint('Getting AOS-CX session...')
            self.aoscx_session.open(self.switch.netmiko_profile.username, self.switch.netmiko_profile.password)
            dprint("  session OK!")
        except Exception as error:
            self.error.status = True
            self.error.description = "Error establishing connection!"
            self.error.details = " Cannot open REST session: {}".format(error)
            dprint("  _open_device: AosSession.open() failed!")
            return False

        return True

    def _close_device(self):
        '''
        make sure we properly close the AOS-CX REST Session
        '''
        dprint("AOS-CX _close_device()")
        self.aoscx_session.close()
        return True
