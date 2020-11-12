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

"""
All the generic classes we use to represent
switch vlans, switch interfaces, switch neighbor devices, etc.
"""
from switches.models import Log
from switches.constants import *
from switches.connect.constants import *
from switches.connect.oui.oui import get_vendor_from_oui
from switches.connect.utils import *
from switches.utils import *


class Error():
    """
    Simple error information object, created with error status indicated!
    """
    def __init__(self):
        """
        Default state is error occured!
        """
        self.status = True
        self.description = "An Unknown Error Occured!"  # simple description of error
        self.details = "No details known!"      # more details about the error, typically a 'traceback'

    def clear(self):
        """
        Clear error status
        """
        self.status = False    # True if error
        self.description = ""  # simple description of error
        self.details = ""      # more details about the error, typically a 'traceback'


class StackMember():
    """
    Represents what we know about a single device entity that is part of the switch stack.
    This could be just one unit (single switch), or multiple if part of a stack
    """
    def __init__(self, id, type):
        """
        Initialize the object
        """
        self.id = id
        self.type = type        # see ENTITY_CLASS_NAME
        self.serial = ""        # serial number
        self.version = ""       # software revision of this device
        self.model = ""         # vendor model number


LACP_IF_TYPE_NONE = 0        # not port of LACP aggregation
LACP_IF_TYPE_MEMBER = 1      # this is a physical port and member
LACP_IF_TYPE_AGGREGATOR = 2  # this is an aggregator port (Port-Channel or Bridge-Aggregation)


class Interface():
    """
    Class to represent all the attributes of a single switch interface.
    """
    def __init__(self, key):
        """
        Initialize the object. We map the MIB-II entity names to similar class attributes.
        """
        self.key = str(key)         # the key used to find the index in the connector.interfaces{} dict
        self.visible = True         # if True, this user can "see" this interface
        self.manageable = False      # if True, this interface is manageable by the current user
        self.unmanage_reason = "Access denied!"     # string with reason why interface is not manageable
        self.can_edit_alias = False  # if True, can change alias, aka interface description
        self.index = key            # ifIndex, the key to all MIB-2 data!
        # self.ifDescr = ""           # the old name of the interface, NOT the "description" attribute which is the ifAlias !!!
        self.name = ""              # the name from IFMIB ifName entry! Falls back to older MIB-2ifDescr is not found!
        self.type = IF_TYPE_NONE    # ifType, the MIB-2 type of the interface
        self.is_routed = False      # if True interface is in routed mode (i.e. a layer 3 interface)
        self.admin_status = IF_ADMIN_STATUS_DOWN    # ifAdminStatus, administrative status of the interface
        self.oper_status = IF_OPER_STATUS_DOWN      # ifOperStatus, operation status of interface
        self.mtu = 0                # ifMTU value, for L3 interfaces
        self.speed = 0              # speed counter, in 1 Mbps (ie. like ifHighSpeed data from IF-MIB)
        self.phys_addr = 0x0
        self.alias = ""             # the interface description, as set by the switch configuration, from IF-MIB
        self.addresses_ip4 = {}     # dictionary of all my ipv4 addresses on this interface
        self.addresses_ip6 = {}     # dictionary of all my ipv6 addresses on this interface
        # vlan related
        self.port_id = -1            # Q-Bridge MIB port id
        self.untagged_vlan = -1      # the vlan id of the interface in untagged mode. This is invalid if tagged/trunked !
        self.vlans = []              # list (array) of vlanId's on this interface. If size > 0 this is a tagged port!
        self.vlan_count = 0
        self.is_tagged = False       # if 802.1q tagging or trunking is enabled
        self.if_vlan_mode = -1       # some vendors (e.g. Comware) have a interface vlan mode, such as access, trunk, hybrid
        self.voice_vlan = 0          # Cisco specific "Voice Vlan"
        self.can_change_vlan = True  # if set, we can change the vlan; some device types this is not implemented yet!
        self.gvrp_enabled = False    # the value representing the status of MVRP/GVRP on the interface
        self.last_change = 0         # ifLastChange, tick count since uptime when interface last changed
        # LACP related
        self.lacp_type = LACP_IF_TYPE_NONE
        # for LACP aggregator, a dictionary of lacp member interfaces. key=ifIndex, value=ifName of member interfaces
        self.lacp_admin_key = -1      # "LacpKey" admin key. Member interfaces map back to this.
        self.lacp_members = {}
        # for members:
        self.lacp_master_index = -1  # we are member of an LACP interface. ifIndex of the master aggregate. Mutually exclusive with above!
        self.lacp_master_name = ""   # we are member of an LACP interface. ifname of the master aggregate.
        # Power related
        self.poe_entry = False          # if interface has PoE capabilities, will be a PoePort() object
        self.allow_poe_toggle = False   # if set, any user can toggle PoE OFF-ON
        # a variety of data about what is happening on this interface:
        self.eth = {}               # heard ethernet address on this interface, dictionay of EthernetAddress() objects
        self.lldp = {}              # LLDP neighbors, dictionay of NeighborDevice() objects
        self.arp4 = {}              # ARP table entries for ipv4, dictionay of IP4Address() objects

    def display_name(self):
        s = self.name   # use the IF-MIB new interface name
        if self.alias:
            s = f"{s}: {self.alias} {self.admin_status} {self.oper_status}"
        if self.admin_status == IF_ADMIN_STATUS_DOWN:
            s = f"{s} (DOWN/"
        else:
            s = f"{s} (UP/"
        if self.oper_status == IF_OPER_STATUS_DOWN:
            s = f"{s}DOWN)"
        else:
            s = f"{s}UP)"
        return s

    def __str__(self):
        return self.display_name()


