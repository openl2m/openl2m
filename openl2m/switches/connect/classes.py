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
import netaddr

from django.conf import settings

"""
All the generic classes we use to represent
switch vlans, switch interfaces, switch neighbor devices, etc.
"""
from switches.connect.constants import (
    ENTITY_CLASS_NAME,
    IF_TYPE_NONE,
    IF_DUPLEX_UNKNOWN,
    LACP_IF_TYPE_NONE,
    VLAN_ADMIN_ENABLED,
    VLAN_STATUS_OTHER,
    VLAN_STATUS_PERMANENT,
    VLAN_STATUS_DYNAMIC,
    VLAN_TYPE_NORMAL,
    LLDP_CAPABILITIES_NONE,
    POE_PSE_STATUS_ON,
    POE_PSE_STATUS_OFF,
    POE_PSE_STATUS_FAULT,
    POE_PORT_DETECT_SEARCHING,
    duplex_name,
    poe_admin_status_name,
    #    poe_priority_name,
    poe_pse_status_name,
    poe_status_name,
    vlan_admin_name,
    vlan_status_name,
)
from switches.utils import dprint, get_ip_dns_name


class Error:
    """
    Simple error information object, created with error status indicated!
    """

    def __init__(self):
        """
        Default state is error occured!
        """
        self.status = True
        self.description = "An Unknown Error Occured!"  # simple description of error
        self.details = ""  # more details about the error, typically a 'traceback'

    def clear(self):
        """
        Clear error status
        """
        self.status = False  # True if error
        self.description = ""  # simple description of error
        self.details = ""  # more details about the error, typically a 'traceback'


class StackMember:
    """
    Represents what we know about a single device entity that is part of the switch stack.
    This could be just one unit (single switch), or multiple if part of a stack
    """

    def __init__(self, id, type):
        """
        Initialize the object
        """
        self.id = id
        self.type = type  # see ENTITY_CLASS_NAME
        self.serial = ""  # serial number
        self.version = ""  # software revision of this device
        self.model = ""  # vendor model number
        self.info = ""  # hardware info string

    def as_dict(self):
        '''
        return this class as a dictionary for use by the API
        '''
        return {
            'id': self.id,
            'type': ENTITY_CLASS_NAME[self.type],
            'serial': self.serial,  # this needs work to get a string return!
            'version': self.version,
            'model': self.model,
            'info': self.info,
        }


class VendorData:
    """
    Class to hold generic Vendor-specific data, represented by
    data name and value. this can be added to any device with a call to
    connector.add_vendor_data(self, category, name, value)
    This gets added to connector.vendor_data{} with category as key.
    """

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def as_dict(self):
        '''
        return this class as a dictionary for use by the API
        '''
        return {
            'name': self.name,
            'value': self.value,
        }


class IPNetworkHostname(netaddr.IPNetwork):
    """
    Class to add a 'hostname' attribute to an IPNetwork() object.
    This can be used to set a FQDN for the Ip address portion of the network.
    """

    def __init__(self, network):
        self.hostname = ''
        super().__init__(network)

    def resolve_ip_address(self):
        '''Use dns resolution to resolve the IP address to a hostname.'''
        # if hostname not already set:
        if not self.hostname:
            self.hostname = get_ip_dns_name(self.ip)


