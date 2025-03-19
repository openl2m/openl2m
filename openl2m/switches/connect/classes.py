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
from typing import Dict, List

from django.conf import settings
from django.utils.encoding import iri_to_uri

from rest_framework import status as http_status

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
    VLAN_TYPE_NORMAL,
    POE_PSE_STATUS_ON,
    POE_PSE_STATUS_OFF,
    POE_PSE_STATUS_FAULT,
    POE_PORT_DETECT_SEARCHING,
    IANA_TYPE_OTHER,
    #   IANA_TYPE_IPV4,
    #   IANA_TYPE_IPV6,
    duplex_name,
    poe_admin_status_name,
    #    poe_priority_name,
    poe_pse_status_name,
    poe_status_name,
    vlan_admin_name,
    vlan_status_name,
    LLDP_CAPABILITIES_OTHER,
    LLDP_CAPABILITIES_REPEATER,
    LLDP_CAPABILITIES_BRIDGE,
    LLDP_CAPABILITIES_WLAN,
    LLDP_CAPABILITIES_ROUTER,
    LLDP_CAPABILITIES_PHONE,
    LLDP_CAPABILITIES_DOCSIS,
    LLDP_CAPABILITIES_STATION,
    LLDP_CAPABILITIES_NONE,
    IPV6_LINK_LOCAL_NETWORK,
)
from switches.utils import dprint, get_ip_dns_name, string_is_int


class Error:
    """
    Simple error information object, created with error status indicated!
    """

    def __init__(
        self,
        status: bool = True,
        code: int = http_status.HTTP_400_BAD_REQUEST,
        description: str = "An Unknown Error Occured!",
        details: str = "",
    ):
        """
        Default state is error occured!
        """
        self.status: bool = status  # True if error, False if not.
        self.code: int = code
        self.description: str = description  # simple description of error
        self.details: str = details  # more details about the error, typically a 'traceback'

    def clear(self):
        """
        Clear error status
        """
        self.status = False  # True if error
        self.code = http_status.HTTP_200_OK
        self.description = ""  # simple description of error
        self.details = ""  # more details about the error, typically a 'traceback'


class StackMember:
    """
    Represents what we know about a single device entity that is part of the switch stack.
    This could be just one unit (single switch), or multiple if part of a stack
    """

    def __init__(self, id: int, type: int):
        """
        Initialize the object
        """
        self.id: int = id
        self.type: int = type  # see ENTITY_CLASS_NAME
        self.serial: str = ""  # serial number
        self.version: str = ""  # software revision of this device module
        self.model: str = ""  # vendor model number
        self.info: str = ""  # hardware info string
        self.description: str = ""  # module description

    def as_dict(self) -> dict:
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
            'description': self.description,
        }


class VendorData:
    """
    Class to hold generic Vendor-specific data, represented by
    data name and value. this can be added to any device with a call to
    connector.add_vendor_data(self, category, name, value)
    This gets added to connector.vendor_data{} with category as key.
    """

    def __init__(self, name: str, value: str):
        self.name: str = name
        self.value = value

    def as_dict(self) -> dict:
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

    def __init__(self, network: netaddr.IPNetwork):
        self.hostname: str = ''
        super().__init__(network)

    def resolve_ip_address(self) -> None:
        '''Use dns resolution to resolve the IP address to a hostname.'''
        # if hostname not already set:
        if not self.hostname:
            self.hostname = get_ip_dns_name(self.ip)


