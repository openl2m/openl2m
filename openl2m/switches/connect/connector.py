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
from collections import OrderedDict
import datetime
import jsonpickle
import lib.manuf.manuf as manuf
import natsort
import netmiko
import re
import time
import traceback
from typing import Any, Dict, List

from django.conf import settings
from django.http.request import HttpRequest

from switches.models import Switch, SwitchGroup, Command, Log
from switches.connect.constants import LLDP_CHASSIC_TYPE_ETH_ADDR
from switches.constants import LOG_TYPE_WARNING, LOG_CONNECTION_ERROR, LOG_TYPE_ERROR, CMD_TYPE_INTERFACE
from switches.utils import dprint, get_remote_ip, get_ip_dns_name
from switches.connect.classes import (
    Error,
    PoePort,
    PoePSE,
    Vlan,
    VendorData,
    Interface,
    EthernetAddress,
    NeighborDevice,
    Vrf,
    StackMember,
    SyslogMsg,
)
from switches.connect.constants import (
    POE_PORT_ADMIN_DISABLED,
    POE_PORT_ADMIN_ENABLED,
    POE_PORT_DETECT_DELIVERING,
    VLAN_TYPE_NORMAL,
    IANA_TYPE_IPV4,
    IANA_TYPE_IPV6,
    IF_TYPE_ETHERNET,
    LACP_IF_TYPE_MEMBER,
    LLDP_CHASSIC_TYPE_NET_ADDR,
    visible_interfaces,
)

# from django.contrib.auth.models import User

from rest_framework.reverse import reverse as rest_reverse

'''
Base Connector() class for OpenL2M.
This implements the interface that is expected by the higher level code
that calls this (e.g in the view.py functions that implement the url handling)
'''