class Interface:
    """
    Class to represent all the attributes of a single device (switch) interface.
    """

    def __init__(self, key):
        """
        Initialize the object. We map the MIB-II entity names to similar class attributes.
        """
        self.key = str(key)  # the key used to find the index in the connector.interfaces{} dict
        self.visible = True  # if True, this user can "see" this interface
        self.manageable = False  # if True, this interface is manageable by the current user
        self.disabled = False  # if True, this interface is disabled by the Connector() driver.
        self.unmanage_reason = "Access denied!"  # string with reason why interface is not manageable or disabled
        self.can_edit_description = False  # if True, can change interface description (snmp ifAlias)
        self.index = key  # ifIndex, the key to all MIB-2 data!
        # self.ifDescr = ""           # the old name of the interface, NOT the "description" attribute which is the ifAlias !!!
        self.name = ""  # the name from IFMIB ifName entry! Falls back to older MIB-2ifDescr is not found!
        self.type = IF_TYPE_NONE  # ifType, the MIB-2 type of the interface
        self.is_routed = False  # if True interface is in routed mode (i.e. a layer 3 interface)
        self.admin_status = False  # administrative status of the interface, True is Admin-Up (snmp ifAdminStatus)
        self.oper_status = False  # operation status of interface, True is Oper-Up (snmp ifOperStatus)
        self.mtu = 0  # ifMTU value, for L3 interfaces
        self.speed = 0  # speed counter, in 1 Mbps (ie. like ifHighSpeed data from IF-MIB)
        self.duplex = IF_DUPLEX_UNKNOWN  # interface duplex setting, if known.
        self.phys_addr = 0x0
        self.description = ""  # the interface description, as set by the switch configuration, from IF-MIB
        self.addresses_ip4 = {}  # dictionary of all my ipv4 addresses on this interface
        self.addresses_ip6 = {}  # dictionary of all my ipv6 addresses on this interface
        self.igmp_snooping = False  # if True, interface does IGMP snooping
        # vlan related
        self.port_id = -1  # Q-Bridge MIB port id
        self.untagged_vlan = -1  # the vlan id of the interface in untagged mode. This is invalid if tagged/trunked !
        self.vlans = []  # list (array) of vlanId's on this interface. If size > 0 this is a tagged port!
        self.vlan_count = 0
        self.is_tagged = False  # if 802.1q tagging or trunking is enabled
        self.if_vlan_mode = -1  # some vendors (e.g. Comware) have a interface vlan mode, such as access, trunk, hybrid
        self.voice_vlan = 0  # Cisco specific "Voice Vlan"
        self.can_change_vlan = True  # if set, we can change the vlan; some device types this is not implemented yet!
        self.gvrp_enabled = False  # the value representing the status of MVRP/GVRP on the interface
        self.last_change = 0  # ifLastChange, tick count since uptime when interface last changed
        # LACP related
        self.lacp_type = LACP_IF_TYPE_NONE
        # for LACP aggregator, a dictionary of lacp member interfaces. key=ifIndex, value=ifName of member interfaces
        self.lacp_admin_key = -1  # "LacpKey" admin key. Member interfaces map back to this.
        self.lacp_members = {}
        # for members:
        self.lacp_master_index = (
            -1
        )  # we are member of an LACP interface. ifIndex of the master aggregate. Mutually exclusive with above!
        self.lacp_master_name = ""  # we are member of an LACP interface. ifname of the master aggregate.
        # Power related
        self.poe_entry = False  # if interface has PoE capabilities, will be a PoePort() object
        self.allow_poe_toggle = False  # if set, any user can toggle PoE OFF-ON
        # a variety of data about what is happening on this interface:
        self.eth = {}  # heard ethernet address on this interface, dictionay of EthernetAddress() objects
        self.lldp = {}  # LLDP neighbors, dictionay of NeighborDevice() objects

    def add_ip4_network(self, address, prefix_len=''):
        '''
        Add an IPv4 address to this interface, as given by the IPv4 address and prefix_len
        It gets stored in the form of a netaddr.IPNetwork() object, indexed by addres.
        return True on success, False on failure.
        '''
        if prefix_len:
            self.addresses_ip4[address] = IPNetworkHostname(f"{address}/{prefix_len}")
        else:
            self.addresses_ip4[address] = IPNetworkHostname(address)
        if settings.LOOKUP_HOSTNAME_ROUTED_IP:
            self.addresses_ip4[address].resolve_ip_address()
        return True

    def add_ip6_network(self, address, prefix_len):
        '''
        Add an IPv6 address to this interface, as given by the IPv6 address and prefix_len
        It gets stored in the form of a netaddr.IPNetwork() object, indexed by addres.
        return True on success, False on failure.
        '''
        self.addresses_ip6[address] = IPNetworkHostname(f"{address}/{prefix_len}")
        if settings.LOOKUP_HOSTNAME_ROUTED_IP:
            self.addresses_ip6[address].resolve_ip_address()
        return True

    def add_tagged_vlan(self, vlan_id):
        '''
        Add a Vlan() object for the vlan_id to this interface. Set tagged mode as well.
        vlan_id = vlan to add as integer
        Return True on success, False on failure and sets error variable.
        '''
        self.is_tagged = True
        self.vlans.append(vlan_id)
        return True

    def remove_tagged_vlan(self, vlan_id):
        '''
        Remove a Vlan() object from this interface.
        vlan_id = vlan to remove as integer
        Return True on success, False on failure and sets error variable.
        '''
        if vlan_id in self.vlans:
            self.vlans.remove(vlan_id)
        return True

    def add_learned_ethernet_address(self, eth_address, vlan_id=-1, ip4_address=''):
        '''
        Add an ethernet address to this interface, as given by the layer2 CAM/Switching tables.
        It gets stored indexed by address. Create new EthernetAddress() object is not found yet.
        If the object already exists, return it.

        Args:
            eth_address(str): ethernet address as string.
            vlan_id(int): the vlan this ethernet address was heard on.

        Returns:
            EthernetAddress(), either existing or new.
        '''
        dprint(f"Interface().add_learned_ethernet_address() for {eth_address}, vlan={vlan_id}, ip4={ip4_address}")
        if eth_address in self.eth.keys():
            # already known!
            dprint("  Eth already known!")
            if vlan_id > 0:
                self.eth[eth_address].set_vlan(vlan_id)
            if ip4_address:
                self.eth[eth_address].set_ip4_address(ip4_address)
            return self.eth[eth_address]
        else:
            # add the new ethernet address
            dprint("  New ethernet, adding.")
            a = EthernetAddress(eth_address)
            if vlan_id > 0:
                a.set_vlan(vlan_id)
            if ip4_address:
                a.set_ip4_address(ip4_address)
            self.eth[eth_address] = a
            return a

    def add_neighbor(self, neighbor):
        '''
        Add an lldp neighbor to this interface.
        neighbor = NeighborDevice() object.
        It gets stored indexed by lldp "index", mostly for snmp purposes.
        return True on success, False on failure.
        '''
        dprint(f"add_neighbor() for {str(neighbor)}")
        self.lldp[neighbor.index] = neighbor
        return True

    def as_dict(self):
        '''
        return this class as a dictionary for use by the API
        '''
        inf = {}
        inf["id"] = self.key
        inf["name"] = self.name
        inf["description"] = self.description
        if self.is_routed:
            inf["mode"] = "Routed"
        elif self.is_tagged:
            inf['mode'] = "Tagged"
            # need to handle tagged vlans
            inf["tagged_vlans"] = ", ".join(map(str, self.vlans))
        else:
            inf["mode"] = "Access"
        if self.untagged_vlan > 0:
            inf["vlan"] = self.untagged_vlan
        if self.admin_status:
            inf["state"] = "Enabled"
        else:
            inf["state"] = "Disabled"
        if self.oper_status:
            inf["online"] = True
        else:
            inf["online"] = False
        if self.speed:
            inf["speed"] = self.speed
        inf["duplex"] = duplex_name[self.duplex]
        if self.mtu:
            inf["mtu"] = self.mtu
        # PoE data:
        if self.poe_entry:
            inf['poe'] = self.poe_entry.as_dict()
        inf['manageable'] = self.manageable
        if not self.manageable:
            inf['unmanage_reason'] = self.unmanage_reason

        # add the learned mac addresses:
        addresses = []
        for address, eth in self.eth.items():
            addresses.append(eth.as_dict())
        inf['ethernet_addresses'] = addresses

        # add the heard neighbors:
        neighbors = []
        for key, neighbor in self.lldp.items():
            neighbors.append(neighbor.as_dict())
        inf['neighbors'] = neighbors

        # and return the dictionary:
        return inf

    def display_name(self):
        s = self.name  # use the IF-MIB new interface name
        if self.description:
            s = f"{s}: {self.description} {self.admin_status} {self.oper_status}"
        if self.admin_status:
            s = f"{s} (UP/"
        else:
            s = f"{s} (DOWN/"
        if self.oper_status:
            s = f"{s}UP)"
        else:
            s = f"{s}DOWN)"
        return s

    def __str__(self):
        return self.display_name()