class Vlan:
    """
    Class to represent a vlan found on the switch
    """

    def __init__(self, id: int = 0, index: int = 0, name: str = ''):
        """
        Vlan() requires passing in the vlan id
        """
        self.id: int = id  # the vlan ID as sent on the wire
        self.index: int = index  # the internal vlan index, used by some MIBs
        self.fdb_index: int = 0  # the Forward-DB index, from maps switch database to vlan index
        self.name: str = name
        self.type: int = VLAN_TYPE_NORMAL  # mostly used for Cisco vlans, to avoid the 1000-1003 range
        self.admin_status: int = VLAN_ADMIN_ENABLED  # ENABLED or DISABLED
        self.status: int = VLAN_STATUS_OTHER  # 1-other-0, 2-permanent, 3-dynamic(gvrp)
        self.igmp_snooping: bool = False  # if True, vlan does IGMP snooping
        # dot1qVlanCurrentEgressPorts OCTETSTRING stored as PortList() object with bitmap of egress ports in this vlan
        self.current_egress_portlist: PortList = PortList()
        # dot1qVlanStaticPorts OCTETSTRING stored as PortList() object with bitmap of egress ports in this vlan
        # self.static_egress_portlist = PortList()
        # self.untagged_ports_bitmap = 0x0    # exactly what you think, PortList format ! :-)
        # self.hh3c_dot1q_vlan_ports = PortList()   # hh3cdot1qVlanPorts is HH3C specific vlan untagged PortList() bitmap
        self.voice: bool = False  # if True, this is a "voice vlan"
        self.vrf: str = ""  # the VRF this vlan is a member of, if any.

    def set_name(self, name: str) -> None:
        self.name = name

    def display_name(self) -> str:
        if self.name:
            return self.name
        return str(self.id)

    def as_dict(self) -> dict:
        '''
        return this class as a dictionary for use by the API
        '''
        return {
            'id': self.id,
            'name': self.name,
            'state': vlan_admin_name[self.admin_status],
            'status': vlan_status_name[self.status],
            'igmp_snooping': self.igmp_snooping,
            'vrf': self.vrf,
        }

    def __str__(self) -> str:
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

    def from_unicode(self, bitmap_string: str) -> None:
        """
        Initialize the bytes from this unicode bitmap string
        """
        for byte in bitmap_string:
            self.portlist.append(ord(byte))

    def from_byte_count(self, bytecount: int) -> None:
        """
        Initialize by setting a number of bytes to 0
        """
        dprint(f"PortList bytecount size={bytecount}")
        for i in range(int(bytecount)):
            self.portlist.append(0)

    def tobytes(self) -> bytes:
        """
        call the array.tobytes() function to return
        """
        return self.portlist.tobytes()

    def to_unicode(self) -> str:
        """
        Encode the bytes as unicode, since the EasySnmp library, and the
        underlying net-snmp want OCTETSTRING variables as Unicode strings,
        so encode as such

        :return: the string of bytes, encoded as Unicode('utf-8'), as needed
                 by the snmp set() call for snmp type OCTETSTRING
        """
        return self.portlist.tobytes().decode(encoding="UTF-8", errors="ignore")

    def to_hex_string(self) -> str:
        """
        Return a hexadecimal string representation of this bitmap.

        :return: a hexadecimal string representing the bytes of this bitmap.
        """
        digits = ["%02x" % octet for octet in self.portlist]
        return "".join(digits)

    def reverse_bits_in_bytes(self) -> None:
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

    def __len__(self) -> int:
        return len(self.portlist) * 8

    def __repr__(self) -> str:
        """
        Handle the "string" representation
        """
        return f"{self.__class__.__name__}({repr(self.to_hex_string())})"

    def __setitem__(self, position: int, value: int) -> None:
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

    def __getitem__(self, position: int) -> int:
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

    def __init__(self, ethernet_string: str):
        """
        EthernetAddress() requires passing in the hyphen or colon format of the 6 ethernet bytes.
        """
        # initiate netaddr EUI class parent object
        super().__init__(ethernet_string)
        self.vendor: str = ''
        self.vlan_id: int = 0  # the vlan id (number) this was heard on, if known
        self.address_ip4: str = ""  # ipv4 address as str() from arp table, if known
        self.address_ip6: List = []  # known ipv6 addresses of this ethernet address, in list as str()
        self.address_ip6_linklocal: str = ""  # IPv6 Link-Local address for this ethernet address, if any.
        self.hostname: str = ""  # reverse lookup for ip4 or ip6 address.

    def set_vlan(self, vlan_id: int) -> None:
        self.vlan_id = int(vlan_id)

    def set_ip4_address(self, ip4_address: str) -> None:
        """Set the IPv4 address for this ethernet address."""
        self.address_ip4 = ip4_address

    def add_ip6_address(self, ip6_address: str) -> None:
        """Add an IPv6 address to the list of addresses for this ethernet address.
        If Link-Local is given, will set the self.ip6_address_linklocal property,
        else will add to self.address_ip6 Dict() indexed by address as key.

        Args:
            ip6_address (str): string representing the IPv6 address for this ethernet address

        Returns:
            n/a
        """
        dprint(f"EthernetAddress() adding IPv6 address '{ip6_address}'")

        # need to add logic to recognize IPv6 link-local "FE80::/10" subnets.
        # we do no check validity of the address at this time.
        if settings.IPV6_USE_UPPER:
            ipv6 = ip6_address.upper()
        else:
            ipv6 = ip6_address.lower()
        try:
            # validate format
            ipv6 = IPNetworkHostname(network=f"{ip6_address}/64")
            # and check if this is Link-Local address
            if ipv6 in IPV6_LINK_LOCAL_NETWORK:
                dprint("   IS LINK-LOCAL!")
                self.address_ip6_linklocal = ip6_address
            else:
                self.address_ip6.append(ip6_address)
        except Exception as err:
            dprint(f"EthernetAddress() object: adding INVALID IPv6 address '{ip6_address}': {err}")

    def as_dict(self) -> dict:
        '''
        return this class as a dictionary for use by the API
        '''
        return {
            'address': self.__str__(),
            'vlan': self.vlan_id,
            'ipv4': self.address_ip4,
            'ipv6': self.address_ip6,
            'hostname': self.hostname,
            'vendor': self.vendor,
        }

    def __str__(self) -> str:
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
    def __init__(self, lldp_index: str):
        """
        Initialize the object, requires the lldp index
        """
        self.index: str = lldp_index  # 'string' remainder of OID that is unique per remote device
        # self.if_index = int(if_index)
        # the above can be set from lldp data via SNMP, when these three fields are found:
        self.chassis_type: int = 0  # integer, LldpChassisIdSubtype.
        # If chassis_string_type is set to IANA_TYPE_IPV4 or IANA_TYPE_IPV6, then
        # chassis_string is assumed to be a string with the IP4/6 address set.
        self.chassis_string_type: int = 0
        self.chassis_string: str = ""  # LldpChassisId, OctetString format depends on type.
        self.vendor: str = ""  # if chassis-string is ethernet address, this is the OUI vendor.
        self.capabilities: int = LLDP_CAPABILITIES_NONE
        # self.capabilities = bytes(2)  # init to 2 0-bytes bitmap of device capabilities, see LLDP mib
        #                               # this is the equivalent to LLDP_CAPABILITIES_NONE from connect.constants
        self.port_name: str = ""  # remote port name
        self.port_descr: str = ""  # remote port description, as set by config
        self.sys_name: str = "Unknown Device"
        self.sys_descr: str = "Unknown Device Description"
        self.hostname: str = ""  # if set, the hostname of the device, possibly resolved from chassis_string
        self.management_address_type: int = IANA_TYPE_OTHER  # valid is either IANA_TYPE_IPV4 or IANA_TYPE_IPV6
        self.management_address: str = ""  # IP address, either v4 or v6
        #
        # the entries below are for use by the mermaid.js graphing library to show neighbors in an image
        # these are assigned in switches.templatetags.helpers.get_neighbor_mermaid_config()
        #
        self.name = ""  # the device name to display
        self.chassis = ""  # chassis description, if any
        self.icon = ""  # the FontAwesome icon to show on the device block
        self.style = ""  # mermaid display style
        self.description = ""  # device type description, Wifi, Router, Switch etc.
        # these are the graphing block "start" and "finish" formatting characters
        self.start_device = ""
        self.stop_device = ""

    def set_port_name(self, port_name: str) -> None:
        '''
        Set the name of the remote port of this device.

        Args:
            port_name(str): the port on the remote device that we are connected to.

        Returns:
            none
        '''
        self.port_name = port_name

    def set_port_description(self, description: str) -> None:
        '''
        Set the description of the remote port of this device.

        Args:
            description(str): the description port on the remote device that we are connected to.

        Returns:
            none
        '''
        self.port_descr = description

    def set_sys_name(self, name: str) -> None:
        '''
        Set the name of the remote device.

        Args:
            name(str): the name of the remote device that we are connected to.

        Returns:
            none
        '''
        self.sys_name = name

    def set_sys_description(self, description: str) -> None:
        '''
        Set the description of the remote device.

        Args:
            description(str): the description of the remote device that we are connected to.

        Returns:
            none
        '''
        self.sys_descr = description

    def set_chassis_type(self, chassis_type: int) -> None:
        '''
        Set the name of the remote port of this device.

        Args:
            chassis_type(int): the type on the remote device that we are connected to.
            valid values are defined in snmp.constants, see LLDP_CHASSIC_TYPE_xxx fields.

        Returns:
            none
        '''
        self.chassis_type = chassis_type

    def set_chassis_string(self, description: str) -> None:
        '''
        Set the string type of remote chassis.

        Args:
            description(str): the description type of the chassis device that we are connected to.

        Returns:
            none
        '''
        self.chassis_string = description

    def set_management_address(self, address: str, type: int) -> None:
        """Set remote device management address.

        Args:
            address (str): the management address
            type (int): the address type, a valid IANA protocol number, either IANA_TYPE_IPV4, or IANA_TYPE_IPV6

        """
        dprint(f"NeighborDevice().set_management_address('{address}', type {type})")
        self.management_address = address
        self.management_address_type = type

    def set_capability(self, capability: int) -> None:
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

    def capabilities_as_string(self) -> str:
        """Return a string respresenting the capabilities of the lldp neighbor.

        Args:
            self: the current object

        Returns:
            (str): names of capabilies of this neighbor.
        """
        info = []
        if self.capabilities == LLDP_CAPABILITIES_NONE:
            info.append('NOT Advertized')
        else:
            if self.capabilities & LLDP_CAPABILITIES_WLAN:
                info.append('Wireless AP')
            if self.capabilities & LLDP_CAPABILITIES_PHONE:
                info.append('VOIP Phone')
            if self.capabilities & LLDP_CAPABILITIES_ROUTER:
                info.append('Router or Switch')
            if self.capabilities & LLDP_CAPABILITIES_STATION:
                info.append('Workstation or Server')
            if (
                self.capabilities & LLDP_CAPABILITIES_BRIDGE
                and not self.capabilities & LLDP_CAPABILITIES_ROUTER
                and not self.capabilities & LLDP_CAPABILITIES_PHONE
            ):
                # We only show Switch if no routing or phone capabilities listed.
                # Most phones and routers also show switch capabilities.
                # In those cases we only show the above Router or Phone icons!
                info.append('Switch')
            if self.capabilities & LLDP_CAPABILITIES_REPEATER:
                info.append('Hub or Repeater')
            if self.capabilities & LLDP_CAPABILITIES_DOCSIS:
                info.append('Cable-Modem')  # unlikely to see this!
            if self.capabilities & LLDP_CAPABILITIES_OTHER:
                info.append('Other')
        return ','.join(info)

    def as_dict(self) -> dict:
        '''
        return this class as a dictionary for use by the API
        '''
        return {
            'port_name': self.port_name,
            'port_description': self.port_descr,
            'system_name': self.sys_name,
            'system_description': self.sys_descr,
            'hostname': self.hostname,
            'chassis_id': self.chassis_string,
            'chassis_type': self.chassis_type,
            'capabilities': self.capabilities_as_string(),
            'management_address': self.management_address,
        }

    def display_name(self) -> str:
        return self.sys_name

    def __str__(self) -> str:
        return self.display_name()