class Vlan():
    """
    Class to represent a vlan found on the switch
    """
    def __init__(self, id=0, index=0):
        """
        Vlan() requires passing in the vlan id
        """
        self.id = id            # the vlan ID as sent on the wire
        self.index = index      # the internal vlan index, used by some MIBs
        self.fdb_index = 0      # the Forward-DB index, from maps switch database to vlan index
        self.name = ""
        self.type = VLAN_TYPE_NORMAL  # mostly used for Cisco vlans, to avoid the 1000-1003 range
        self.status = VLAN_STATUS_OTHER     # 1-other-0, 2-permanent, 3-dynamic(gvrp)
        # dot1qVlanCurrentEgressPorts OCTETSTRING stored as PortList() object with bitmap of egress ports in this vlan
        self.current_egress_portlist = PortList()
        # dot1qVlanStaticPorts OCTETSTRING stored as PortList() object with bitmap of egress ports in this vlan
        # self.static_egress_portlist = PortList()
        # self.untagged_ports_bitmap = 0x0    # exactly what you think, PortList format ! :-)
        # self.hh3c_dot1q_vlan_ports = PortList()   # hh3cdot1qVlanPorts is HH3C specific vlan untagged PortList() bitmap

    def set_name(self, name):
        self.name = name

    def display_name(self):
        if self.name:
            return self.name
        return str(self.id)

    def __str__(self):
        return self.display_name()