class Vlan:
    """
    Class to represent a vlan found on the switch
    """

    def __init__(self, id=0, index=0, name=''):
        """
        Vlan() requires passing in the vlan id
        """
        self.id = id  # the vlan ID as sent on the wire
        self.index = index  # the internal vlan index, used by some MIBs
        self.fdb_index = 0  # the Forward-DB index, from maps switch database to vlan index
        self.name = name
        self.type = VLAN_TYPE_NORMAL  # mostly used for Cisco vlans, to avoid the 1000-1003 range
        self.admin_status = VLAN_ADMIN_ENABLED  # ENABLED or DISABLED
        self.status = VLAN_STATUS_OTHER  # 1-other-0, 2-permanent, 3-dynamic(gvrp)
        self.igmp_snooping = False  # if True, vlan does IGMP snooping
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

    def as_dict(self):
        '''
        return this class as a dictionary for use by the API
        '''
        return {
            'id': self.id,
            'name': self.name,
            'state': vlan_admin_name[self.admin_status],
            'status': vlan_status_name[self.status],
            'igmp_snooping': self.igmp_snooping,
        }

    def __str__(self):
        return self.display_name()


class PortList:
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


class EthernetAddress(netaddr.EUI):
    """
    Class to represents an Ethernet address, and whatever we know about it.
    We reuse most of the netaddr library abilities to find vendor.
    """

    def __init__(self, ethernet_string):
        """
        EthernetAddress() requires passing in the hyphen or colon format of the 6 ethernet bytes.
        """
        # initiate netaddr EUI class parent object
        super().__init__(ethernet_string)
        self.vendor = ''
        self.vlan_id = 0  # the vlan id (number) this was heard on, if known
        self.address_ip4 = ""  # ipv4 address from arp table, if known
        self.address_ip6 = ""  # ipv6 address, if known
        self.hostname = ""  # reverse lookup for ip4 or ip6 address.

    def set_vlan(self, vlan_id):
        self.vlan_id = int(vlan_id)

    def set_ip4_address(self, ip4_address):
        self.address_ip4 = ip4_address

    def set_ip6_address(self, ip6_address):
        self.address_ip6 = ip6_address

    def as_dict(self):
        '''
        return this class as a dictionary for use by the API
        '''
        return {
            'address': self.__str__(),
            'vlan': self.vlan_id,
            'ipv4': self.address_ip4,
            'ipv6': self.address_ip6,
            'hostname': self.hostname,
        }

    def __str__(self):
        """
        Print the ethernet string, formatted per the settings value.
        """
        self.dialect = settings.MAC_DIALECT
        return super().__str__()