class Connector:
    '''
    This base class defines the basic interface for all switch connections.
    This implements the interface that is expected by the higher level code
    that calls this (e.g in the view.py functions that implement the url handling)
    '''

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        '''
        Initialized the connector class.

        Args:
            request (http_request): the Django request object.
            switch (Switch): the switch object to connect to.
            group (Group): the group this switch belongs to.

        Returns:
            Connector() object with a valid connection.
        '''
        dprint("Connector() __init__")

        self.description = "The base Connector() that drivers should inherit from."

        self.request = request  # if running on web server, Django http request object, needed for request.user() and request.session[]
        self.group = group  # Django SwitchGroup object
        self.switch = switch  # Django Switch()
        self.error = Error()
        self.error.status = False  # we don't actually have an error yet :-)

        # caching related. All attributes but these will be cached:
        self._do_not_cache = [
            "_do_not_cache",
            "request",
            "group",
            "switch",
            "error",
            "eth_addr_count",
            "neighbor_count",
        ]

        self.hostname = ""  # system hostname, typically set in sub-class
        self.vendor_name = ""  # typically set in sub-classes

        self.show_interfaces = True  # If False, do NOT show interfaces, vlans etc... for command-only devices.
        # data we collect and potentially cache:
        self.interfaces: Dict[str, Interface] = (
            {}
        )  # Interface() objects representing the ports on this switch, key is if_name *as string!*
        self.vlans: Dict[int, Vlan] = {}  # Vlan() objects on this switch, key is vlan id *as integer!* (not index!)
        self.vlan_count = 0  # number of vlans defined on device
        self.vrfs: Dict[str, Vrf] = {}  # VRFs available on this device.
        self.ip4_to_if_index: Dict[str, int] = (
            {}
        )  # the IPv4 addresses as keys, with stored value if_index; needed to map netmask to interface
        # some flags:
        self.cache_loaded = False  # if True, system data was loaded from cache
        # some timestamps:
        self.basic_info_read_timestamp = 0  # when the last 'basic' read occured

        # data we calculate or collect without caching:
        self.allowed_vlans: Dict[int, Vlan] = (
            {}
        )  # list of vlans (stored as Vlan() objects) allowed on the switch, the join of switch and group Vlans
        self.eth_addr_count = 0  # number of known mac/ethernet addresses
        self.neighbor_count = 0  # number of lldp neighbors
        self.warnings: List[str] = []  # list of warning strings that may be shown to users
        # timing related attributes:
        self.timing = {}  # dictionary to track how long various calls take to read. Key = name, value = tuple()
        self.add_timing("Total", 0, 0)  # initialize the 'total' count to 0 entries, 0 seconds!

        # PoE related values
        self.poe_capable = False  # can the switch deliver PoE
        self.poe_enabled = False  # note: this needs more work, as we do not parse "units"/stack members
        self.poe_max_power = 0  # maximum power (watts) availabe in this switch, combines all PSE units
        self.poe_power_consumed = 0  # same for power consumed, across all PSE units
        self.poe_pse_devices: Dict[int, PoePSE] = {}  # dictionary of PoePSE() objects, key is PSE id.

        # features that may or may not be implemented:
        self.gvrp_enabled = False
        # set this flag is a save aka. 'write mem' is needed:
        self.save_needed = False

        # Netmiko is used for SSH connections to run commands. Here are some defaults a class can set.
        #
        # device_type:
        # if set, will be a value that will override (ie. hardcode) values from the
        # "Credentials Profile" (aka the NetmikoProfile() object)
        self.netmiko_device_type = ""
        # if netmiko_device_type is not set, the netmiko_valid_device_types is a  list()
        # with the valid device_type choices a driver should allow in the
        # "Credentials Profile". Any other value will trigger an error, and fail the SSH connection.
        self.netmiko_valid_device_types = []
        # the command that should be sent to disable screen paging
        # this allows us to override the default built-in command set by the Netmiko() driver class,
        # where each driver __init__() set the proper value.
        # eg.  https://github.com/ktbyers/netmiko/blob/develop/netmiko/hp/hp_comware.py )
        # this is typically not needed.
        self.netmiko_disable_paging_command = ""
        # some netmiko devices, when executing commands with send_command(), have problems with prompt parsing.
        # setting this to True disables prompt checking, and uses send_command_timing() calls.
        self.netmiko_ignore_prompt = False
        # variable to deal with the SSH connection:
        self.netmiko_connection = False  # return from Netmiko.ConnectHandler()
        # self.netmiko_timeout = settings.SSH_TIMEOUT  # should be SSH timeout/retry values
        # self.netmiko_retries = settings.SSH_RETRIES
        self.netmiko_output = ""  # any output from a netmiko/ssh command executed.

        # physical device related:
        self.vendor_data: Dict[str, Any] = {}  # dictionary to keep vendor-specific data
        self.hardware_details_needed = True  # True if we still need to read more hardware info (eg. the Entity tables)
        self.stack_members: Dict[int, StackMember] = (
            {}
        )  # StackMember() objects that are part of this switch, key is member id
        # syslog related info, if supported:
        self.syslog_msgs: Dict[int, SyslogMsg] = {}  # list of Syslog messages, if any
        self.syslog_max_msgs = 0  # how many syslog msgs device will store
        # generic info for the "Switch Information" tab:
        self.more_info: Dict[str, tuple] = (
            {}
        )  # dict of categories string, each a list of tuples (name, value), to extend sytem info about this switch!

        # save switch previous (last) access, since this will be overwritten by this access!
        self.last_accessed = self.switch.last_accessed

        # when we create a connection to close a session, there is no group object. So test for it!
        self.read_only = (
            self.switch.read_only
            or (self.group and self.group.read_only)
            or (self.request and self.request.user and self.request.user.profile.read_only)
        )

        # capabilities of the vendor or tech-specific driver, we assume No for all changing:
        self.can_change_admin_status = False
        self.can_change_vlan = False
        self.can_edit_vlans = False  # if true, this driver can edit (create/delete) vlans on the device!
        self.can_set_vlan_name = True  # set to False if vlan create/delete cannot set/change vlan name!
        self.can_change_poe_status = False
        self.can_change_description = False
        self.can_save_config = False  # do we have the ability (or need) to execute a 'save config' or 'write memory' ?
        self.can_reload_all = False  # if true, we can reload all our data (and show a button on screen for this)
        self.can_get_client_data = hasattr(self, 'get_my_client_data')  # do we implement reading arp/lldp/etc?

    def as_dict(self) -> dict:
        '''
        return this class as a dictionary for use by the API
        '''
        data = {
            'hostname': self.hostname,
            'vendor': self.vendor_name,
            'driver': self.__class__.__name__,
            'name': self.switch.name,
            'id': self.switch.id,
            'group': self.group.name,
            'group_id': self.group.id,
            "read_only": self.read_only,
            "primary_ipv4": self.switch.primary_ip4,
            "change_admin_status": self.can_change_admin_status,
            "change_vlan": self.can_change_vlan,
            "change_poe": self.can_change_poe_status,
            "change_description": self.can_change_description,
            "edit_vlans": self.can_edit_vlans,
            "change_vlan_name": self.can_set_vlan_name,
            "url": rest_reverse(
                "switches-api:api_switch_view",
                request=self.request,
                kwargs={"group_id": self.group.id, "switch_id": self.switch.id},
            ),
            # more to add later...
        }
        if self.switch.nms_id:
            data["nms_id"] = self.switch.nms_id
        else:
            data["nms_id"] = ""
        data["save_config"] = self.can_save_config

        # add VRF info
        if self.vrfs:
            vrfs = []
            for v in self.vrfs:
                vrfs.append(v.as_dict())
            data['vrfs'] = vrfs

        # add PoE data:
        if self.poe_capable:
            poe = {
                'enabled': self.poe_enabled,
                'max_power': self.poe_max_power,
                'power_consumed': self.poe_power_consumed,
            }
            supplies = []
            for pse in self.poe_pse_devices.values():
                supplies.append(pse.as_dict())
            poe['power-supplies'] = supplies
            data['poe'] = poe
        else:
            data['poe'] = False

        # this data represents the info about the connected device
        return data

    def vlans_as_dict(self) -> dict:
        '''
        return the vlans as a dictionary for use by the API
        '''
        # add vlan data:
        vlans = {}
        for v in self.vlans.values():
            vlans[v.id] = v.as_dict()
            # can this user access this vlan?
            if v.id in self.allowed_vlans:
                vlans[v.id]['allowed'] = True
            else:
                vlans[v.id]['allowed'] = False
        return vlans

    def _close_device(self) -> bool:
        """_close_device() is called to clean-up any session, REST credentials,etc when done with this device.
        This is called when changing device or logging out of the application.

        This needs to be implemented in each driver that cached sessions (cookies, etc.) and need to destroy
        that data when completely done with the device. See e.g. aruba_aoscx/connector.py

        Note: we cannot use the deconstructor __del__(), since that is called at the end of each use
        (ie when a web page has finished loading!)

        Args:
            none

        Returns:
            (boolean) True.
        """
        return True

    '''
    These are the high level functions used to "get" interface information.
    These are called by the switches.view functions to display data.
    '''

    def get_basic_info(self) -> bool:
        '''
        This is called from view.py to load the basic set of information about the switch.
        We call an device implementation specific function "get_my_basic_info()"
        that should load the following class attributes:
        self.interfaces = {} dictionary of interfaces (ports) on the current
        switch, i.e. Interface() objects, indexed by a class-specific key (string).

        self.vlans = {} dictionary of vlans on the current switch, i.e. Vlan()
        objects, indexed by vlan id (integer number)

        Args:
            none

        Returns:
            return True on success, False on error and set self.error variables
        '''
        self.error.clear()
        dprint("Connector.get_basic_info()")

        # including when this may have been read before it got cached:
        if not self.cache_loaded:
            dprint("  => Cache did NOT load!")
            # add some info about the device:
            self.add_more_info('System', 'Group', self.group.name)
            self.add_more_info('System', 'Class Handler', self.__class__.__name__)
            self.add_more_info('System', 'Driver info', self.description)
            if self.switch.netmiko_profile:
                self.add_more_info('System', 'Credentials Profile', self.switch.netmiko_profile.name)

            # call the implementation-specific function:
            if hasattr(self, 'get_my_basic_info'):
                # set this to the time the switch data was actually read,
                self.basic_info_read_timestamp = time.time()
                success = self.get_my_basic_info()
                # update the time it took to read the basic info when it was first read:
                read_duration = time.time() - self.basic_info_read_timestamp
                if not success:
                    self.add_warning(f"WARNING: cannot get basic info - {self.error.description}")
                    if self.error.details:
                        self.add_warning(f"Connection Error: {self.error.details}")
                else:
                    self.add_timing('Basic Info Read', 1, read_duration)
                    # All OK, now set the permissions to the interfaces:
                    self._set_interfaces_permissions()

            else:
                self.add_warning("WARNING: device driver does not support 'get_my_basic_info()' !")

            # see if we can get hardware details from the driver:
            if hasattr(self, 'get_my_hardware_details'):
                start_time = time.time()
                self.get_my_hardware_details()
                self.add_timing('HW Info Read', 1, time.time() - start_time)
            # this is optional, so we do not warn if not found!

            # see if the driver has VRF support:
            if hasattr(self, 'get_my_vrfs'):
                start_time = time.time()
                self.get_my_vrfs()
                self.add_timing('VRF Info Read', 1, time.time() - start_time)
            # this is optional, so we do not warn if not found!

            # info about access times, etc.
            default_time = datetime.datetime(2000, 1, 1, 0, 0, 0, 0, datetime.timezone.utc)

            # by the time we get here, the access timestamp for this switch instance has already
            # been written. This previous data was stored in the Connection() object during init:
            if self.last_accessed == default_time:
                self.add_more_info("System", "Last Accessed", "never")
            else:
                self.add_more_info("System", "Last Accessed", self.last_accessed)
                self.add_more_info("System", "Access Count", self.switch.access_count)

            if self.switch.last_changed == default_time:
                self.add_more_info("System", "Last Changed", "never")
            else:
                self.add_more_info("System", "Last Changed", self.switch.last_changed)
                self.add_more_info("System", "Change Count", self.switch.change_count)

            if self.switch.last_command_time == default_time:
                self.add_more_info("System", "Last Command", "never")
            else:
                self.add_more_info("System", "Last Command", self.switch.last_command_time)
                self.add_more_info("System", "Command Count", self.switch.command_count)

            # and save the switch cache:
            # self.save_cache()
        else:
            dprint("  ==> Already loaded from cache!")
        return True

    '''
    This placeholder needs to be implemented by vendor or tech specific drivers.
    return True on success, False on error and set self.error variables

    def get_my_basic_info(self):
        return True

    '''

    def get_client_data(self) -> bool:
        '''
        This loads the layer 2 switch tables, any ARP tables available,
        and LLDP neighbor data.
        Not intended to be cached, so we get fresh, "live" data anytime called!

        Args:
            none

        Returns:
            return True on success, False on error and set self.error variables
        '''
        # clear previous client data
        self.clear_client_data()

        # call the implementation-specific function:
        if hasattr(self, 'get_my_client_data'):
            start_time = time.time()
            self.get_my_client_data()  # to be implemented by device/vendor class!
            stop_time = time.time()
            # add to timing data, for admin use!
            self.add_timing('Client Info Read', 1, time.time() - start_time)
            # are we resolving IP addresses to hostnames?
            if settings.LOOKUP_HOSTNAME_ARP:
                start_time = time.time()
                count = self._lookup_hostname_from_arp()
                # add to timing data, for admin use!
                self.add_timing('DNS Read (arp)', count, time.time() - start_time)
            # are we resolving IP addresses for LLDP neighbors?
            if settings.LOOKUP_HOSTNAME_LLDP:
                start_time = time.time()
                count = self._lookup_hostname_from_lldp()
                # add to timing data, for admin use!
                self.add_timing('DNS Read (lldp)', count, time.time() - start_time)
            # resolve the ethernet OUI to vendor
            start_time = time.time()
            count = self._lookup_ethernet_vendors()
            # add to timing data, for admin use!
            self.add_timing('Ethernet Vendor Search', count, time.time() - start_time)

            return True
        self.add_warning("WARNING: device driver does not support 'get_my_client_data()' !")
        return False

    '''
    placeholder for class-specific implementation to read things like:
        self.get_known_ethernet_addresses()
            this should add EthernetAddress() =objects to the interface.eth dict(),
            indexed by the ethernet address in string format

        self.get_arp_data()

        self.get_lldp_data()
    return True on success, False on error and set self.error variables

    def get_my_client_data(self):
        return True
    '''

    def clear_client_data(self):
        '''
        Clear out all client data, ie arp, lldp, etc.

        Args:
            none

        Returns:
            N/a
        '''
        dprint("clear_client_data()")
        for interface in self.interfaces.values():
            interface.eth = {}
            interface.lldp = {}

    '''
    These are the "set" functions that implement changes on the device.
    The base-class implemention updates the neccessary data that is used by
    the 'views'.
    The actual 'physical' changes on the device need to be implemented
    by the device/vendor specific class, which upon success need to call
    the relevant base-class functions
    '''

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
        dprint(f"Connector.set_interface_admin_status() for {interface.name} to {bool(new_state)}")
        interface.admin_status = bool(new_state)
        # self.save_cache()
        return True

    def set_interface_description(self, interface: Interface, description: str) -> bool:
        '''
        Set the interface description (aka. description) to the string

        Args:
            interface = Interface() object for the requested port
            new_description = a string with the requested text

        Returns:
            return True on success, False on error and set self.error variables
        '''
        dprint(f"Connector.set_interface_description() for {interface.name} to '{description}'")
        interface.description = description
        # self.save_cache()
        return True

    def set_interface_poe_status(self, interface: Interface, new_state: int) -> bool:
        '''
        Set the interface Power-over-Ethernet status as given

        Args:
            interface = Interface() object for the requested port
            new_state = POE_PORT_ADMIN_ENABLED or POE_PORT_ADMIN_DISABLED

        Returns:
            return True on success, False on error and set self.error variables
        '''
        dprint(f"Connector.set_interface_poe_status() for {interface.name} to {new_state}")
        if interface.poe_entry:
            interface.poe_entry.admin_status = int(new_state)
            dprint("   PoE admin_status set OK")
            if new_state == POE_PORT_ADMIN_DISABLED:
                interface.poe_entry.power_consumed = 0
            # self.save_cache()
        else:
            dprint("WARNING: set_interface_poe_status() called on Non-PoE interface!")
        return True

    def set_interface_poe_available(self, interface: Interface, power_available: int) -> bool:
        '''
        Set the interface Power-over-Ethernet available power

        Args:
            interface = Interface() object for the requested port
            power_available = in milli-watts (eg 4.5W = 4500)

        Returns:
            True on success, False on error and set self.error variables
        '''
        dprint(f"Connector.set_interface_poe_available() for {interface.name} to {power_available}")
        if not interface.poe_entry:
            interface.poe_entry = PoePort(interface.index, POE_PORT_ADMIN_ENABLED)
            self.poe_capable = True
            self.poe_enabled = True
        interface.poe_entry.admin_status = POE_PORT_ADMIN_ENABLED
        interface.poe_entry.power_consumption_supported = True
        interface.poe_entry.power_available = int(power_available)
        # self.save_cache()
        dprint("   PoE available power set OK")
        return True

    def set_interface_poe_consumed(self, interface: Interface, power_consumed: int) -> bool:
        '''
        Set the interface Power-over-Ethernet consumed power

        Args:
            interface = Interface() object for the requested port
            power_consumed = in milli-watts (eg 4.5W = 4500)

        Returns:
            True on success, False on error and set self.error variables
        '''
        dprint(f"Connector.set_interface_poe_consumed() for {interface.name} to {power_consumed}")
        if not interface.poe_entry:
            interface.poe_entry = PoePort(interface.index, POE_PORT_ADMIN_ENABLED)
            self.poe_capable = True
            self.poe_enabled = True
        interface.poe_entry.admin_status = POE_PORT_ADMIN_ENABLED
        if power_consumed > 0:
            interface.poe_entry.detect_status = POE_PORT_DETECT_DELIVERING
        interface.poe_entry.power_consumption_supported = True
        interface.poe_entry.power_consumed = int(power_consumed)
        # self.save_cache()
        dprint("   PoE consumed power set OK")
        return True

    def set_interface_poe_detect_status(self, interface: Interface, status: bool) -> bool:
        '''
        set the interface Power-over-Ethernet consumed power

        Args:
            interface: Interface() object for the requested port
            status(boolean): state of PoE on interface

        Returns:
            True on success, False on error and set self.error variables
        '''
        dprint(f"Connector.set_interface_poe_detect_status() for {interface.name} to {status}")
        if not interface.poe_entry:
            interface.poe_entry = PoePort(interface.index, POE_PORT_ADMIN_ENABLED)
            self.poe_capable = True
            self.poe_enabled = True
        interface.poe_entry.detect_status = status
        return True

    def set_interface_untagged_vlan(self, interface: Interface, new_vlan_id: int) -> bool:
        '''
        Set the interface untagged vlan to the given vlan

        Args:
            interface = Interface() object for the requested port
            new_vlan_id = an integer with the requested untagged vlan

        Returns:
            True on success, False on error and set self.error variables
        '''
        dprint(f"Connector.set_interface_untagged_vlan() for {interface.name} to vlan {new_vlan_id}")
        interface.untagged_vlan = int(new_vlan_id)
        # self.save_cache()
        return True

    def add_interface_tagged_vlan(self, interface: Interface, new_vlan: int) -> bool:
        '''
        Add a tagged vlan to the interface trunk.

        Args:
            interface = Interface() object for the requested port
            new_vlan = an integer with the requested tagged vlan

        Returns:
            True on success, False on error and set self.error variables
        '''
        interface.vlans.append(int(new_vlan))
        # self.save_cache()
        return True

    def remove_interface_tagged_vlan(self, interface: Interface, old_vlan: int) -> bool:
        '''
        Remove a tagged vlan from the interface trunk.

        Args:
            interface = Interface() object for the requested port
            old_vlan = an integer with the tagged vlan to removes

        Returns:
            True on success, False on error and set self.error variables
        '''
        interface.vlans.remove(int(old_vlan))
        # self.save_cache()
        return True

    def vlan_create(self, vlan_id: int, vlan_name: str) -> bool:
        '''
        Create a new vlan on this device. This will update the self.vlans{} dict.
        This is a function that needs to be implemented by a specific vendor or technology drivers
        to implemented the actual creation of the vlan. Upon success, this then needs to be
        called for the bookkeeping !

        Args:
            id (int): the vlan id
            name (str): the name of the vlan

        Returns:
            True on success, False on error and set self.error variables.
        '''
        self.add_vlan_by_id(vlan_id=vlan_id, vlan_name=vlan_name)
        # we now need to re-calculate the allowed-vlan list for the current user
        self._set_allowed_vlans()
        return True

    def vlan_edit(self, vlan_id: int, vlan_name: str) -> bool:
        '''
        Edit the vlan name. This will update the self.vlans{} dict.
        This is a function that needs to be implemented by a specific vendor or technology drivers
        to implemented the actual creation of the vlan. Upon success, this then needs to be
        called for the bookkeeping !

        Args:
            id (int): the vlan id
            name (str): the name of the vlan

        Returns:
            True on success, False on error and set self.error variables.
        '''
        self.add_vlan_by_id(vlan_id=vlan_id, vlan_name=vlan_name)
        # update allowed vlans:
        if vlan_id in self.allowed_vlans:
            self.allowed_vlans[vlan_id].name = vlan_name
        return True

    def vlan_delete(self, vlan_id: int) -> bool:
        '''
        Delete the vlan. This will update the self.vlans{} dict.
        This is a function that needs to be implemented by a specific vendor or technology drivers
        to implemented the actual creation of the vlan. Upon success, this then needs to be
        called for the bookkeeping !

        Args:
            id (int): the vlan id

        Returns:
            True on success, False on error and set self.error variables.
        '''
        self.vlans.pop(vlan_id)
        # update allowed vlans as well:
        if vlan_id in self.allowed_vlans:
            self.allowed_vlans.pop(vlan_id)
        return True

    #############################
    # various support functions #
    #############################

    def add_vlan_by_id(self, vlan_id: int, vlan_name: str = '') -> bool:
        '''
        Add a Vlan() object to the device, based on vlan ID and name (if set).
        Store it in the vlans{} dictionary, indexed by vlan_id

        Args:
            vlan_id (int): id of the vlan to add
            vlan_name (str): string representing the vlan name

        Returns:
            True
        '''
        v = Vlan(vlan_id)
        v.name = vlan_name
        self.vlans[vlan_id] = v
        # sort ordered by vlan id; this is needed for vlans added by users.
        self.vlans = dict(sorted(self.vlans.items()))  # note: sorted() returns a list of tuples(key, value), NOT dict!
        return True

    def add_vlan(self, vlan: Vlan) -> bool:
        '''
        Add a new vlan as an object.
        Store it in the vlans{} dictionary, indexed by vlan.id

        Args:
            vlan: a Vlan() object to add to the device

        Returns:
            True
        '''
        self.vlans[vlan.id] = vlan
        return True

    def add_interface(self, interface: Interface) -> bool:
        '''
        Add and Interface() object to the self.interfaces{} dictionary,
        indexed by the interface key.

        Args:
            interface: Interface() object to add

        Returns:
            True on success, False on error and set self.error variables
        '''
        self.interfaces[interface.key] = interface
        return True

    def add_poe_powersupply(self, id: int, power_available: int) -> PoePSE:
        '''
        Add a power supply PoePse() object to the device, and return this new object.

        Args:
            id (int): index of power supply
            power_available (int): max power in Watts

        Returns:
            PoePSI() object created.
        '''
        pse = PoePSE(id)
        pse.set_max_power(power_available)
        pse.set_enabled()
        self.poe_pse_devices[id] = pse
        self.poe_max_power += int(power_available)
        self.poe_capable = True
        self.poe_enabled = True
        return pse

    def set_powersupply_attribute(self, id: int, attribute: str, value) -> bool:
        '''
        set the value for a specified attribute of a power supply indexed by id

        Args:
            id (int) = the ID of the power supply
            attribute (str) = the name of field to set
            value = the value to set the field above.

        Returns:
            True on success, False on error
        '''
        id = int(id)
        dprint(f"set_powersupply_attribute_by_id() for {id}, {attribute} = {value}")
        try:
            setattr(self.poe_pse_devices[id], attribute, value)
            return True
        except Exception as e:
            dprint(f"   ERROR: {e}")
            return False

    def get_interface_by_key(self, key: str) -> Interface | bool:
        '''
        get an Interface() object from out self.interfaces{} dictionary,
        search based on the key that was used when it was added.

        Args:
            key (str): the key used when the Interface() was created.

        Returns:
            Interface() if found, False if not found.
        '''
        key = str(key)
        if key in self.interfaces.keys():
            dprint(f"get_interface_by_key() for '{key}' => Found!")
            return self.interfaces[key]
        dprint(f"get_interface_by_key() for '{key}' => NOT Found!")
        return False

    def get_interface_by_name(self, name: str) -> Interface | bool:
        '''
        get an Interface() object from out self.interfaces{} dictionary,
        search based on the name.

        Args:
            name (str): the value of the Interface().name attribute

        Returns:
            Interface() if found, False if not found.
        '''
        for iface in self.interfaces.values():
            if iface.name == name:
                return iface
        return False

    def set_interface_attribute_by_key(self, key: str, attribute: str, value) -> bool:
        '''
        set the value for a specified attribute of an interface indexed by key

        Args:
            key (str): the index key of the Interface() when created.
            attribute (str): the attribute name of the Interface() object to look for.
            value: the value to set the Interface() attribute to.

        Returns:
            True on success, False on error
        '''
        key = str(key)
        dprint(f"set_interface_attribute_by_key() for {key} ({type(key)}), {attribute} = {value} ({type(value)})")
        try:
            setattr(self.interfaces[key], attribute, value)
            return True
        except Exception as e:
            dprint(f"   ERROR: {e}")
            return False

    def set_save_needed(self, value: bool = True) -> bool:
        '''
        Set a flag that this switch needs the config saved

        Args:
            value(boolean): True or False to set or clear save-needed flag.

        Returns:
            True
        '''
        dprint(f"Connector.set_save_needed({value})")
        if self.can_save_config:
            self.save_needed = value
        return True

    def add_vlan_to_interface(self, iface: Interface, vlan_id: int):
        '''
        Generic function to add a vlan to the list of vlans on the given interface
        This implies the interface is in 802.1q tagged mode (ie 'trunked')

        Args:
            iface: Interface() object to update
            vlan_id: the vlan id to add to this interface.

        Returns:
            none
        '''
        if vlan_id in self.vlans.keys() and self.vlans[vlan_id].type == VLAN_TYPE_NORMAL and vlan_id not in iface.vlans:
            dprint(f"   add_vlan_to_interface(): Adding Vlan {vlan_id} to {iface.name}!")
            iface.vlans.append(vlan_id)
            iface.is_tagged = True

    def set_interfaces_natural_sort_order(self):
        '''
        Some APIs give responses in alphabetic order, eg 1/1/10 before 1/1/2.
        Sort interfaces by their key in natural sort order.

        Args:
            none

        Returns:
            none
        '''
        self.interfaces = OrderedDict({key: self.interfaces[key] for key in natsort.natsorted(self.interfaces)})

    def add_learned_ethernet_address(
        self, if_name: str, eth_address: str, vlan_id: int = -1, ip4_address: str = '', ip6_address: str = ''
    ) -> EthernetAddress | bool:
        '''
        Add an ethernet address to an interface, as given by the layer2 CAM/Switching tables.
        Creates a new EthernetAddress() object and returns it. If the ethernet address already
        exists on the interface, just return the object. The EthernetAddress() objects
        gets stored indexed by address in the interface.eth dict.

        Args:
            if_name(str): interface name (key) as string.
            eth_address(str): ethernet address as string.
            vlan_id(int): vlan where ethernet is learned, if known.
            ip4_address(str): IPv4 address for this ethernet, if known.

        Returns:
            EthernetAddress() on success, False on failure (interface not found).
        '''
        dprint(f"conn.add_learned_ethernet_address() for {eth_address} on {if_name}")
        iface = self.get_interface_by_key(if_name)
        if iface:
            a = iface.add_learned_ethernet_address(
                eth_address=eth_address, vlan_id=vlan_id, ip4_address=ip4_address, ip6_address=ip6_address
            )
            self.eth_addr_count += 1
            return a
        else:
            dprint(f"conn.add_learned_ethernet_address(): Interface {if_name} does NOT exist!")
            return False

    def add_neighbor_object(self, if_name: str, neighbor: NeighborDevice) -> bool:
        '''
        Add an lldp neighbor to an interface.
        It gets stored on the interface.lldp dict.

        Args:
            if_name = interface name
            neighbor = NeighborDevice() object.
        Returns:
            True on success, False on failure.
        '''
        dprint(f"conn.add_neighbor_object() for {str(neighbor)} on {if_name}")
        iface = self.get_interface_by_key(if_name)
        if iface:
            iface.add_neighbor(neighbor)
            self.neighbor_count += 1
            return True
        else:
            dprint(f"conn.add_neighbor_object(): Interface {if_name} does NOT exist!")
            return False

    def get_vrf_by_name(self, name: str) -> Vrf:
        """Get a Vrf() object by name. If not exists, create it

        Args:
            name(str): the name of the VRF to find, or create.

        Returns:
            (Vrf() or False): a valid Vrf() object, or False
        """
        dprint(f"Connector.get_vrf_by_name(name='{name}')")
        if name in self.vrfs:
            return self.vrfs[name]
        # go create a new Vrf()
        vrf = Vrf()
        vrf.name = name
        self.vrfs[name] = vrf
        return vrf

    def save_running_config(self) -> bool:
        '''
        Execute a 'save config' command. This is switch dependent.
        To be implemented by technology or vendor sub-classes, e.g. SnmpConnector()

        Args:
            none

        Returns:
            True if this succeeds, False on failure. self.error() will be set in that case
        '''
        dprint("Connector.save_running_config() - NOT IMPLEMENTED!")
        self.error.status = True
        self.error.description = "Save is NOT implemented!"
        return False

    def can_run_commands(self) -> bool:
        '''
        Does the device have the ability to execute a 'cli command'
        This should be overwritten in a vendor-specific sub-class.
        The default implementation of run_command() is with Netmiko library,
        and we assume that we can indeed run commands if we have a valid credential profile.

        Args:
            none

        Returns:
            True or False
        '''
        if self.switch.primary_ip4 and self.switch.netmiko_profile:
            return True
        return False

    """
    SSH connectivity uses the Netmiko library to connect to a device.
    The varous ssh_* functions implement the netmiko/ssh connection.
    """

    def netmiko_connect(self) -> bool:
        """
        Establish the connection
        return True on success, False on error,
        with self.error.status and self.error.description set accordingly
        """
        dprint("netmiko_connect()")
        self.error.clear()
        if not self.switch.netmiko_profile:
            dprint("  ERROR: No netmiko profile")
            self.error.status = True
            self.error.description = 'No Credentials Profile set! Please ask the admin to correct this.'
            return False

        # try to connect, figure out device type to use:
        if self.netmiko_device_type:
            # hardcoded in driver!
            dprint("  Device type hardcoded!")
            device_type = self.netmiko_device_type
        else:
            if self.netmiko_valid_device_types:
                # we have device_type choices configured,
                # make sure we have a netmiko_profile that matches a choice
                if self.switch.netmiko_profile.device_type not in self.netmiko_valid_device_types:
                    self.error.status = True
                    self.error.description = f"Invalid device type in Credentials Profile ({self.switch.netmiko_profile.device_type}). Valid are '{self.netmiko_valid_device_types}'. Please ask the admin to correct this."
                    return False
                dprint("  Device type valid!")
            else:
                dprint("  Device type: anything goes :-)")
            # set to selected device type:
            device_type = self.switch.netmiko_profile.device_type
        # connection attributes:
        dprint(f"  Netmiko device_type: '{device_type}'")
        device = {
            'device_type': device_type,
            'host': self.switch.primary_ip4,
            'username': self.switch.netmiko_profile.username,
            'password': self.switch.netmiko_profile.password,
            'port': self.switch.netmiko_profile.tcp_port,
            'conn_timeout': settings.SSH_CONNECT_TIMEOUT,
        }

        try:
            handle = netmiko.ConnectHandler(**device)
        except netmiko.NetMikoTimeoutException:
            dprint("netmiko_connect(): ERROR NetMikoTimeoutException")
            self.error.status = True
            self.error.description = "Connection time-out! Please ask the admin to verify the switch hostname or IP, or change the SSH_COMMAND_TIMEOUT configuration."
            return False
        except netmiko.NetMikoAuthenticationException:
            dprint("netmiko_connect(): ERROR NetMikoAuthenticationException")
            self.error.status = True
            self.error.description = "Access denied! Please ask the admin to correct the switch credentials."
            return False
        except netmiko.exceptions.ReadTimeout as err:
            dprint(f"netmiko_connect(): ERROR ReadTimeout: {repr(err)}")
            self.output = "Error: the connection attempt timed out!"
            self.error.status = True
            self.error.description = "Error: the connection attempt timed out!"
            self.error.details = f"Netmiko Error: {repr(err)}"
            return False
        except Exception as err:
            dprint(f"netmiko_connect(): ERROR Generic Error: {str(type(err))}")
            self.error.status = True
            self.error.description = "SSH Connection denied! Please inform your admin."
            self.error.details = f"Netmiko Error: {repr(err)} ({str(type(err))})\n{traceback.format_exc()}"
            return False

        dprint("  connection OK!")
        self.netmiko_connection = handle
        return True

    def netmiko_disable_paging(self) -> bool:
        """
        Disable paging, ie the "hit a key" for more
        We call the Netmiko built-in function with a command set in our drivers.
        This allows us to override the default built-in command set by the Netmiko() object.
        (see __init__() in Netmiko drivers,
         eg.  https://github.com/ktbyers/netmiko/blob/develop/netmiko/hp/hp_comware.py )

        Return:
            (boolean): True on success, False on error.
        """
        dprint("netmiko_disable_paging()")
        self.error.clear()
        if not self.netmiko_disable_paging_command:
            dprint("  Disable command not set, using Netmiko default!")
            return True
        if not self.netmiko_connection:
            dprint("  netmiko.disable_paging(): No connection yet, calling self.connect() (Huh?)")
            if not self.netmiko_connect():
                return False
        if self.netmiko_connection:
            try:
                dprint(f"  Trying with command: '{self.netmiko_disable_paging_command}'")
                self.netmiko_connection.disable_paging(self.netmiko_disable_paging_command)
            except Exception as err:
                dprint(f"  ERROR disabling paging: {err}")
                self.error.status = True
                self.error.description = f"Error disabling SSH paging! {err}"
                return False
        dprint("netmiko_disable_paging() OK!")
        return True

    def netmiko_execute_command(self, command: str) -> bool:
        """
        Execute a single command on the device.
        Save the command output to self.output

        Args:
            command: the string the execute as a command on the device

        Returns:
            (boolean): True if success, False on failure.
        """
        dprint(f"netmiko_execute_command() '{command}'")
        self.error.clear()
        self.netmiko_output = ''
        if not self.netmiko_connection:
            dprint("  netmiko.execute_command(): No connection yet, calling self.connect()")
            if not self.netmiko_connect():
                return False
        if not self.netmiko_disable_paging():
            return False
        dprint("  sending command string...")
        try:
            if self.netmiko_ignore_prompt:
                dprint("  using send_command_timing()!")
                self.netmiko_output = self.netmiko_connection.send_command_timing(
                    command,
                    read_timeout=settings.SSH_COMMAND_TIMEOUT,
                )
            else:
                # regular with prompt parsing:
                self.netmiko_output = self.netmiko_connection.send_command(
                    command,
                    read_timeout=settings.SSH_COMMAND_TIMEOUT,
                )
        except netmiko.exceptions.ReadTimeout as err:
            dprint(f"  Netmiko.connection ReadTimeout: {repr(err)}")
            self.netmiko_output = "Error: the command timed out!"
            self.error.status = True
            self.error.description = "Error: the command timed out!"
            self.error.details = f"Netmiko Error: {repr(err)}"
            return False
        except Exception as err:
            dprint(f"  Netmiko.connection error: {str(type(err))} - {repr(err)}")
            self.netmiko_output = "Error sending command!"
            self.error.status = True
            self.error.description = "Error sending command!"
            self.error.details = f"Netmiko Error: {repr(err)} ({str(type(err))})"
            return False
        dprint("  netmiko_execute_command() OK!")
        return True

    def run_command(self, command_id: int, interface_name: str = '') -> dict:
        '''
        Execute a cli command. This is switch dependent,
        but by default handled via Netmiko library.
        On error, self.error() will also be set.
        Note: if you override and implement, you are responsible
        for checking rights by calling switch.is_valid_command_id() !

        Args:
            command_id = the id (pk) of the Command() object we will execute,
            interface_name = the device interface name, as string.

        Returns:
            a dictionary with result attributes.
        '''
        dprint(f"run_command() called, id='{command_id}', interface=''{interface_name}''")
        # default command result dictionary info:
        cmd = {
            'state': 'list',  # 'list' or 'run'
            'id': 0,  # command chosen to run
            'output': '',  # output of chosen command
            'error_descr': '',  # if set, error that occured running command
            'error_details': '',  # and the details for above
        }
        self.error.clear()
        # Now go exexute a specific Command object by ID
        # instead of using get_object_or_404, we want to register the error!
        # c = get_object_or_404(Command, pk=command_id)
        try:
            c = Command.objects.get(pk=command_id)
        except Exception:
            # not found raises Command.DoesNotExist, but we simple catch all!
            self.error.status = True
            self.error.description = "Invalid command found!"
            self.error.details = f"Command ID '{command_id}' is not valid!"
            cmd['error_descr'] = self.error.description
            cmd['error_details'] = self.error.details
            return cmd

        cmd['command'] = c.command
        if self.request:
            is_staff = self.request.user.is_superuser or self.request.user.is_staff
        else:
            is_staff = False
        if not self.switch.is_valid_command_id(command_id=command_id, is_staff=is_staff):
            self.error.status = True
            self.error.description = "Invalid command found!"
            self.error.details = f"Command ID '{command_id}' is not valid for this device!"
            cmd['error_descr'] = self.error.description
            cmd['error_details'] = self.error.details
            return cmd

        if c.type == CMD_TYPE_INTERFACE:
            if interface_name and interface_name in self.interfaces.keys():
                cmd['command'] = c.command % self.interfaces[interface_name].name
            else:
                # invalid interface name!
                self.error.status = True
                self.error.description = "Invalid interface name found!"
                self.error.details = (
                    f"Interface Command ID '{command_id}' found but interface name '{interface_name}' is invalid!"
                )
                cmd['error_descr'] = self.error.description
                cmd['error_details'] = self.error.details
                return cmd

        cmd['state'] = 'run'
        cmd['id'] = command_id
        # now go do it:
        if self.netmiko_execute_command(cmd['command']):
            cmd['output'] = self.netmiko_output
        else:
            # error occured, pass it on
            cmd['error_descr'] = self.error.description
            cmd['error_details'] = self.error.details
        del self.netmiko_connection
        return cmd

    def run_command_string(self, command_string: str) -> dict:
        '''
        Execute a cli command. This is switch dependent,
        but by default handled via Netmiko library.
        On error, self.error() will also be set.
        Note: if you override and implement, you are responsible

        Args:
            command_string = the string we will execute

        Returns:
             a dictionary with return result attributes.
        '''
        dprint(f"run_command_string() called, str='{command_string}'")
        # default command result dictionary info:
        cmd = {
            'command': command_string,
            'state': 'run',  # 'list' or 'run'
            'id': 0,  # command chosen to run
            'output': '',  # output of chosen command
            'error_descr': '',  # if set, error that occured running command
            'error_details': '',  # and the details for above
        }
        self.error.clear()
        # now go do it:
        if self.netmiko_execute_command(command_string):
            cmd['output'] = self.netmiko_output
        else:
            # error occured, pass it on
            cmd['error_descr'] = self.error.description
            cmd['error_details'] = self.error.details
        del self.netmiko_connection
        return cmd

    def set_do_not_cache_attribute(self, name: str):
        '''
        Add the name of one of our class object attributes
        to the list of do not cache attributes.

        Args:
            name (str): name of attribute to no cache

        Return:
            none
        '''
        if name not in self._do_not_cache:
            self._do_not_cache.append(name)

    def load_cache(self) -> bool:
        '''
        Load cached data to improve performance.

        Args:
            none
        Returns:
            True if cache was read and variables set.
            False if this fails, primarily when the switch id is not correct!
        '''
        dprint("load_cache()")

        if self.request and 'switch_id' in self.request.session.keys():
            # is the cached data for the current switch ?
            if self.request.session['switch_id'] != self.switch.id:
                # wrong switch id, i.e. we changed switches, clear session data!
                dprint("load_cache() for new switch! so clearing cache...")
                self.clear_cache()
                return False

            # Yes - read it
            dprint("load_cache() for current switch!")
            start_time = time.time()
            count = 0
            # get myself from cache :-)
            for attr_name, value in self.__dict__.items():
                dprint(f"Reading cached attribute '{attr_name}'")
                if attr_name not in self._do_not_cache:
                    if attr_name in self.request.session.keys():
                        dprint("   Valid attribute!")
                        # with Django 5, Pickle serialization is no longer supported, so to use the JSON session cache
                        # we use jsonpickle to make sure we can store *any* class object in the sesssion!
                        # keys=True ensures that integer dictionary keys are maintained! (e.g self.vlans)
                        self.__setattr__(attr_name, jsonpickle.decode(self.request.session[attr_name], keys=True))
                        count += 1
                else:
                    dprint("   Ignoring (_do_not_cache)!")

            # call the child-class specific load_my_cache()
            self.load_my_cache()
            self.cache_loaded = True
            stop_time = time.time()
            self.add_timing("Cache load", count, stop_time - start_time)
            return True
        dprint("  NO cache found!")
        return False

    def load_my_cache(self):
        '''
        To be implemented by child classes.
        Allows them to load more cached data.

        Args:
            none

        Returns:
            none
        '''
        return

    def save_cache(self) -> bool:
        '''
        Save various data in a cache for access by the next page.
        By default, we store in the HTTP request session, see also
        add_to_cache() below.
        Can be overriden by sub-class to use other cache mechanisms, eg Redis.

        Args:
            none

        Returns:
            True on success, False on failure.
        '''
        dprint("Connector.save_cache()")
        # for name, value in self.__dict__.items():
        #    dprint(f"dict caching:  { name }")

        if self.request:
            # save switch ID, it all triggers around that!
            start_time = time.time()
            count = 0
            self.request.session['switch_id'] = self.switch.id
            # can I cache myself :-) ?
            for attr_name, value in self.__dict__.items():
                if attr_name not in self._do_not_cache:
                    # with Django 5, Pickle serialization is no longer supported, so to use the JSON session cache
                    # we use jsonpickle to make sure we can store *any* class object in the sesssion!
                    # keys=True ensures that integer dictionary keys are maintained! (e.g self.vlans)
                    dprint(f"  Caching Attrib = {attr_name}")
                    self.request.session[attr_name] = jsonpickle.encode(value, keys=True)
                    count += 1
                else:
                    dprint(f"  NOT caching attrib = {attr_name}")
            # now notify we changed the session data:
            self.request.session.modified = True

            # call the child-class specific save_my_cache()
            self.save_my_cache()
            stop_time = time.time()
            self.add_timing("Cache save", count, stop_time - start_time)
        # else:
        # only happens if running in CLI or tasks
        # dprint("_set_http_session_cache() called but NO http.request found!")
        dprint("save_cache() DONE!")
        return True

    def save_my_cache(self):
        '''
        To be implemented by child classes.
        Allows them to add more cached data.

        Args:
            none

        Returns:
            none
        '''

        return

    def clear_cache(self):
        '''
        clear all cached data, likely because we changed switches

        Args:
            none

        Returns:
            none
        '''
        dprint("clear_cache()")
        clear_switch_cache(self.request)
        # call child-class specific clear-clear_my_cache()
        self.clear_my_cache()
        return

    def clear_my_cache(self):
        '''
        To be implemented by child classes.
        Allows them to override and clear their cached data.

        Args:
            none

        Returns:
            none
        '''
        return

    def set_cache_variable(self, name: str, value: Any) -> bool:
        '''
        Store a variable 'name' in the session cache.
        By default, we use the HTTP request session to cache data.

        Note: we access the session store via the request object.
        We could also access it direct, for possibly better performance:
        https://docs.djangoproject.com/en/3.1/topics/http/sessions/#session-serialization

        Args:
            name (str): name of item to cache
            value: data to cache

        Returns:
            True if set, False is an error occurs.
        '''
        dprint(f"set_cache_variable(): {name}")

        if self.request:
            # store this variable
            self.request.session[name] = value
            # and append the name to the list of cached variable names
            if "cache_var_names" in self.request.session.keys():
                cache_var_names = self.request.session["cache_var_names"]
            else:
                cache_var_names = {}
            # safe this variable name
            cache_var_names[name] = True
            self.request.session["cache_var_names"] = cache_var_names
            # make sure this is stored, can also add this setting:
            # SESSION_SAVE_EVERY_REQUEST=True
            self.request.session.modified = True
            return True
        return False

    def get_cache_variable(self, name: str) -> Any:
        '''
        Read a variable 'name' from the session cache.
        This returns the value if found, or None if not found.

        Note: we access the session store via the request object.
        We could also access it direct, for possibly better performance:
        https://docs.djangoproject.com/en/3.1/topics/http/sessions/#session-serialization

        Args:
            name (str): name of cached item to retrieve

        Returns:
            value of cached item. None if not found.
        '''
        dprint(f"get_cache_variable(): {name}")
        if name in self.request.session.keys():
            dprint("   ... found!")
            return self.request.session[name]
        else:
            return None

    def clear_cache_variable(self, name: str) -> bool:
        '''
        remove variable from cache

        Args:
            name(str): name of cached item to remove

        Returns:
            True if succeeds, False if fails
        '''
        dprint(f"clear_cache_variable(): {name}")
        if self.request and name in self.request.session.keys():
            dprint("   ... found and deleted!")
            del self.request.session[name]
            # update cached variable names
            cache_var_names = self.request.session["cache_var_names"]
            cache_var_names.pop(name)
            self.request.session["cache_var_names"] = cache_var_names
            # and mark session
            self.request.session.modified = True
            return True
        return False

    def add_timing(self, name: str, count: int, time):
        '''
        Function to track response time of the switch
        This add/updates self.timing {}, dictionary to track how long various calls
        take to read. Key = name, value = tuple(item_count, time)

        Args:
            name (str): name of timed item
            count(int): number of occurances of item
            time:  time() is took for this item.

        Returns:
            none
        '''
        self.timing[name] = (count, time)
        (total_count, total_time) = self.timing["Total"]
        total_count += count
        total_time += time
        self.timing["Total"] = (total_count, total_time)

    def add_more_info(self, category, name: str, value: Any):
        '''
        This adds specific pieces of information to the "General Info" tab.
        Items are ordered by category heading, then name/value pairs

        Args:
            categoiry(str): a category name that organized names.
            name(str): an info item name in a category.
            value: the value of named info item.

        Returns:
            none
        '''
        if category not in self.more_info.keys():
            self.more_info[category] = {}
        self.more_info[category][name] = value

    def _can_manage_interface(self, iface: Interface):
        '''
        Function meant to check if this interface can be managed.

        This allows for vendor-specific override in the vendor subclass, to detect e.g. stacking ports
        called from _set_interfaces_permissions() to check for each interface.

        If this returns False, then  _set_interfaces_permissions()
        will not allow any attribute of this interface to be managed (even then admin!)

        Args:
            iface: the Interface() to check.

        Returns:
            True by default
        '''
        return True

    def _map_lacp_members_to_logical(self):
        '''
        Match LACP member interfaces to their 'logical' virtual aggregate interface.
        This is likely not possible at interface discovery time, as the 'lag' interfaces
        have likely not been found yet.

        Will loop through all interfaces, find lacp members, and add their name to the
        list of members of the main virtual aggregate interface.

        Args:
            none

        Returns:
            none
        '''
        for iface in self.interfaces.values():
            if iface.lacp_type == LACP_IF_TYPE_MEMBER:
                lag_iface = self.get_interface_by_key(key=iface.lacp_master_name)
                if lag_iface:
                    # add the member to the aggregator interface:
                    lag_iface.lacp_members[iface.name] = iface.name
                else:
                    dprint(f"Cannot find LAG interface {iface.lacp_master_name} for {iface.name}")

    def _set_allowed_vlans(self):
        '''
        set the list of vlans defined on the switch that are allowed per the SwitchGroup.vlangroups/vlans
        self.vlans = {} dictionary of vlans on the current switch, i.e. Vlan() objects, but
        self.group.vlans and self.group.vlangroups is a list of allowed VLAN() Django objects (see switches/models.py)

        Args:
            none

        Returns:
            none
        '''
        dprint("_set_allowed_vlans()")
        self.allowed_vlans = {}
        # check the vlans on the switch (self.vlans) agains switchgroup.vlan_groups and switchgroup.vlans
        # if self.group.read_only and self.request and not self.request.user.is_superuser:
        # if self.group.read_only or (self.request and self.request.user.profile.read_only):
        if self.read_only:
            # no vlan allowed!
            dprint("  read-only, no vlans allowed!")
            return
        for switch_vlan_id in self.vlans.keys():
            # if allow_all is set, or we are staff or supervisor, allow this vlan:
            if self.group.allow_all_vlans or (
                self.request and (self.request.user.is_superuser or self.request.user.is_staff)
            ):
                self.allowed_vlans[int(switch_vlan_id)] = self.vlans[switch_vlan_id]
                dprint(f"  {switch_vlan_id}: allowed per allow-all or superuser or staff")
            else:
                # 'regular' user, first check the switchgroup.vlan_groups:
                found_vlan = False
                for vlan_group in self.group.vlan_groups.all():
                    for group_vlan in vlan_group.vlans.all():
                        if int(group_vlan.vid) == int(switch_vlan_id):
                            self.allowed_vlans[int(switch_vlan_id)] = self.vlans[switch_vlan_id]
                            found_vlan = True
                            dprint(f"  {switch_vlan_id}: allowed per group.vlan_groups")
                            continue
                # check if this switch vlan is in the list of allowed vlans
                if not found_vlan:
                    for group_vlan in self.group.vlans.all():
                        if int(group_vlan.vid) == int(switch_vlan_id):
                            # save using the switch vlan name, which is possibly different from the VLAN group name!
                            self.allowed_vlans[int(switch_vlan_id)] = self.vlans[switch_vlan_id]
                            dprint(f"  {switch_vlan_id}: allowed per group.vlans(individual)")
                            continue
        return

    def _disable_interface_management(self, interface: Interface):
        """Function that can be implemented by other drivers to disable management of an interface
        Params:
            iface (Interface): the Interface() object to check management of.

        Returns:
            (bool): True is disabled, False if not.
        """
        return False

    def _set_interfaces_permissions(self):
        '''
        For all found interfaces, check out rules to see if this user should be able see or edit them

        Args:
            none

        Returns:
            none
        '''
        dprint("_set_interfaces_permissions()")
        switch = self.switch
        group = self.group
        user = self.request.user

        # find allowed vlans for this user
        self._set_allowed_vlans()

        # apply the permission rules to all interfaces
        for iface in self.interfaces.values():
            # dprint(f"  checking {iface.name}")

            # first give the custom lower driver an opportunity to disable management:
            if self._disable_interface_management(interface=iface):
                continue

            # if disabled by the Connector() driver:
            if self.read_only or iface.disabled:
                iface.manageable = False
                iface.allow_poe_toggle = False
                iface.can_edit_description = False
                continue

            # we can only manage ethernet interfaces!
            if iface.type != IF_TYPE_ETHERNET:
                iface.manageable = False
                iface.allow_poe_toggle = False
                iface.can_edit_description = False
                if settings.HIDE_NONE_ETHERNET_INTERFACES:
                    iface.visible = False
                    continue

            # if we are showing it, check other thing as well:

            # Layer 3 (routed mode) ethernet interfaces are denied (but shown)!
            if iface.is_routed:
                iface.manageable = False
                iface.allow_poe_toggle = False
                iface.can_edit_description = False
                iface.visible = True
                iface.unmanage_reason = "Access denied: interface in routed mode!"
                continue

            # next check vendor-specific restrictions. This allows denying Stacking ports, etc.
            # vendor should set reason for not managing!
            if not self._can_manage_interface(iface):
                iface.manageable = False
                iface.allow_poe_toggle = False
                iface.can_edit_description = False
                iface.visible = True
                continue

            # Read-Only switch cannot be overwritten, not even by SuperUser!
            # if switch.read_only or group.read_only or user.profile.read_only:
            if self.read_only:
                iface.manageable = False
                iface.unmanage_reason = "Access denied: Read-Only"
                iface.allow_poe_toggle = False
                iface.can_edit_description = False
                iface.visible = True
                continue

            # super-users have access to all other ethernet interfaces!
            if user.is_superuser:
                if iface.type == IF_TYPE_ETHERNET:
                    iface.manageable = True
                    iface.visible = True
                    iface.allow_poe_toggle = True
                    iface.can_edit_description = True
                continue

            # globally allow PoE toggle:
            # we can also enable PoE toggle globally, per user, group or switch, if allowed somewhere:
            if (
                settings.ALWAYS_ALLOW_POE_TOGGLE
                or switch.allow_poe_toggle
                or group.allow_poe_toggle
                or user.profile.allow_poe_toggle
            ):
                iface.allow_poe_toggle = True

            # we can also modify interface description, if allowed everywhere:
            if switch.edit_if_descr and group.edit_if_descr and user.profile.edit_if_descr:
                iface.can_edit_description = True

            # For regular users, next apply any rules that HIDE first !!!

            # check interface types first, only show ethernet and aggregaton types
            # this hides vlan, loopback etc. interfaces for the regular user.
            if iface.type not in visible_interfaces.keys():
                iface.visible = False
                iface.manageable = False  # just to be safe :-)
                iface.unmanage_reason = "Interface access denied: type is not visible!"  # should never show!
                continue

            # see if this regex matches the interface name, e.g. GigabitEthernetx/x/x
            if settings.IFACE_HIDE_REGEX_IFNAME != "":
                match = re.match(settings.IFACE_HIDE_REGEX_IFNAME, iface.name)
                if match:
                    iface.manageable = False  # match, so we cannot modify! Show anyway...
                    iface.unmanage_reason = "Interface access denied: name matches admin deny setting!"
                    continue

            # see if this regex matches the interface 'ifAlias' aka. the interface description
            if settings.IFACE_HIDE_REGEX_IFDESCR != "":
                match = re.match(settings.IFACE_HIDE_REGEX_IFDESCR, iface.description)
                if match:
                    iface.manageable = False  # match, so we cannot modify! Show anyway...
                    iface.unmanage_reason = "Interface access denied: description matches admin deny setting!"
                    continue

            # see if we should hide interfaces with speeds above this value in Mbps.
            if int(settings.IFACE_HIDE_SPEED_ABOVE) > 0 and int(iface.speed) > int(settings.IFACE_HIDE_SPEED_ABOVE):
                iface.manageable = False  # match, so we cannot modify! Show anyway...
                iface.unmanage_reason = "Interface access denied: speed is denied by admin setting!"
                continue

            # check if this vlan is in the group allowed vlans list:
            if int(iface.untagged_vlan) not in self.allowed_vlans.keys():
                iface.manageable = False  # match, so we cannot modify! Show anyway...
                iface.unmanage_reason = "Interface access denied: you do not have access to the interface vlan!"
                continue

            # finally, we can edit this interface!
            iface.manageable = True

        dprint("_set_interfaces_permissions() done!")
        return

    def add_log(self, description: str, type: int, action: int):
        '''
        Log a message about some event on this device to the log table.

        Args:
            description (str): a string describing the log entry.
            type (int): the log type, as defined by the LOG_TYPE_xxx values.
            action (int): the action this message pertains to, as defined by the LOG_xxx values.

        Returns:
            none
        '''
        if self.group:
            group = self.group
        else:
            # this happens when we close a device, we no longer have the group object!
            group = None
        log = Log(
            group=group,
            switch=self.switch,
            ip_address=get_remote_ip(self.request),
            type=type,
            action=action,
            description=description,
        )
        if self.request:
            log.user = self.request.user
        log.save()
        return

    def add_warning(self, warning: str, add_log: bool = True):
        '''
        Add a warning to the self.warnings[] list, and log it as well!

        Args:
            warning(str): warning text to add to list and log

        Returns:
            none
        '''
        self.warnings.append(warning)
        if add_log:
            # add a log message
            self.add_log(type=LOG_TYPE_WARNING, action=LOG_CONNECTION_ERROR, description=warning)
        # done!
        return

    def log_error(self, error: Error | bool = False):
        '''
        Log the current error, either passed in, or as set in the self.error() object.

        Args:
            error: an Error() object with error info.

        Returns:
            none
        '''
        err = False
        if error:
            err = error
        elif self.error.status:
            err = self.error
        if err:
            # add a log message
            self.add_log(
                type=LOG_TYPE_ERROR,
                action=LOG_CONNECTION_ERROR,
                description=f"{self.error.description}: {self.error.details}",
            )
        # done!
        return

    def add_vendor_data(self, category: str, name: str, value: Any):
        '''
        This adds a vendor specific piece of information to self.vendor_data[].
        This is shown on the "Info" tab of the device html page.
        Items are ordered by category heading, then name/value pairs

        Args:
            category(str): a category for origanizing names
            name(str): the named entry to add to the category
            value: the value of the named entry

        Returns:
            none
        '''
        vdata = VendorData(name, value)
        if category not in self.vendor_data.keys():
            self.vendor_data[category] = []
        self.vendor_data[category].append(vdata)

    def get_switch_vlans(self) -> dict:
        '''
        Return the list of self.vlans defined on this switch

        Args:
            none

        Returns:
            self.vlans, a list of vlans
        '''
        return self.vlans

    def get_vlan_by_id(self, vlan_id: int) -> bool | Vlan:
        '''
        Return the Vlan() object for the given id

        Args:
            vlan_id(int): the vlan ID desired.

        Returns:
            the Vlan() object if found, else False
        '''
        dprint(f"get_vlan_by_id({id}={type(vlan_id)})")
        vlan_id = int(vlan_id)
        if vlan_id in self.vlans.keys():
            return self.vlans[vlan_id]
        return False

    def vlan_exists(self, vlan_id: int) -> bool:
        '''
        If a vlan ID exists, return True otherwize False.

        Args:
            vlan_id (int): the ID of the vlan to check

        Returns:
            (boolean):  True if vlan id exists, False if not
        '''
        if int(vlan_id) in self.vlans.keys():
            return True
        return False

    def _lookup_hostname_from_arp(self):
        """Look up the hostnames for found ethernet/arp pairs on all interfaces.
        Fill the hostname attribute for all arp IP's found, using dns resolution of
        the PTR reverse lookup.

        Args:
            none

        Returns:
            (int): number of entries attempted to resolve.
        """
        dprint("_lookup_hostname_from_arp() called.")
        count = 0
        for interface in self.interfaces.values():
            for eth in interface.eth.values():
                if eth.address_ip4:
                    eth.hostname = get_ip_dns_name(eth.address_ip4)
                    count += 1
                # only resolve IPv6 if IPv4 did not resolve hostname
                if not eth.hostname and eth.address_ip6:
                    eth.hostname = get_ip_dns_name(eth.address_ip6)
                    count += 1
        return count

    def _lookup_hostname_from_lldp(self):
        """Look up the hostnames for found lldp neigbors on all interfaces,
        if the chassis address type an ip address.
        Fill the hostname attribute using dns resolution of
        the PTR reverse lookup.

        Args:
            none

        Returns:
            (int): number of entries attemted to resolve.
        """
        dprint("_lookup_hostname_from_lldp() called.")
        count = 0
        for interface in self.interfaces.values():
            for neighbor in interface.lldp.values():
                if neighbor.chassis_type == LLDP_CHASSIC_TYPE_NET_ADDR:
                    # networkAddress(5), first byte is address type, next bytes are address.
                    # see https://www.iana.org/assignments/address-family-numbers/address-family-numbers.xhtml
                    if neighbor.chassis_string_type in [IANA_TYPE_IPV4, IANA_TYPE_IPV6]:
                        count += 1
                        neighbor.hostname = get_ip_dns_name(neighbor.chassis_string)
        return count

    def _lookup_ethernet_vendors(self):
        """Look up the vendor names for the ethernet addresses found on interfaces.
           This will also lookup lldp neighbor vendors if the chassis info is ethernet.

        Args:
            none

        Returns:
            (int): number of entries attemted to resolve.
        """
        dprint("_lookup_ethernet_vendors() called.")

        # load the Wireshark ethernet OUI parser
        parser = manuf.manuf.MacParser()
        # go through the list of ethernet addresses on each interface
        count = 0
        for interface in self.interfaces.values():
            for eth in interface.eth.values():
                count += 1
                eth.vendor = self._get_oui_vendor(parser=parser, ethernet_address=str(eth))
                dprint(f"  Vendor = {eth.vendor}")
            # also lookup vendor for Neighbors where the chassis-string is an ethernet address:
            for neighbor in interface.lldp.values():
                if neighbor.chassis_type == LLDP_CHASSIC_TYPE_ETH_ADDR:
                    count += 1
                    neighbor.vendor = self._get_oui_vendor(parser=parser, ethernet_address=neighbor.chassis_string)
                    dprint(f"  Neighbor vendor = {neighbor.vendor}")
        return count

    def _get_oui_vendor(self, parser, ethernet_address: str) -> str:
        '''Look up an ethernet address in the OUI database, and return vendor information.

        Args:
            parser: a pre-loaded manuf.MacParser() object.
            ethernet_address (str): the string representing the ethernet address

        Returns:
            (str): vendor name with either .manuf_long or .manuf string representing OUI vendor name.
            if unknown, returns ""
        '''
        dprint(f"_get_oui_vendor() for '{ethernet_address}'")
        # try to get the vendor from the OUI list
        try:
            vendor = parser.get_all(ethernet_address)
            if vendor.manuf_long:
                return vendor.manuf_long
            elif vendor.manuf:
                return vendor.manuf
        except Exception as err:
            dprint(f"ERROR: cannot get Ethernet vendor for '{ethernet_address}")
            # this will also add log entry:
            self.add_warning(f"Error retrieving Ethernet vendor for '{ethernet_address}' (error: {err})")
            return ''

        return ''

    def display_name(self) -> str:
        '''
        Set the object display name based on device class and switch named

        Args:
            none

        Returns:
            a string representing the device display name.
        '''
        return f"{self.__class__.__name__} for {self.switch.name}"

    def __str__(self) -> str:
        return self.display_name


# --- End of Connector() ---


'''
We need one helper function, since we will need to clear the cache outside
the context of a class...
'''


def clear_switch_cache(request: HttpRequest):
    '''
    Clear all cached data for the current switch.
    Does not return anything.

    Args:
        request: the Django http_reques() object.

    Returns:
        none
    '''
    dprint("clear_switch_cache() called:")
    if request:
        # all we have to do it clear the 'switch_id' !
        if 'switch_id' in request.session:
            del request.session['switch_id']
            request.session.modified = True
        # if not found, we had not selected a switch before. ie upon login!