class PortList():
    """
    Object to handle the Q-BRIDGE PortList bitmap that exists per vlan.
    This is the back-and-forth mapping of switch port to bit
    in a stream of bits . This is snmp type OCTETSTRING
    Mostly a copy of the BitVector() class from NAV

    :param bitmap_string: a Unicode encoded string of bytes representing
                          the bitmap that represents switch ports on a vlan.
                          This is the PortList OCTETSTRING returned by the
                          snmp get() call
    """
    def __init__(self):
        self.portlist = array.array('B')

    def from_unicode(self, bitmap_string):
        """
        Initialize the bytes from this unicode bitmap string
        """
        for byte in bitmap_string:
            self.portlist.append(ord(byte))

    def from_byte_count(self, bytecount):
        """
        Initialize by setting a number of bytes to 0
        """
        dprint(f"PortList bytecount size={bytecount}")
        for i in range(int(bytecount)):
            self.portlist.append(0)

    def tobytes(self):
        """
        call the array.tobytes() function to return
        """
        return self.portlist.tobytes()

    def to_unicode(self):
        """
        Encode the bytes as unicode, since the EasySnmp library, and the
        underlying net-snmp want OCTETSTRING variables as Unicode strings,
        so encode as such

        :return: the string of bytes, encoded as Unicode('utf-8'), as needed
                 by the snmp set() call for snmp type OCTETSTRING
        """
        return self.portlist.tobytes().decode(encoding="UTF-8", errors="ignore")

    def to_hex_string(self):
        """
        Return a hexadecimal string representation of this bitmap.

        :return: a hexadecimal string representing the bytes of this bitmap.
        """
        digits = ["%02x" % octet for octet in self.portlist]
        return "".join(digits)

    def reverse_bits_in_bytes(self):
        """
        Reverse all bits in each byte. I.e. bit 8 goes to 1, 7 to 2, etc.
        There is probably a much more efficient way to do this!
        """
        offset = 0
        for octet in self.portlist:
            new_octet = 0
            if octet & 128:
                new_octet += 1
            if octet & 64:
                new_octet += 2
            if octet & 32:
                new_octet += 4
            if octet & 16:
                new_octet += 8
            if octet & 8:
                new_octet += 16
            if octet & 4:
                new_octet += 32
            if octet & 2:
                new_octet += 64
            if octet & 1:
                new_octet += 128
            self.portlist[offset] = new_octet
            offset += 1

    def __len__(self):
        return len(self.portlist) * 8

    def __repr__(self):
        """
        Handle the "string" representation
        """
        return f"{self.__class__.__name__}({repr(self.to_hex_string())})"

    def __setitem__(self, position, value):
        """
        Set the bit in position position to val.  NOTE: The most
        significant bit is regarded as bit 0 in this context.
        """
        # NOTE: bit 0 = port_id 1. First byte is ports 1-8, second 9-16, etc.
        dprint(f"PortList __setitem__ pos={position}, val={value}")
        position -= 1
        value = value and 1 or 0
        block = position // 8
        shift = position & 7
        dprint(f"PortList position={position} value={value} block={block} shift={shift}")
        block_value = self.portlist[block]
        if (block_value << shift) & 128 and 1 or 0 != value:
            if value:
                self.portlist[block] = block_value | (128 >> shift)
            else:
                self.portlist[block] = block_value ^ (128 >> shift)

    def __getitem__(self, position):
        """
        Get the value of the bit in position.  NOTE: The most
        significant bit is regarded as bit 0 in this context.
        """
        dprint(f"PortList __getitem__ pos={position}")
        position -= 1
        if isinstance(position, slice):
            result = []
            for i in range(*position.indices(len(self))):
                result.append(self[i])
            return result
        else:
            block = position // 8
            shift = position & 7
            return (self.portlist[block] << shift) & 128 and 1 or 0


class IP4Address():
    """
    Class to represent an IPv4 address
    """
    def __init__(self, ip, netmask="255.255.255.255"):
        """
        Initialize the object
        """
        self.ip = ip
        self.netmask = netmask
        self.cyder_bits = 32
        self.if_index = 0

    def set_netmask(self, netmask):
        self.netmask = netmask
        # set bits as well
        self.cyder_bits = (sum([bin(int(bits)).count("1") for bits in self.netmask.split(".")]))

    def set_if_index(self, if_index):
        self.if_index = if_index

    def display_name(self):
        return self.ip + "/" + self.netmask

    def __str__(self):
        return self.display_name()


class EthernetAddress():
    """
    Class to represents an Ethernet address, and whatever we know about it.
    """
    def __init__(self, ethernet_string):
        """
        EthernetAddress() requires passing in the "colon-string" value the 6 ethernet bytes.
        """
        self.display_address = ethernet_string
        self.vendor = self.get_vendor()
        self.vlan_id = 0        # the vlan id (number) this was heard on, if known
        self.address_ip4 = ""   # ipv4 address from arp table, if known
        self.address_ip6 = ""   # ipv6 address, if known

    def get_vendor(self):
        """
        Lookup the vendor OUI, first 3 bytes
        """
        return get_vendor_from_oui(ethernet_to_oui(self.display_address))

    def display_name(self):
        return self.display_address

    def __str__(self):
        return self.display_name()


class NeighborDevice():
    """
    Class to represents an lldp neighbor, and whatever we know about it.
    """
    # def __init__(self, lldp_index, if_index):
    def __init__(self, lldp_index):
        """
        Initialize the object, requires the lldp index and ifIndex
        """
        self.index = lldp_index     # 'string' remainder of OID that is unique per remote device
        # self.if_index = int(if_index)
        # descriptive field about the chassis, likely ethernet or ip info:
        self.chassis_info = ""
        # the above can be set from lldp data via SNMP, when these three fields are found:
        self.chassis_type = 0    # integer, LldpChassisIdSubtype
        self.chassis_string = ""        # LldpChassisId, OctetString format depends on type.
        self.capabilities = bytes(2)    # init to 2 0-bytes bitmap of device capabilities, see LLDP mib
        self.port_descr = ""     # remote port description, as set by config
        self.sys_name = "Unknown Device"
        self.sys_descr = "Unknown Device Description"

    def display_name(self):
        return self.sys_name

    def __str__(self):
        return self.display_name()