class NeighborDevice:
    """
    Class to represents an lldp neighbor, and whatever we know about it.
    """

    # def __init__(self, lldp_index, if_index):
    def __init__(self, lldp_index):
        """
        Initialize the object, requires the lldp index
        """
        self.index = lldp_index  # 'string' remainder of OID that is unique per remote device
        # self.if_index = int(if_index)
        # the above can be set from lldp data via SNMP, when these three fields are found:
        self.chassis_type = 0  # integer, LldpChassisIdSubtype.
        # If chassis_string_type is set to IANA_TYPE_IPV4 or IANA_TYPE_IPV6, then
        # chassis_string is assumed to be a string with the IP4/6 address set.
        self.chassis_string_type = 0
        self.chassis_string = ""  # LldpChassisId, OctetString format depends on type.
        self.capabilities = LLDP_CAPABILITIES_NONE
        # self.capabilities = bytes(2)  # init to 2 0-bytes bitmap of device capabilities, see LLDP mib
        #                               # this is the equivalent to LLDP_CAPABILITIES_NONE from connect.constants
        self.port_name = ""  # remote port name
        self.port_descr = ""  # remote port description, as set by config
        self.sys_name = "Unknown Device"
        self.sys_descr = "Unknown Device Description"
        self.hostname = ""  # if set, the hostname of the device, possibly resolved from chassis_string

    def set_port_name(self, port_name):
        '''
        Set the name of the remote port of this device.

        Args:
            port_name(str): the port on the remote device that we are connected to.

        Returns:
            none
        '''
        self.port_name = port_name

    def set_port_description(self, description):
        '''
        Set the description of the remote port of this device.

        Args:
            description(str): the description port on the remote device that we are connected to.

        Returns:
            none
        '''
        self.port_descr = description

    def set_sys_name(self, name):
        '''
        Set the name of the remote device.

        Args:
            name(str): the name of the remote device that we are connected to.

        Returns:
            none
        '''
        self.sys_name = name

    def set_sys_description(self, description):
        '''
        Set the description of the remote device.

        Args:
            description(str): the description of the remote device that we are connected to.

        Returns:
            none
        '''
        self.sys_descr = description

    def set_chassis_type(self, chassis_type):
        '''
        Set the name of the remote port of this device.

        Args:
            type(int): the type on the remote device that we are connected to.
            valid values are defined in snmp.constants, see LLDP_CHASSIC_TYPE_xxx fields.

        Returns:
            none
        '''
        self.chassis_type = chassis_type

    def set_chassis_string(self, description):
        '''
        Set the string type of remote chassis.

        Args:
            description(str): the description type of the chassis device that we are connected to.

        Returns:
            none
        '''
        self.chassis_string = description

    def set_capability(self, capability):
        '''
        Add a capability to this device. These are defined in switches.connect.constants,
        see LLDP_CAPABILITIES_xxx fields. They are accumulative, as a device can have
        multiple capabilities.

        Args:
            capacility: as defined above.

        Returns:
            none
        '''
        self.capabilities += capability

    def as_dict(self):
        '''
        return this class as a dictionary for use by the API
        '''
        return {
            'port_name': self.port_name,
            'port_description': self.port_descr,
            'system_name': self.sys_name,
            'system_description': self.sys_descr,
            'hostname': self.hostname,
            # need to handle capabilities, etc.
            'capabilities': "TBD",
        }

    def display_name(self):
        return self.sys_name

    def __str__(self):
        return self.display_name()