class PoePSE:
    """
    Class to represent a Power Source Entity aka PSE device. (ie a power supply! :-)
    This is the device that feeds PoE to ports. Typically, modular switches or
    stacks have multiple, e.g. one per line card or stack unit.
    """

    def __init__(self, index: int):
        """
        Initialize the object
        """
        self.index: int = int(index)
        self.max_power: int = 0  # maximum power available on this power supply, in watts
        self.status: int = POE_PSE_STATUS_ON
        self.power_consumed: int = 0  # total power consumed on this power supply, in watts
        self.threshold: int = 0
        # some drivers have this easily available:
        self.name = ""
        self.description = ""
        self.model = ""
        self.part_number = ""
        self.serial = ""

    def as_dict(self) -> dict:
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

    def set_enabled(self) -> None:
        '''
        Set status as Enabled.
        '''
        self.status = POE_PSE_STATUS_ON

    def set_disabled(self) -> None:
        '''
        Set status as Disabled.
        '''
        self.status = POE_PSE_STATUS_OFF

    def set_fault(self) -> None:
        '''
        Set status as Faulted.
        '''
        self.status = POE_PSE_STATUS_FAULT

    def set_max_power(self, power: int) -> None:
        '''
        Set maximum power available.
        '''
        try:
            self.max_power = int(power)
        except Exception:
            self.max_power = 0

    def set_consumed_power(self, power: int) -> None:
        '''
        Set power consumed.
        '''
        try:
            self.power_consumed = int(power)
        except Exception:
            self.consumed_power = 0

    def add_consumed_power(self, power: int) -> None:
        '''
        Add to the consumed power consumed.
        Args:
            power (int): the consumed power, in WATTS!

        Returns:
            n/a
        '''
        try:
            self.power_consumed += int(power)
        except Exception:
            dprint(f"add_consumed_power(): INVALID argument '{power}'")

    def display_name(self) -> str:
        return f"PS #{self.index}"

    def __str__(self) -> str:
        return self.display_name()

    #    return (f"PoePSE:\nIndex={self.index}\nStatus={self.status}\n" \
    #            "Max Power={self.max_power}\nPower Draw={self.power_consumed}\n" \
    #            "Threshold={self.threshold}\n"