class PoePSE():
    """
    Class to represent a Power Source Entity aka PSE device. (ie a power supply! :-)
    This is the device that feeds PoE to ports. Typically, modular switches or
    stacks have multiple, e.g. one per line card or stack unit.
    """
    def __init__(self, index):
        """
        Initialize the object
        """
        self.index = int(index)
        self.max_power = 0          # maximum power available on this power supply
        self.status = POE_PSE_STATUS_OFF
        self.power_consumed = 0     # total power consumed on this power supply
        self.threshold = 0

    def display_name(self):
        return f"PSE #{self.index}"

    def __str__(self):
        return self.display_name()
    #    return (f"PoePSE:\nIndex={self.index}\nStatus={self.status}\n" \
    #            "Max Power={self.max_power}\nPower Draw={self.power_consumed}\n" \
    #            "Threshold={self.threshold}\n"


class PoePort():
    """
    Class to represent a "pethPsePortEntry" for an interface.
    I.e. this is the per-interface power information.
    """
    def __init__(self, index, admin_status):
        """
        Initialize the object
        """
        self.index = index          # port entry is the value after the PoE OID that is the index to this interface
        self.admin_status = admin_status
        self.detect_status = POE_PORT_DETECT_SEARCHING
        """ currently not used:
        self.priority = 0
        self.description = ""       # rarely used, but available in POE MIB
        """
        # power consumed is not in the standard PoE MIB, but some proprietary MIBs support this (e.g. Cisco)
        self.power_consumption_supported = False
        self.power_consumed = 0      # power consumed in milliWatt
        self.power_available = 0     # power available in milliWatt
        self.max_power_consumed = 0  # max power drawn since PoE reset, in milliWatt

    def __str__(self):
        return (f"PoePort:\nIndex={self.index}\nAdmin={self.admin_status}\n"
                "Detect={self.detect_status}\n"
                "Power Draw Supported={self.power_consumption_supported}\n"
                "Power Draw={self.power_consumed}\n")


