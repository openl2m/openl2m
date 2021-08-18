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
import array
import re
import time
import netaddr

from django.conf import settings

from switches.models import Command, Log
from switches.constants import *
from switches.utils import *
from switches.connect.classes import *
from switches.connect.constants import *
from switches.connect.netmiko.execute import NetmikoExecute


"""
Base Connector() class for OpenL2M.
This implements the interface that is expected by the higher level code
that calls this (e.g in the view.py functions that implement the url handling)
"""


class Connector():
    """
    This base class defines the basic interface for all switch connections.
    """
    def __init__(self, request=False, group=False, switch=False):

        dprint("Connector() __init__")

        self.request = request  # if running on web server, Django http request object, needed for request.user() and request.session[]
        self.group = group      # Django SwitchGroup object
        self.switch = switch    # Django Switch()
        self.error = Error()
        self.error.status = False   # we don't actually have an error yet :-)

        # caching related. All attributes but these will be cached:
        self.do_not_cache = [
            "do_not_cache", "request", "group", "switch", "error",
        ]

        self.hostname = ""      # system hostname, typically set in sub-class
        self.vendor_name = ""   # typically set in sub-classes

        # data we collect and potentially cache:
        self.interfaces = {}        # Interface() objects representing the ports on this switch, key is if_name
        self.vlans = {}             # Vlan() objects on this switch, key is vlan id (not index!)
        self.ip4_to_if_index = {}   # the IPv4 addresses as keys, with stored value if_index; needed to map netmask to interface
        self.syslog_msgs = {}       # list of Syslog messages, if any
        self.syslog_max_msgs = 0    # how many syslog msgs device will store
        # some flags:
        self.hwinfo_needed = True   # True if we still need to read the Entity tables
        self.cache_loaded = False   # if True, system data was loaded from cache
        # some timestamps:
        self.basic_info_read_timestamp = 0    # when the last 'basic' snmp read occured
        self.basic_info_read_duration = 0     # time in seconds for initial basic info gathering
        self.detailed_info_duration = 0  # time in seconds for each detailed info gathering

        # data we calculate or collect without caching:
        self.allowed_vlans = {}     # list of vlans (stored as Vlan() objects) allowed on the switch, the join of switch and group Vlans
        self.eth_addr_count = 0     # number of known mac/ethernet addresses
        self.neighbor_count = 0     # number of lldp neighbors
        self.warnings = []          # list of warning strings that may be shown to users
        # timing related attributes:
        self.start_time = 0     # start time of current action
        self.stop_time = 0      # and the stop time
        self.timing = {}            # dictionary to track how long various calls take to read. Key = name, value = tuple()
        self.add_timing("Total", 0, 0)     # initialize the 'total' count to 0 entries, 0 seconds!

        # PoE related values
        self.poe_capable = False     # can the switch deliver PoE
        self.poe_enabled = False     # note: this needs more work, as we do not parse "units"/stack members
        self.poe_max_power = 0       # maximum power (watts) availabe in this switch, combines all PSE units
        self.poe_power_consumed = 0  # same for power consumed, across all PSE units
        self.poe_pse_devices = {}    # list of PoePSE() objects

        # features that may or may not be implemented:
        self.vlan_change_implemented = self.can_change_interface_vlan()     # if True, enables vlan editing if permissions allow it
        self.gvrp_enabled = False
        # set this flag is a save aka. 'write mem' is needed:
        self.save_needed = False

        # physical device related:
        self.hwinfo_needed = True   # True if we still need to read more hardware info (eg. the Entity tables)
        self.stack_members = {}     # list of StackMember() objects that are part of this switch
        # syslog related info, if supported:
        self.syslog_msgs = {}       # list of Syslog messages, if any
        self.syslog_max_msgs = 0    # how many syslog msgs device will store
        # generic info for the "Switch Information" tab:
        self.more_info = {}         # dict of categories string, each a list of tuples (name, value), to extend sytem info about this switch!

        # self.add_warning("Test Warning, Ignore!")

    """
    These are the high level functions used to "get" interface information.
    These are called by the switches.view functions to display data.
    """

    def get_basic_info(self):
        """
        This is called from view.py to load the basic set of information about the switch.
        We call an device implementation specific function "get_my_basic_info()"
        that should load the following class attributes:
            self.interfaces = {} dictionary of interfaces (ports) on the current
                switch, i.e. Interface() objects, indexed by a class-specific key (string).
            self.vlans = {} dictionary of vlans on the current switch, i.e. Vlan()
                objects, indexed by vlan id (integer number)
        return True on success, False on error and set self.error variables
        """
        self.error.clear()
        dprint("Connector.get_basic_info()")
        # set this to the time the switch data was actually read,
        # including when this may have been read before it got cached:
        if not self.cache_loaded:
            dprint("  => Cache did NOT load!")
            # we need to read the device class:
            self.basic_info_read_timestamp = time.time()

            # call the implementation-specific function:
            self.get_my_basic_info()

            # update the time it took to read the basic info when it was first read:
            read_duration = int((time.time() - self.basic_info_read_timestamp) + 0.5)

            # you have to set the permissions to the interfaces:
            self._set_interfaces_permissions()

            self.add_more_info('System', 'Basic Info Read', f"{read_duration} seconds")

            # and save the switch cache:
            # self.save_cache()
            # update counters
            # self.switch.save()

        return True

    def get_my_basic_info(self):
        """
        placeholder for class-specific implementation to read Interfaces() etc.
        return True on success, False on error and set self.error variables
        """
        return True

    def get_client_data(self):
        """
        This loads the layer 2 switch tables, any ARP tables available,
        and LLDP neighbor data.
        Not intended to be cached, so we get fresh, "live" data anytime called!
        return True on success, False on error and set self.error variables
        """
        start_time = time.time()

        # call the implementation-specific function:
        self.get_my_client_data()   # to be implemented by device/vendor class!

        self.detailed_info_duration = int((time.time() - start_time) + 0.5)
        return True

    def get_my_client_data(self):
        """
        placeholder for class-specific implementation to read things like:
            self.get_known_ethernet_addresses()
                this should add EthernetAddress() =objects to the interface.eth dict(),
                indexed by the ethernet address in string format

            self.get_arp_data()

            self.get_lldp_data()
        return True on success, False on error and set self.error variables
        """
        return True

    def get_detailed_info(self):
        """
        Get all (possible) hardware info, stacking details, etc.
        return True on success, False on error and set self.error variables
        """

        # call the vendor-specific data first, if implemented
        self.get_my_detailed_info()

        # set the flag to indicate we read this already, and store in session
        # if flag is set, the button will not be shown in menu bar!
        self.hwinfo_needed = False
        # and cache it:
        # self.save_cache()
        return True

    def get_my_detailed_info(self):
        """
        placeholder for class-specific implementation to read things like:
            stacking info, serial #, and whatever you want to add:
            Attributes:
            self.stack_members
            self.syslog_max_msgs
            self.syslog_msgs
        return True on success, False on error and set self.error variables
        """
        return True

    """
    These are the "set" functions that implement changes on the device.
    The base-class implemention updates the neccessary data that is used by
    the 'views'.
    The actual 'physical' changes on the device need to be implemented
    by the device/vendor specific class, which upon success need to call
    the relevant base-class functions
    """

    def set_interface_admin_status(self, interface, new_state):
        """
        set the interface to the requested state (up or down)
        interface = Interface() object for the requested port
        new_state = True / False  (enabled/disabled)
        return True on success, False on error and set self.error variables
        """
        # interface.admin_status = new_state
        dprint(f"Connector.set_interface_admin_status() for {interface.name} to {bool(new_state)}")
        interface.admin_status = bool(new_state)
        # self.save_cache()
        return True

    def set_interface_description(self, interface, description):
        """
        set the interface description (aka. description) to the string
        interface = Interface() object for the requested port
        new_description = a string with the requested text
        return True on success, False on error and set self.error variables
        """
        dprint(f"Connector.set_interface_description() for {interface.name} to '{description}'")
        interface.description = description
        # self.save_cache()
        return True

    def set_interface_poe_status(self, interface, new_state):
        """
        set the interface Power-over-Ethernet status as given
        interface = Interface() object for the requested port
        new_state = POE_PORT_ADMIN_ENABLED or POE_PORT_ADMIN_DISABLED
        return True on success, False on error and set self.error variables
        """
        dprint(f"Connector.set_interface_poe_status() for {interface.name} to {new_state}")
        if interface.poe_entry:
            interface.poe_entry.admin_status = int(new_state)
            dprint("   PoE set OK")
            if new_state == POE_PORT_ADMIN_DISABLED:
                interface.poe_entry.power_consumed = 0
            # self.save_cache()
        return True

    def set_interface_poe_available(self, interface, power_available):
        """
        set the interface Power-over-Ethernet available power
        interface = Interface() object for the requested port
        power_availablr = in milli-watts (eg 4.5W = 4500)
        returns True on success, False on error and set self.error variables
        """
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

    def set_interface_poe_consumed(self, interface, power_consumed):
        """
        set the interface Power-over-Ethernet consumed power
        interface = Interface() object for the requested port
        power_consumed = in milli-watts (eg 4.5W = 4500)
        returns True on success, False on error and set self.error variables
        """
        dprint(f"Connector.set_interface_poe_consumed() for {interface.name} to {power_consumed}")
        if not interface.poe_entry:
            interface.poe_entry = PoePort(interface.index, POE_PORT_ADMIN_ENABLED)
            self.poe_capable = True
            self.poe_enabled = True
        interface.poe_entry.admin_status = POE_PORT_ADMIN_ENABLED
        interface.poe_entry.detect_status = POE_PORT_DETECT_DELIVERING
        interface.poe_entry.power_consumption_supported = True
        interface.poe_entry.power_consumed = int(power_consumed)
        # self.save_cache()
        dprint("   PoE consumed power set OK")
        return True

    def set_interface_untagged_vlan(self, interface, new_pvid):
        """
        set the interface untagged vlan to the given vlan
        interface = Interface() object for the requested port
        new_pvid = an integer with the requested untagged vlan
        return True on success, False on error and set self.error variables
        """
        dprint(f"Connector.set_interface_untagged_vlan() for {interface.name} to vlan {new_pvid}")
        interface.untagged_vlan = int(new_pvid)
        # self.save_cache()
        return True

    def add_interface_tagged_vlan(self, interface, new_vlan):
        """
        add a tagged vlan to the interface trunk.
        interface = Interface() object for the requested port
        new_vlan = an integer with the requested tagged vlan
        return True on success, False on error and set self.error variables
        """
        interface.vlans.append(int(new_vlan))
        # self.save_cache()
        return True

    def remove_interface_tagged_vlan(self, interface, old_vlan):
        """
        remove a tagged vlan from the interface trunk.
        interface = Interface() object for the requested port
        old_vlan = an integer with the tagged vlan to removes
        return True on success, False on error and set self.error variables
        """
        interface.vlans.remove(int(old_vlan))
        # self.save_cache()
        return True

    def add_interface_learned_ethernet(self, interface, ethernet_address):
        """
        add a learned/heard EthernetAddress) object to the interface.eth{} dictionary.
        interface = Interface() object for the requested port
        ethernet_address = EthernetAddress() object with details set
        return True on success, False on error and set self.error variables
        """
        interface.add_learned_ethernet_address(ethernet_address)
        # self.save_cache()
        return

    def add_interface_neighbor(self, interface, neighbor):
        """
        add a NeighborDevice() object to the interface.lldp{} dictionary.
        interface = Interface() object for the requested port
        neighbor = LldpNeighbor() object with details set
        return True on success, False on error and set self.error variables
        """
        interface.add_neighbor(neighbor)
        # self.save_cache()
        return True

    def add_neighbor_to_interface_by_name(self, if_name, neighbor):
        '''
        Add an lldp neighbor to an interface.
        if_name = interface name
        neighbor = NeighborDevice() object.
        It gets stored on the interface.lldp dict.
        return True on success, False on failure.
        '''
        dprint(f"conn.add_neighbor_to_interface_by_name() for {str(neighbor)} on {if_name}")
        iface = self.get_interface_by_key(if_name)
        if iface:
            iface.add_neighbor(neighbor)
            self.neighbor_count += 1
            return True
        else:
            dprint(f"conn.add_neighbor_to_interface_by_name(): Interface {if_name} does NOT exist!")
            return False

    #############################
    # various support functions #
    #############################

    def add_vlan_by_id(self, vlan_id, vlan_name="Not set"):
        """
        Add a Vlan() object to the device, based on vlan ID and name (if set).
        Store it in the vlans{} dictionary, indexed by vlan_id
        return True
        """
        v = Vlan(vlan_id)
        v.name = vlan_name
        self.vlans[vlan_id] = v
        return True

    def add_vlan(self, vlan):
        """
        vlan is a Vlan() object to add to the device
        Store it in the vlans{} dictionary, indexed by vlan.id
        return True
        """
        self.vlans[vlan.id] = vlan
        return True

    def add_interface(self, interface):
        """
        Add and Interface() object to the self.interfaces{} dictionary,
        indexed by the interface key.
        return True on success, False on error and set self.error variables
        """
        self.interfaces[interface.key] = interface
        return True

    def add_poe_powersupply(self, id, power_available):
        """
        Add a power supply PoePse() object to the device,
        id = index of power supply
        power_available = max power in Watts
        return True on success, False on error and set self.error variables
        """
        self.poe_pse_devices[id] = PoePSE(id)
        self.poe_pse_devices[id].max_power = int(power_available)
        self.poe_max_power += int(power_available)
        self.poe_capable = True
        self.poe_enabled = True
        return True

    def get_interface_by_key(self, key):
        """
        get an Interface() object from out self.interfaces{} dictionary,
        search based on the key that was used when it was added.
        return Interface() if found, False if not found.
        """
        key = str(key)
        if key in self.interfaces.keys():
            dprint(f"get_interface_by_key() for '{key}' => Found!")
            return self.interfaces[key]
        dprint(f"get_interface_by_key() for '{key}' => NOT Found!")
        return False

    def set_interface_attribute_by_key(self, key, attribute, value):
        """
        set the value for a specified attribute of an interface indexed by key
        return True on success, False on error
        """
        key = str(key)
        dprint(f"set_interface_attribute_by_key() for {key}, {attribute} = {value}")
        try:
            setattr(self.interfaces[key], attribute, value)
            return True
        except Exception as e:
            return False

    def set_save_needed(self, value=True):
        """
        Set a flag that this switch needs the config saved
        just return True
        """
        dprint(f"Connector.set_save_needed({value})")
        if self.can_save_config():
            self.save_needed = value
        return True

    def can_change_interface_vlan(self):
        """
        Return True if we can change a vlan on an interface, False if not
        """
        return False

    def add_vlan_to_interface(self, iface, vlan_id):
        """
        Generic function to add a vlan to the list of vlans on the given interface
        This implies the interface is in 802.1q tagged mode (ie 'trunked')
        """
        if vlan_id in self.vlans.keys() and self.vlans[vlan_id].type == VLAN_TYPE_NORMAL and vlan_id not in iface.vlans:
            dprint(f"   add_vlan_to_interface(): Adding Vlan {vlan_id} to {iface.name}!")
            iface.vlans.append(vlan_id)
            iface.is_tagged = True

    def add_learned_ethernet_address(self, if_name, eth_address):
        '''
        Add an ethernet address to an interface, as given by the layer2 CAM/Switching tables.
        Creates a new EthernetAddress() object and returns it. If the ethernet address already
        exists on the interface, just return the object.
        if_name = interface name (key)
        eth_address_obj = EthernetAddress() object.
        It gets stored indexed by address on the interface.eth dict.
        return EthernetAddress() on success, False on failure.
        '''
        dprint(f"conn.add_learned_ethernet_address() for {eth_address} on {if_name}")
        iface = self.get_interface_by_key(if_name)
        if iface:
            a = iface.add_learned_ethernet_address(eth_address)
            self.eth_addr_count += 1
            return a
        else:
            dprint(f"conn.add_learned_ethernet_address(): Interface {if_name} does NOT exist!")
            return False

    def can_save_config(self):
        """
        Does the switch have the ability (or need) to execute a 'save config'
        or 'write memory' as it known on many platforms. This should be overwritten
        in a vendor-specific sub-class. We just return False here.
        Returns True or False
        """
        return False

    def save_running_config(self):
        """
        Execute a 'save config' command. This is switch dependent.
        To be implemented by technology or vendor sub-classes, e.g. SnmpConnector()
        Returns True if this succeeds, False on failure. self.error() will be set in that case
        """
        self.error.status = True
        self.error.description = "Save is NOT implemented!"
        return False

    def can_run_commands(self):
        """
        Does the switch have the ability to execute a 'cli command'
        This should be overwritten in a vendor-specific sub-class.
        The default implementation of run_command() is with Netmiko library,
        and we assume that we can indeed run commands.
        Returns True or False
        """
        return True

    def run_command(self, command_id, interface_name=''):
        """
        Execute a cli command. This is switch dependent,
        but by default handled via Netmiko library.
        Returns a command dictionary with results.
        On error, self.error() will also be set.
        Note: if you override and implement, you are responsible
        for checking rights by calling switch.is_valid_command_id() !
        """
        dprint(f"run_command() called, id='{command_id}', interface=''{interface_name}''")
        # default command result dictionary info:
        cmd = {
            'state': 'list',        # 'list' or 'run'
            'id': 0,                # command chosen to run
            'output': '',           # output of chosen command
            'error_descr': '',      # if set, error that occured running command
            'error_details': '',    # and the details for above
        }
        self.error.clear()
        # Now go exexute a specific Command object by ID
        # instead of using get_object_or_404, we want to register the error!
        # c = get_object_or_404(Command, pk=command_id)
        try:
            c = Command.objects.get(pk=command_id)
        except e:
            # not found raises Command.DoesNotExist, but we simple catch all!
            self.error.status = True
            self.error.description = "Invalid command found!"
            self.error.details = f"Command ID '{command_id}' is not valid!"
            cmd['error_descr'] = self.error.description
            cmd['error_details'] = self.error.details
            return cmd

        cmd['command'] = c.command
        if self.request:
            is_staff = (self.request.user.is_superuser or self.request.user.is_staff)
        else:
            is_staff = False
        if not self.switch.is_valid_command_id(command_id=command_id,
                                               is_staff=is_staff):
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
                self.error.details = f"Interface Command ID '{command_id}' found but interface name '{interface_name}' is invalid!"
                cmd['error_descr'] = self.error.description
                cmd['error_details'] = self.error.details
                return cmd

        cmd['state'] = 'run'
        cmd['id'] = command_id
        # now go do it:
        nm = NetmikoExecute(self.switch)
        if nm.execute_command(cmd['command']):
            cmd['output'] = nm.output
            del nm
        else:
            # error occured, pass it on
            cmd['error_descr'] = nm.error.description
            cmd['error_details'] = nm.error.details
            self.error.status = True
            self.error.description = nm.error.description
            self.error.details = nm.error.details
        return cmd

    def set_do_not_cache_attribute(self, name):
        """
        Add the name of one of our class object attributes
        to the list of do not cache attributes.
        Return nothing.
        """
        if name not in self.do_not_cache:
            self.do_not_cache.append(name)
        return

    def load_cache(self):
        """
        Load cached data to improve performance.
        Returns True if cache was read and variables set.
        False if this fails, primarily when the switch id is not correct!
        """
        dprint("load_cache()")

        if self.request and "switch_id" in self.request.session.keys():
            switch_id = -1
            # is the cached data for the current switch ?
            if "switch_id" in self.request.session.keys():
                if self.request.session["switch_id"] != self.switch.id:
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
                if attr_name not in self.do_not_cache:
                    if attr_name in self.request.session.keys():
                        dprint("   Valid attribute!")
                        self.__setattr__(attr_name, self.request.session[attr_name])
                        count += 1
                else:
                    dprint("   Ignoring (do_not_cache)!")

            # call the child-class specific load_my_cache()
            self.load_my_cache()
            self.cache_loaded = True
            stop_time = time.time()
            self.add_timing("Cache load", count, stop_time - start_time)
            return True

        return False

    def load_my_cache(self):
        """
        To be implemented by child classes.
        Allows them to load more cached data.
        """
        return

    def save_cache(self):
        """
        Save various data in a cache for access by the next page.
        By default, we store in the HTTP request session, see also
        add_to_cache() below.
        Can be overriden by sub-class to use other cache mechanisms, eg Redis.
        Return True on success, False on failure.
        """
        """
        Store the snmp switch data in the http session, if exists
        """
        dprint("Connector.save_cache()")
        # for name, value in self.__dict__.items():
        #    dprint(f"dict caching:  { name }")

        if self.request:
            # save switch ID, it all triggers around that!
            start_time = time.time()
            count = 0
            self.request.session["switch_id"] = self.switch.id
            # can I cache myself :-) ?
            for attr_name, value in self.__dict__.items():
                if attr_name not in self.do_not_cache:
                    dprint(f"Caching Attrib = {attr_name}")
                    self.request.session[attr_name] = value
                    count += 1
                else:
                    dprint(f"NOT caching attrib = {attr_name}")
            # now notify we changed the session data:
            self.request.session.modified = True

            # call the child-class specific save_my_cache()
            self.save_my_cache()
            stop_time = time.time()
            self.add_timing("Cache save", count, stop_time - start_time)
        # else:
            # only happens if running in CLI or tasks
            # dprint("_set_http_session_cache() called but NO http.request found!")
        return True

    def save_my_cache(self):
        """
        To be implemented by child classes.
        Allows them to add more cached data.
        """
        return

    def clear_cache(self):
        """
        clear all cached data, likely because we changed switches
        """
        dprint("clear_cache()")
        clear_switch_cache(self.request)
        # call child-class specific clear-clear_my_cache()
        self.clear_my_cache()
        return

    def clear_my_cache(self):
        """
        To be implemented by child classes.
        Allows them to override and clear their cached data.
        """
        return

    def set_cache_variable(self, name, value):
        """
        Store a variable 'name' in the session cache.
        By default, we use the HTTP request session to cache data.
        Returns True if set, False is an error occurs.

        Note: we access the session store via the request object.
        We could also access it direct, for possibly better performance:
        https://docs.djangoproject.com/en/3.1/topics/http/sessions/#session-serialization
        """
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

    def get_cache_variable(self, name):
        """
        Read a variable 'name' from the session cache.
        This returns the value if found, or None if not found.

        Note: we access the session store via the request object.
        We could also access it direct, for possibly better performance:
        https://docs.djangoproject.com/en/3.1/topics/http/sessions/#session-serialization
        """
        dprint(f"get_cache_variable(): {name}")
        if name in self.request.session.keys():
            dprint("   ... found!")
            return self.request.session[name]
        else:
            return None

    def clear_cache_variable(self, name):
        """
        remove variable from cache
        Returns True is succeeds, False is fails
        """
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

    def add_timing(self, name, count, time):
        """
        Function to track response time of the switch
        This add/updates self.timing {}, dictionary to track how long various calls
        take to read. Key = name, value = tuple(item_count, time)
        """
        self.timing[name] = (count, time)
        (total_count, total_time) = self.timing["Total"]
        total_count += count
        total_time += time
        self.timing["Total"] = (total_count, total_time)

    def add_more_info(self, category, name, value):
        """
        This adds specific pieces of information to the "General Info" tab.
        Items are ordered by category heading, then name/value pairs
        """
        if category not in self.more_info.keys():
            self.more_info[category] = {}
        self.more_info[category][name] = value

    def _can_manage_interface(self, iface):
        """
        Function meant to check if this interface can be managed.
        This allows for vendor-specific override in the vendor subclass, to detect e.g. stacking ports
        called from _set_interfaces_permissions() to check for each interface.
        Returns True by default, but if False, then _set_interfaces_permissions()
        will not allow any attribute of this interface to be managed (even then admin!)
        """
        return True

    def _set_allowed_vlans(self):
        """
        set the list of vlans defined on the switch that are allowed per the SwitchGroup.vlangroups/vlans
        self.vlans = {} dictionary of vlans on the current switch, i.e. Vlan() objects, but
        self.group.vlans and self.group.vlangroups is a list of allowed VLAN() Django objects (see switches/models.py)
        """
        dprint("_set_allowed_vlans()")
        # check the vlans on the switch (self.vlans) agains switchgroup.vlan_groups and switchgroup.vlans
        # if self.group.read_only and self.request and not self.request.user.is_superuser:
        if self.group.read_only or (self.request and self.request.user.profile.read_only):
            # Read-Only group or user, no vlan allowed!
            return
        for switch_vlan_id in self.vlans.keys():
            if self.request and (self.request.user.is_superuser or self.user.is_staff):
                self.allowed_vlans[int(switch_vlan_id)] = self.vlans[switch_vlan_id]
            else:
                # 'regular' user, first check the switchgroup.vlan_groups:
                found_vlan = False
                for vlan_group in self.group.vlan_groups.all():
                    for group_vlan in vlan_group.vlans.all():
                        if int(group_vlan.vid) == int(switch_vlan_id):
                            self.allowed_vlans[int(switch_vlan_id)] = self.vlans[switch_vlan_id]
                            found_vlan = True
                            continue
                # check if this switch vlan is in the list of allowed vlans
                if not found_vlan:
                    for group_vlan in self.group.vlans.all():
                        if int(group_vlan.vid) == int(switch_vlan_id):
                            # save using the switch vlan name, which is possibly different from the VLAN group name!
                            self.allowed_vlans[int(switch_vlan_id)] = self.vlans[switch_vlan_id]
                            continue
        return

    def _set_interfaces_permissions(self):
        """
        For all found interfaces, check out rules to see if this user should be able see or edit them
        """
        dprint("_set_interfaces_permissions()")
        switch = self.switch
        group = self.group
        if self.request:
            user = self.request.user
        else:
            # we are running as a task, simulate 'admin'
            # permissions were checked when form was generated/submitted
            user = User.objects.get(pk=1)

        # find allowed vlans for this user
        self._set_allowed_vlans()

        # apply the permission rules to all interfaces
        for key in self.interfaces:
            iface = self.interfaces[key]
            # dprint(f"  checking {iface.name}")

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
            if switch.read_only or group.read_only or user.profile.read_only:
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
            if settings.ALWAYS_ALLOW_POE_TOGGLE or switch.allow_poe_toggle or group.allow_poe_toggle or user.profile.allow_poe_toggle:
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
                iface.unmanage_reason = "Interface type is not visible!"    # should never show!
                continue

            # see if this regex matches the interface name, e.g. GigabitEthernetx/x/x
            if settings.IFACE_HIDE_REGEX_IFNAME != "":
                match = re.match(settings.IFACE_HIDE_REGEX_IFNAME, iface.name)
                if match:
                    iface.manageable = False  # match, so we cannot modify! Show anyway...
                    iface.unmanage_reason = "Access denied: interface name matches admin setting!"
                    continue

            # see if this regex matches the interface 'ifAlias' aka. the interface description
            if settings.IFACE_HIDE_REGEX_IFDESCR != "":
                match = re.match(settings.IFACE_HIDE_REGEX_IFDESCR, iface.description)
                if match:
                    iface.manageable = False  # match, so we cannot modify! Show anyway...
                    iface.unmanage_reason = "Access denied: interface description matches admin setting!"
                    continue

            # see if we should hide interfaces with speeds above this value in Mbps.
            if int(settings.IFACE_HIDE_SPEED_ABOVE) > 0 and int(iface.speed) > int(settings.IFACE_HIDE_SPEED_ABOVE):
                iface.manageable = False  # match, so we cannot modify! Show anyway...
                iface.unmanage_reason = "Access denied: interface speed is denied by admin setting!"
                continue

            # check if this vlan is in the group allowed vlans list:
            if int(iface.untagged_vlan) not in self.allowed_vlans.keys():
                iface.manageable = False  # match, so we cannot modify! Show anyway...
                iface.unmanage_reason = "Access denied: vlan is not allowed!"
                continue

            # finally, we can edit this interface!
            iface.manageable = True

        dprint("_set_interfaces_permissions() done!")
        return

    def add_warning(self, warning):
        """
        Add a warning to the list, and log it as well!
        """
        self.warnings.append(warning)
        # add a log message
        log = Log(group=self.group,
                  switch=self.switch,
                  ip_address=get_remote_ip(self.request),
                  type=LOG_TYPE_WARNING,
                  action=LOG_SNMP_ERROR,
                  description=warning)
        if self.request:
            log.user = self.request.user
        log.save()
        # done!
        return

    def log_error(self, error=False):
        """
        Log the current error, either passed in, or as set in the object.
        """
        err = False
        if error:
            err = error
        elif self.error.status:
            err = self.error
        if err:
            # add a log message
            log = Log(group=self.group,
                      switch=self.switch,
                      ip_address=get_remote_ip(self.request),
                      type=LOG_TYPE_ERROR,
                      action=LOG_SNMP_ERROR,
                      description=f"{self.error.description}: {self.error.details}")
            if self.request:
                log.user = self.request.user
                log.save()
        # done!
        return

    def add_vendor_data(self, category, name, value):
        """
        This adds a vendor specific piece of information to the "Info" tab.
        Items are ordered by category heading, then name/value pairs
        """
        vdata = VendorData(name, value)
        if category not in self.vendor_data.keys():
            self.vendor_data[category] = []
        self.vendor_data[category].append(vdata)

    def get_switch_vlans(self):
        """
        Return the vlans defined on this switch
        """
        return self.vlans

    def get_vlan_by_id(self, vlan_id):
        """
        Return the Vlan() object for the given id
        """
        if int(vlan_id) in self.vlans.keys():
            return self.vlans[vlan_id]
        return False

    def display_name(self):
        return f"{self.name} for {self.switch.name}"

    def __str__(self):
        return self.display_name

# --- End of Connector() ---


"""
We need one helper function, since we will need to clear the cache outside
the context of a class...
"""


def clear_switch_cache(request):
    """
    Clear all cached data for the current switch.
    Does not return anything.
    """
    dprint("clear_switch_cache() called:")
    if request:
        # all we have to do it clear the "switch_id" !
        if 'switch_id' in request.session:
            del request.session["switch_id"]
            request.session.modified = True
        # if not found, we had not selected a switch before. ie upon login!