class PoePort:
    """
    Class to represent a "pethPsePortEntry" for an interface.
    I.e. this is the per-interface power information.
    """

    def __init__(self, index: str, admin_status: int):
        """
        Initialize the object
        """
        self.index: str = index  # port entry is the value after the PoE OID that is the index to this interface
        self.admin_status: int = admin_status
        self.detect_status: int = POE_PORT_DETECT_SEARCHING
        """ currently not used:
        self.priority = 0
        self.description = ""       # rarely used, but available in POE MIB
        """
        # power consumed is not in the standard PoE MIB, but some proprietary MIBs support this (e.g. Cisco)
        self.power_consumption_supported: bool = False
        self.power_consumed: int = 0  # power consumed in milliWatt
        self.power_available: int = 0  # power available in milliWatt
        self.max_power_consumed: int = 0  # max power drawn since PoE reset, in milliWatt

    def as_dict(self) -> dict:
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

    def __str__(self) -> str:
        return (
            f"PoePort:\nIndex={self.index}\nAdmin={self.admin_status}\n"
            "Detect={self.detect_status}\n"
            "Power Draw Supported={self.power_consumption_supported}\n"
            "Power Draw={self.power_consumed}\n"
        )


class Transceiver:
    """
    Class to represent a transceiver in an interface slot. Eg. QSFP28 100g-LR4, etc.
    """

    def __init__(self):
        """
        Initialize the object
        """
        self.type: str = ""  # the type of transceiver, eg. SFP, SFP+, 10G-LR, 40G-SR4, 400G-LR4, etc.
        self.vendor: str = ""
        self.model: str = ""
        self.description: str = ""
        self.serial: str = ""
        self.wavelength: int = 0  # the wavelength in nm, ie 850, 130, 1550, etc.
        self.distance: int = 0  # the max distance of this transceiver
        self.connector: str = ""  # 'LC', SC', etc.

    def as_dict(self) -> dict:
        '''
        return this class as a dictionary for use by the API
        '''
        return {
            'type': self.type,
            'vendor': self.vendor,
            'model': self.model,
            'description': self.description,
            'serial': self.serial,
            'wavelength': self.wavelength,
            'distance': self.distance,
            'connector': self.connector,
        }

    def __str__(self) -> str:
        """String representation of this Transceiver() object.
        This is shows in the HTML template in _tpl_if_type_icons.html, since it uses "{{ transceiver }} transceiver"
        """

        if self.wavelength:
            if string_is_int(self.wavelength):
                wavelength = f" {self.wavelength}nm"
            else:
                wavelength = f" {self.wavelength}"
        else:
            wavelength = ""
        if self.vendor:
            vendor = f" ({self.vendor})"
        else:
            vendor = ""
        if self.distance:
            d = self.distance / 1000
            distance = f"{d}km"
        else:
            distance = ""
        # what do we show for the type of optics?
        if self.type:
            name = self.type
        elif self.model:
            name = self.model
        else:
            name = "Unknown"
        return f"{name}{wavelength}{distance}{vendor}"