class PoePSE:
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
        self.max_power = 0  # maximum power available on this power supply
        self.status = POE_PSE_STATUS_ON
        self.power_consumed = 0  # total power consumed on this power supply
        self.threshold = 0

    def as_dict(self):
        '''
        return this class as a dictionary for use by the API
        '''
        return {
            'id': self.index,
            'max_power': self.max_power,
            'status': poe_pse_status_name[self.status],
            'power_consumed': self.power_consumed,
            'threshold': self.threshold,
        }

    def set_enabled(self):
        '''
        Set status as Enabled.
        '''
        self.status = POE_PSE_STATUS_ON

    def set_disabled(self):
        '''
        Set status as Disabled.
        '''
        self.status = POE_PSE_STATUS_OFF

    def set_fault(self):
        '''
        Set status as Faulted.
        '''
        self.status = POE_PSE_STATUS_FAULT

    def set_max_power(self, power):
        '''
        Set maximum power available.
        '''
        try:
            self.max_power = int(power)
        except Exception:
            self.max_power = 0

    def set_consumed_power(self, power):
        '''
        Set power consumed.
        '''
        try:
            self.power_consumed = int(power)
        except Exception:
            self.consumed_power = 0

    def display_name(self):
        return f"PS #{self.index}"

    def __str__(self):
        return self.display_name()

    #    return (f"PoePSE:\nIndex={self.index}\nStatus={self.status}\n" \
    #            "Max Power={self.max_power}\nPower Draw={self.power_consumed}\n" \
    #            "Threshold={self.threshold}\n"


class PoePort:
    """
    Class to represent a "pethPsePortEntry" for an interface.
    I.e. this is the per-interface power information.
    """

    def __init__(self, index, admin_status):
        """
        Initialize the object
        """
        self.index = index  # port entry is the value after the PoE OID that is the index to this interface
        self.admin_status = admin_status
        self.detect_status = POE_PORT_DETECT_SEARCHING
        """ currently not used:
        self.priority = 0
        self.description = ""       # rarely used, but available in POE MIB
        """
        # power consumed is not in the standard PoE MIB, but some proprietary MIBs support this (e.g. Cisco)
        self.power_consumption_supported = False
        self.power_consumed = 0  # power consumed in milliWatt
        self.power_available = 0  # power available in milliWatt
        self.max_power_consumed = 0  # max power drawn since PoE reset, in milliWatt

    def as_dict(self):
        '''
        return this class as a dictionary for use by the API
        '''
        return {
            'admin_status': poe_admin_status_name[self.admin_status],
            'detect_status': poe_status_name[self.detect_status],
            # 'priority': poe_priority_name[self.priority]
            'power_consumption_supported': self.power_consumption_supported,
            'power_consumed': self.power_consumed,
            'power_available': self.power_available,
            'max_power_consumed': self.max_power_consumed,
        }

    def __str__(self):
        return (
            f"PoePort:\nIndex={self.index}\nAdmin={self.admin_status}\n"
            "Detect={self.detect_status}\n"
            "Power Draw Supported={self.power_consumption_supported}\n"
            "Power Draw={self.power_consumed}\n"
        )


class SyslogMsg:
    """
    Class to represent a Syslog Message, implemented in SYSLOG-MSG-MIB
    or vendorm-specific mibs like CISCO-SYSLOG-MIB
    """

    def __init__(self, index):
        """
        Initialize the object with the message index
        """
        self.index = index  # snmp table index
        self.facility = ""  # some name
        self.severity = -1  # valid are 0-7
        self.name = ""  # type or name or app-name of message
        self.message = ""  # the text of the message
        # datetime() value of message. Generic SYSLOG-MSG-MIB has time "string" (DateAndTime)
        # some vendor mibs have sys-uptime timetick. Recalculate all to datetime() object
        self.datetime = 0

    def as_dict(self):
        '''
        return this class as a dictionary for use by the API
        '''
        return {
            'index': self.index,
            'facility': self.facility,
            'severity': self.severity,
            'name': self.name,
            'message': self.message,
            'datetime': self.datetime,
        }

    def __str__(self):
        return self.message  # for now.