class SyslogMsg():
    """
    Class to represent a Syslog Message, implemented in SYSLOG-MSG-MIB
    or vendorm-specific mibs like CISCO-SYSLOG-MIB
    """
    def __init__(self, index):
        """
        Initialize the object with the message index
        """
        self.index = index      # snmp table index
        self.facility = ""      # some name
        self.severity = -1      # valid are 0-7
        self.name = ""          # type or name or app-name of message
        self.message = ""       # the text of the message
        # datetime() value of message. Generic SYSLOG-MSG-MIB has time "string" (DateAndTime)
        # some vendor mibs have sys-uptime timetick. Recalculate all to datetime() object
        self.datetime = 0

    def __str__(self):
        return (self.message)   # for now.


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

        self.name = "Generic Connector"  # what type of class is running!
        self.hostname = ""      # system hostname, typically set in sub-class
        self.vendor_name = ""   # typically set in sub-classes

        # data we collect and potentially cache:
        self.interfaces = {}        # Interface() objects representing the ports on this switch, key is if_name
        self.vlans = {}             # Vlan() objects on this switch, key is vlan id (not index!)
        self.ip4_to_if_index = {}   # the IPv4 addresses as keys, with stored value if_index; needed to map netmask to interface
        self.syslog_msgs = {}       # list of Syslog messages, if any
        self.syslog_max_msgs = 0    # how many syslog msgs device will store
        # some flags:
        self.save_needed = False    # set this flag if a save aka. 'write mem' is needed:
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
        self.poe_port_entries = {}  # PoePort() port power entries, used to store until we can map to interface

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
    These are the high level "viewing" interfaces.
    These are called by the switches.view functions to display data.
    """

    def get_switch_basic_info(self):
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
        # set this to the time the switch data was actually read,
        # including when this may have been read before it got cached:
        if not self.cache_loaded:
            # we need to read the device class:
            self.basic_info_read_timestamp = time.time()

            self.get_my_basic_info()

            # update the time it took to read the basic info when it was first read:
            self.basic_info_read_duration = int((time.time() - self.basic_info_read_timestamp) + 0.5)

            # you have to set the permissions to the interfaces:
            self._set_interfaces_permissions()

            self.add_more_info('System', 'Hostname', self.name)

            # and save the switch cache:
            self.save_cache()

        return True

    def get_my_basic_info(self):
        """
        placeholder for class-specific implementation to read Interfaces() etc.
        return True on success, False on error and set self.error variables
        """
        return True

    def get_switch_client_data(self):
        """
        This loads the layer 2 switch tables, any ARP tables available,
        and LLDP neighbor data.
        Not intended to be cached, so we get fresh, "live" data anytime called!
        return True on success, False on error and set self.error variables
        """
        start_time = time.time()
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

    def get_switch_hardware_details(self):
        """
        Get all (possible) hardware info, stacking details, etc.
        return True on success, False on error and set self.error variables
        """

        # call the vendor-specific data first, if implemented
        self.get_my_hardware_details()

        # set the flag to indicate we read this already, and store in session
        # if flag is set, the button will not be shown in menu bar!
        self.hwinfo_needed = False
        # and cache it:
        self.save_cache()
        return True

    def get_my_hardware_details(self):
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
    These are the functions that implement changes on the device.
    This needs to be implement by the device/vendor specific class.
    """

    def set_interface_admin_status(self, interface, new_state):
        """
        set the interface to the requested state (up or down)
        interface = Interface() object for the requested port
        new_state = IF_ADMIN_STATUS_UP or IF_ADMIN_STATUS_DOWN
        return True on success, False on error and set self.error variables
        """
        # interface.admin_status = new_state
        dprint(f"Connector.set_interface_admin_status() for {interface.name} to {new_state}")
        self.interfaces[interface.key].admin_status = int(new_state)
        self.save_cache()
        return True

    def set_interface_description(self, interface, description):
        """
        set the interface description (aka. alias) to the string
        interface = Interface() object for the requested port
        new_alias = a string with the requested text
        return True on success, False on error and set self.error variables
        """
        dprint(f"Connector.set_interface_description() for {interface.name}")
        self.interfaces[interface.key].description = description
        self.save_cache()
        return True

    def set_interface_untagged_vlan(self, interface, new_pvid):
        """
        set the interface untagged vlan to the given vlan
        interface = Interface() object for the requested port
        new_pvid = an integer with the requested untagged vlan
        return True on success, False on error and set self.error variables
        """
        dprint(f"Connector.set_interface_untagged_vlan() for {interface.name} to vlan {new_pvid}")
        self.interfaces[interface.key].untagged_vlan = new_pvid
        self.save_cache()
        return True

    def add_interface_tagged_vlan(self, interface, new_vlan):
        """
        add a tagged vlan to the interface trunk.
        interface = Interface() object for the requested port
        new_vlan = an integer with the requested tagged vlan
        return True on success, False on error and set self.error variables
        """
        return True

    def remove_interface_tagged_vlan(self, interface, old_vlan):
        """
        remove a tagged vlan from the interface trunk.
        interface = Interface() object for the requested port
        old_vlan = an integer with the tagged vlan to removes
        return True on success, False on error and set self.error variables
        """
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
            self.interfaces[interface.key].poe_entry.admin_status = int(new_state)
            dprint("   PoE set OK")
            if new_state == POE_PORT_ADMIN_DISABLED:
                self.interfaces[interface.key].poe_entry.power_consumed = 0
            self.save_cache()
        return True

    def add_interface_learned_ethernet(self, if_key, ethernet_address):
        """
        add an learned/heard EthernetAddress()) object to the interface.eth{} dictionary.
        """
        return

    def add_interface_neighbor(self, if_key, ethernet_address):
        """
        add and EthernetAddress) object to the interface.eth{} dictionary.
        """
        return

    #############################
    # various support functions #
    #############################

    def add_interface(self, interface):
        """
        Add and Interface() object to the self.interfaces{} dictionary,
        indexed by the interface key.
        return True on success, False on error and set self.error variables
        """
        self.interfaces[interface.key] = interface
        return True

    def get_interface_by_key(self, key):
        """
        get an Interface() object from out self.interfaces{} dictionary,
        search based on the key that was used when it was added.
        return Interface() if found, False if not found.
        """
        key = str(key)
        dprint(f"get_interface_by_key() for '{key}'")
        if key in self.interfaces.keys():
            return self.interfaces[key]
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
        if value:
            if self.can_save_config():
                self.set_cache_variable("save_needed", True)
            # else:
            #    dprint("   save config NOT supported")
        else:
            self.clear_cache_variable("save_needed")
        return True

    def get_save_needed(self):
        """
        Does the switch need to execute a 'save config' command
        to save changes to the startup config.
        We store and read this from the http session.
        Returns True or False
        """
        val = self.get_cache_variable("save_needed")
        if val is None:
            return False
        return val

    def can_save_config(self):
        """
        Does the switch have the ability (or need) to execute a 'save config'
        or 'write memory' as it known on many platforms. This should be overwritten
        in a vendor-specific sub-class. We just return False here.
        Returns True or False
        """
        return False

    def can_change_interface_vlan(self):
        """
        Return True if we can change a vlan on an interface, False if not
        """
        return False

    def save_running_config(self):
        """
        Vendor-agnostic interface to save the current config to startup
        To be implemented by sub-classes, eg CISCO-SNMP, H3C-SNMP
        Returns True is this succeeds. On Failure, set self.error() and
        return False
        NOTE: does NOT clear 'save-needed' flag.
        Upstream needs to call self.set_save_needed(False)
        """
        return True

    def save_running_config(self):
        """
        Execute a 'save config' command. This is switch dependent.
        To be implemented by sub-classes, eg CISCO-SNMP, H3C-SNMP
        Returns 0 is this succeeds, -1 on failure. self.error() will be set in that case
        """
        self.error.status = True
        self.error.description = "Not implemented!"
        return -1

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
                        dprint("   Found!")
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

    def load_cache_OLD(self):
        """
        Load cached data to improve performance.
        Returns True if cache was read and variables set.
        False if this fails, primarily when the switch id is not correct!
        """
        dprint("load_cache()")
        switch_id = self.get_cache_variable("switch_id")
        # is the cached data for the current switch ?
        if switch_id == self.switch.id:
            # Yes - read it
            dprint("load_cache() for current switch!")
            self.hwinfo_needed = self.get_cache_variable("hwinfo_needed")
            self.timing = self.get_cache_variable("timing")
            self.save_needed = self.get_save_needed()
            self.basic_info_read_timestamp = self.get_cache_variable("basic_info_read_timestamp")
            self.basic_info_read_duration = self.get_cache_variable("basic_info_read_duration")

            self.poe_capable = self.get_cache_variable("poe_capable")
            self.poe_enabled = self.get_cache_variable("poe_enabled")
            self.poe_max_power = self.get_cache_variable("poe_max_power")
            self.poe_power_consumed = self.get_cache_variable("poe_power_consumed")

            self.poe_pse_devices = self.get_cache_variable("poe_pse_devices")
            self.poe_port_entries = self.get_cache_variable("poe_port_entries")
            self.interfaces = self.get_cache_variable("interfaces")
            dprint(f"READ YAML interfaces: {self.interfaces}")
            for (key, iface) in self.interfaces.items():
                dprint(f"    Interface: {key} => {iface.name}")

            self.vlans = self.get_cache_variable("vlans")
            self.allowed_vlans = self.get_cache_variable("allowed_vlans")
            self.ip4_to_if_index = self.get_cache_variable("ip4_to_if_index")
            self.syslog_msgs = self.get_cache_variable("syslog_msgs")
            self.stack_members = self.get_cache_variable("stack_members")
            self.more_info = self.get_cache_variable("more_info")

            # now give child-classes opportunity to load cache
            self.load_my_cache()

            self.cache_loaded = True
            return True
        else:
            # wrong switch id, i.e. we changed switches, clear session data!
            dprint("load_cache() for new switch! so clearing cache...")
            self.clear_cache()
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
        dprint("save_cache()")
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

    def save_cache_OLD(self):
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
        dprint("save_cache()")
        # for name, value in self.__dict__.items():
        #    dprint(f"dict caching:  { name }")

        if self.request:

            # can I cache myself ?
            for attr_name in self.__dict__:
                dprint(f"Caching Attrib = {attr_name}")

            self.set_cache_variable("switch_id", self.switch.id)
            self.set_cache_variable("basic_info_read_timestamp", self.basic_info_read_timestamp)
            self.set_cache_variable("basic_info_read_duration", self.basic_info_read_duration)
            self.set_cache_variable("hwinfo_needed", self.hwinfo_needed)
            self.set_cache_variable("timing", self.timing)

            self.set_cache_variable("poe_capable", self.poe_capable)
            self.set_cache_variable("poe_enabled", self.poe_enabled)
            self.set_cache_variable("poe_max_power", self.poe_max_power)
            self.set_cache_variable("poe_power_consumed", self.poe_power_consumed)
            self.set_cache_variable("poe_pse_devices", self.poe_pse_devices)
            self.set_cache_variable("poe_port_entries", self.poe_port_entries)

            self.set_cache_variable("interfaces", self.interfaces)
            self.set_cache_variable("vlans", self.vlans)
            self.set_cache_variable("allowed_vlans", self.allowed_vlans)
            self.set_cache_variable("ip4_to_if_index", self.ip4_to_if_index)
            self.set_cache_variable("syslog_msgs", self.syslog_msgs)
            self.set_cache_variable("stack_members", self.stack_members)
            self.set_cache_variable("more_info", self.more_info)

            # call the child-class specific save_my_cache()
            self.save_my_cache()
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
        if self.group.read_only and self.request and not self.request.user.is_superuser:
            # Read-Only Group, no vlan allowed!
            return
        for switch_vlan_id in self.vlans.keys():
            if self.request and self.request.user.is_superuser:
                self.allowed_vlans[int(switch_vlan_id)] = self.vlans[switch_vlan_id]
            else:
                # first the switchgroup.vlan_groups:
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

            # Layer 3 (routed mode) interfaces are denied (but shown)!
            if iface.is_routed:
                iface.manageable = False
                iface.allow_poe_toggle = False
                iface.can_edit_alias = False
                iface.visible = True
                iface.unmanage_reason = "Access denied: interface in routed mode!"
                continue

            if iface.type != IF_TYPE_ETHERNET and settings.HIDE_NONE_ETHERNET_INTERFACES:
                iface.manageable = False
                iface.allow_poe_toggle = False
                iface.can_edit_alias = False
                iface.visible = False
                continue

            # next check vendor-specific restrictions. This allows denying Stacking ports, etc.
            if not self._can_manage_interface(iface):
                iface.manageable = False
                iface.allow_poe_toggle = False
                iface.can_edit_alias = False
                iface.visible = True
                continue

            # Read-Only switch cannot be overwritten, not even by SuperUser!
            if switch.read_only or group.read_only or user.profile.read_only:
                iface.manageable = False
                iface.unmanage_reason = "Access denied: Read-Only"
                iface.visible = True
                continue

            # super-users have access to all other attributes of interfaces!
            if user.is_superuser:
                iface.manageable = True
                iface.visible = True
                iface.allow_poe_toggle = True
                iface.can_edit_alias = True
                continue

            # globally allow PoE toggle:
            if settings.ALWAYS_ALLOW_POE_TOGGLE:
                iface.allow_poe_toggle = True

            # we can also enable PoE toggle on user, group or switch, if allowed somewhere:
            if switch.allow_poe_toggle or group.allow_poe_toggle or user.profile.allow_poe_toggle:
                iface.allow_poe_toggle = True

            # we can also modify interface description, if allowed everywhere:
            if switch.edit_if_descr and group.edit_if_descr and user.profile.edit_if_descr:
                iface.can_edit_alias = True

            # Next apply any rules that HIDE first !!!

            # check interface types first, only show ethernet
            # this hides vlan, loopback etc. interfaces for the regular user.
            if iface.type not in visible_interfaces.keys():
                iface.visible = False
                iface.manageable = False  # just to be safe :-)
                iface.unmanage_reason = "Switch is not visible!"    # should never show!
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
                match = re.match(settings.IFACE_HIDE_REGEX_IFDESCR, iface.alias)
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
                  action=LOG_WARNING_SNMP_ERROR,
                  description=warning)
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
        dprint("   http request found!")
        # all we have to do it clear the "switch_id" !
        try:
            del request.session["switch_id"]
            request.session.modified = True
        except Exception:
            # this means we did not have anything set, we can ignore!
            dprint("   cached 'switch_id' cleared (not found!)")