class SyslogMsg:
    """
    Class to represent a Syslog Message, implemented in SYSLOG-MSG-MIB
    or vendorm-specific mibs like CISCO-SYSLOG-MIB
    """

    def __init__(self, index: int):
        """
        Initialize the object with the message index
        """
        self.index: int = index  # snmp table index
        self.facility: str = ""  # some name
        self.severity: int = -1  # valid are 0-7
        self.name: str = ""  # type or name or app-name of message
        self.message: str = ""  # the text of the message
        # datetime() value of message. Generic SYSLOG-MSG-MIB has time "string" (DateAndTime)
        # some vendor mibs have sys-uptime timetick. Recalculate all to datetime() object
        self.datetime = 0

    def as_dict(self) -> dict:
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

    def __str__(self) -> str:
        return self.message  # for now.


class Vrf:
    """
    Class to represent a VRF (Virtual Routing and Forwarding instance) that exists on the device.
    """

    def __init__(self, name: str = "", rd: str = "", description: str = "", ipv4: bool = False, ipv6: bool = False):
        """
        Initialize the VRF object

        Params:
            name (str): the name of the VRF.
            rd (str): the Route Distinguisher, as a string.
            description (str): the VRF description.
            ipv4 (bool): if True, this VRF is used for IPv4 routing.
            ipv6 (bool): if True, this VRF is used for IPv6 routing.
        """
        self.name = name
        self.rd = rd  # vrf route distinguisher
        self.description = description
        # self.state      # enable or disabled, VRF_ACTIVE or VRF_INACTIVE
        self.ipv4 = ipv4  # True if VRF is enabled for IPv4
        self.ipv6 = ipv6  # True if VRF is enabled for IPv6
        self.active_interfaces = 0  # number of interfaces active on this VRF
        self.interfaces = []  # list of interface names in this VRF

    def add_interface(name: str = ""):
        """Add an interface name to the dict of interfaces in this vrf."""
        if name:
            self.interfaces.append(name)
        # return

    def as_dict(self):
        '''
        return this Vrf() class as a dictionary for use by the API

        Params:
            None.

        Returns:
            dict(): key-value pairs with information about this VRF.
        '''
        # return just the basic data for now...
        return {
            "name": self.name,
            'rd': self.rd,
            'description': self.description,
            'ipv4': self.ipv4,
            'ipv6': self.ipv6,
        }


class Interface:
    """
    Class to represent all the attributes of a single device (switch) interface.
    """

    def __init__(self, key: str):
        """
        Initialize the object. We map the MIB-II entity names to similar class attributes.
        """
        self.key: str = str(key)  # the key used to find the index in the connector.interfaces{} dict
        self.visible: bool = True  # if True, this user can "see" this interface
        self.manageable: bool = False  # if True, this interface is manageable by the current user
        self.disabled: bool = False  # if True, this interface is disabled by the Connector() driver.
        self.unmanage_reason: str = "Access denied!"  # string with reason why interface is not manageable or disabled
        self.can_edit_description: bool = False  # if True, can change interface description (snmp ifAlias)
        self.index = key  # ifIndex, the key to all MIB-2 data!
        # self.ifDescr = ""           # the old name of the interface, NOT the "description" attribute which is the ifAlias !!!
        self.name: str = ""  # the name from IFMIB ifName entry! Falls back to older MIB-2ifDescr is not found!
        self.type: int = IF_TYPE_NONE  # ifType, the MIB-2 type of the interface
        self.is_routed: bool = False  # if True interface is in routed mode (i.e. a layer 3 interface)
        self.admin_status: bool = False  # administrative status of the interface, True is Admin-Up (snmp ifAdminStatus)
        self.oper_status: bool = False  # operation status of interface, True is Oper-Up (snmp ifOperStatus)
        self.mtu: int = 0  # ifMTU value, for L3 interfaces
        self.speed: int = 0  # speed counter, in 1 Mbps (ie. like ifHighSpeed data from IF-MIB)
        self.duplex: int = IF_DUPLEX_UNKNOWN  # interface duplex setting, if known.
        self.phys_addr = 0x0
        self.transceiver: Transceiver = None  # any transceiver info know for this interface
        self.description: str = ""  # the interface description, as set by the switch configuration, from IF-MIB
        self.addresses_ip4: Dict[str, IPNetworkHostname] = {}  # dictionary of all my ipv4 addresses on this interface
        self.addresses_ip6: Dict[str, IPNetworkHostname] = (
            {}
        )  # dictionary of all my (routable) ipv6 addresses on this interface
        self.address_ip6_linklocal: str = ""  # the IPv6 LinkLocal address for this interface, if any.
        self.igmp_snooping: bool = False  # if True, interface does IGMP snooping
        # vlan related
        self.port_id: int = -1  # Q-Bridge MIB port id
        self.untagged_vlan: int = (
            -1
        )  # the vlan id of the interface in untagged mode. This is invalid if tagged/trunked !
        self.vlans: List[int] = (
            []
        )  # list (array) of vlanId's (as int) on this interface. If size > 0 this is a tagged port!
        self.vlan_count: int = 0
        self.is_tagged: bool = False  # if 802.1q tagging or trunking is enabled
        # some vendors (e.g. Comware, Cisco-SB) have a interface vlan mode:
        # Comware driver uses this for access, trunk, hybrid modes.
        # Cisco-SB devices use this for general, access, trunk modes.
        self.if_vlan_mode: int = -1
        self.voice_vlan: int = 0  # Cisco specific "Voice Vlan"
        self.can_change_vlan: bool = (
            True  # if set, we can change the vlan; some device types this is not implemented yet!
        )
        self.gvrp_enabled: bool = False  # the value representing the status of MVRP/GVRP on the interface
        self.last_change: int = 0  # ifLastChange, tick count since uptime when interface last changed
        # LACP related
        self.lacp_type: int = LACP_IF_TYPE_NONE
        # for LACP aggregator, a dictionary of lacp member interfaces. key=ifIndex, value=ifName of member interfaces
        self.lacp_admin_key: int = -1  # "LacpKey" admin key. Member interfaces map back to this.
        self.lacp_members: Dict[str, str] = {}
        # for members:
        self.lacp_master_index: int = (
            -1
        )  # we are member of an LACP interface. ifIndex of the master aggregate. Mutually exclusive with above!
        self.lacp_master_name: str = ""  # we are member of an LACP interface. ifname of the master aggregate.
        # Power related
        self.poe_entry: PoePort | bool = False  # if interface has PoE capabilities, will be a PoePort() object
        self.allow_poe_toggle: bool = False  # if set, any user can toggle PoE OFF-ON
        # a variety of data about what is happening on this interface:
        self.eth: Dict[str, EthernetAddress] = (
            {}
        )  # heard ethernet address on this interface, dictionay of EthernetAddress() objects
        self.lldp: Dict[str, NeighborDevice] = {}  # LLDP neighbors, dictionay of NeighborDevice() objects
        # the Vrf() this interface belongs to, if any
        self.vrf_name = ''

    def add_ip4_network(self, address: str, prefix_len: int = 0, netmask: str = "") -> None:
        '''
        Add an IPv4 address to this interface, as given by the IPv4 address and prefix_len
        It gets stored in the form of a netaddr.IPNetwork() object, indexed by addres.
        return True on success, False on failure.
        '''
        dprint(f"add_ip4_network(): interface '{self.name}': adding '{address}' len {prefix_len}, netmask '{netmask}")
        if prefix_len:
            self.addresses_ip4[address] = IPNetworkHostname(f"{address}/{prefix_len}")
        elif netmask:
            self.addresses_ip4[address] = IPNetworkHostname(f"{address}/{netmask}")
        else:
            self.addresses_ip4[address] = IPNetworkHostname(address)
        if settings.LOOKUP_HOSTNAME_ROUTED_IP:
            self.addresses_ip4[address].resolve_ip_address()
        # return True

    def add_ip6_network(self, address: str, prefix_len: int = 64) -> None:
        '''
        Add an IPv6 address to this interface, as given by the IPv6 address and prefix_len
        It gets stored in the form of a netaddr.IPNetwork() object, indexed by addres.
        return True on success, False on failure.
        '''
        dprint(f"add_ip6_network(): interface '{self.name}': adding '{address}' len {prefix_len}")
        try:
            ipv6 = IPNetworkHostname(f"{address}/{prefix_len}")
            if ipv6 in IPV6_LINK_LOCAL_NETWORK:
                self.address_ip6_linklocal = ipv6
            else:
                if settings.LOOKUP_HOSTNAME_ROUTED_IP:
                    ipv6.resolve_ip_address()
                self.addresses_ip6[address] = ipv6
        except Exception as err:
            dprint(f"INVALID IPv6 address '{address}/{prefix_len}': {err}")
        # return True

    def add_tagged_vlan(self, vlan_id: int) -> None:
        '''
        Add a Vlan() object for the vlan_id to this interface. Set tagged mode as well.
        vlan_id = vlan to add as integer
        Return True on success, False on failure and sets error variable.
        '''
        self.is_tagged = True
        self.vlans.append(int(vlan_id))
        # return True

    def remove_tagged_vlan(self, vlan_id: int) -> None:
        '''
        Remove a Vlan() object from this interface.
        vlan_id = vlan to remove as integer
        Return True on success, False on failure and sets error variable.
        '''
        vlan_id = int(vlan_id)
        if vlan_id in self.vlans:
            self.vlans.remove(vlan_id)
        # return True

    def add_learned_ethernet_address(
        self,
        eth_address: str,
        vlan_id: int = -1,
        ip4_address: str = '',
        ip6_address: str = '',
    ) -> EthernetAddress:
        '''
        Add an ethernet address to this interface, as given by the layer2 CAM/Switching tables.
        It gets stored indexed by ethernet address. Create new EthernetAddress() object if not found yet.
        If the object already exists, return it.

        Args:
            eth_address(str): ethernet address as string.
            vlan_id(int): the vlan this ethernet address was heard on.
            ip4_address (str): the IPv4 address for this ethernet address, if known. Typically from ARP tables.
            ip6_address (str): the IPv6 address for this ethernet address, if known. Found in ND tables.

        Returns:
            EthernetAddress(), either existing or new.
        '''
        dprint(
            f"Interface().add_learned_ethernet_address() for {eth_address}, vlan={vlan_id}, ip4='{ip4_address}', ip6='{ip6_address}'"
        )
        if eth_address in self.eth.keys():
            # already known!
            e = self.eth[eth_address]
            dprint("  Eth already known!")
            if vlan_id > 0:
                e.set_vlan(vlan_id)
            if ip4_address:
                e.set_ip4_address(ip4_address)
            if ip6_address:
                e.add_ip6_address(ip6_address=ip6_address)
            return e
        else:
            # add the new ethernet address
            dprint("  New ethernet, adding.")
            e = EthernetAddress(eth_address)
            if vlan_id > 0:
                e.set_vlan(vlan_id)
            if ip4_address:
                e.set_ip4_address(ip4_address=ip4_address)
            if ip6_address:
                e.add_ip6_address(ip6_address=ip6_address)
            self.eth[eth_address] = e
            return e

    def add_neighbor(self, neighbor: NeighborDevice) -> None:
        '''
        Add an lldp neighbor to this interface.
        neighbor = NeighborDevice() object.
        It gets stored indexed by lldp "index", mostly for snmp purposes.
        return True on success, False on failure.
        '''
        dprint(f"add_neighbor() for {str(neighbor)}")
        self.lldp[neighbor.index] = neighbor
        # return True

    def as_dict(self) -> dict:
        '''
        return this Interface() class as a dictionary for use by the API

        Params:
            None.

        Returns:
            dict(): key-value pairs with information about this interface.
        '''
        inf = {}
        # for the id or key, we use the same encoded as django template url() function
        inf["id"] = iri_to_uri(self.key)
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
        # VRF info
        inf['vrf'] = self.vrf_name
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

    def display_name(self) -> str:
        s = self.name  # use the IF-MIB new interface name
        if self.description:
            s = f"{s}: \"{self.description}\""
        if self.admin_status:
            s = f"{s} (UP/"
        else:
            s = f"{s} (DOWN/"
        if self.oper_status:
            s = f"{s}UP)"
        else:
            s = f"{s}DOWN)"
        return s

    def __str__(self) -> str:
        return self.display_name()
