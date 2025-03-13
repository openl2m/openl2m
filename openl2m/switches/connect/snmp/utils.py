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
import ipaddress
import netaddr
import struct

from django.conf import settings
from switches.utils import dprint
from switches.connect.constants import IANA_TYPE_IPV4, IANA_TYPE_IPV6

"""
This file contains SNMP utility functions
"""


def decimal_to_hex_string_ethernet(decimals: str) -> str:
    """
    Convert SNMP decimal ethernet string "5.12.13.78.90.100"
    to hex value and colon-string "05:0c:0d:4e:5a:64"
    """
    bytes = decimals.split('.')
    if len(bytes) == 6:
        mac = ''
        for byte in bytes:
            h = "%02X" % int(byte)
            if not mac:
                mac += h
            else:
                mac += ":%s" % h
        return mac
    return "00:00:00:00:00:00"


def bytes_ethernet_to_string(bytes: str) -> str:
    """
    Convert SNMP ethernet in 6-byte octetstring to the selected ethernet string format.
    """
    if len(bytes) == 6:
        eth_string = ":".join("%02X" % ord(b) for b in bytes)
        dprint(f"bytes_ethernet_to_string() for {eth_string}")
        # we use the netaddr library here to make it easy on ourselves to convert to the version wanted:
        eth = netaddr.EUI(eth_string)
        # make sure we use consistent string representation of this ethernet address:
        eth.dialect = settings.MAC_DIALECT
        return str(eth)
    return ''


def get_ip_from_sub_oid(sub_oid: str, addr_type: int, has_length: bool) -> str:
    """Convert an OID sub-sub_oid to an IP address in string format.
    Note: currently does NOT do IPV6 parsing yet!

    Params:
        sub_oid (str): the sub_oid is the final part of the returned SNMP OID.
                       It may contains length as first number, followed by the rest of the IP digits in dotted-decimal format.
        addr_type (int): either IANA_TYPE_IPV4 (1) or IANA_TYPE_IPV6 (2). This defines format of the sub_oid string.
        has_length (bool): if True, first byte in sub_oid is length, ie. "<length>.<ip in dotted-decimal>"
                           False: format is "<ip in dotted-decimal>"
    Returns:
        (str): the parsed IP address in string format, or "" if invalid.
    """
    dprint(f"get_ip_from_sub_oid(sub_oid={sub_oid}, addr_type={addr_type}, has_length={has_length}")
    if addr_type == IANA_TYPE_IPV4:
        if has_length:
            # for IPv4, encoding is simply the length (always 4) followed by IP:
            parts = sub_oid.split('.', 1)  # only split in 2
            if int(parts[0]) != 4:  # looks valid
                # very unlikely to happen (only if bad snmp implementation on device):
                dprint(f"  INVALID IPv4 length field, expected 4, got {int(parts[0])}")
                return ""
            # the remaining part is the IPv4 address:
            ip = parts[1]
        else:
            # no length, just use full sub-oid as IPv4:
            ip = sub_oid
        dprint(f"  IPv4={ip}")
        return ip

    if addr_type == IANA_TYPE_IPV6:
        # for IPv6, encoding has optional length (always 16) followed by IP:
        if has_length:
            parts = sub_oid.split('.', 1)  # only split in 2
            if int(parts[0]) != 16:  # invalid
                dprint(f"  INVALID IPv6 lenght field, expected 16, got {int(parts[0])}")
                return ""
            # the IPv6 is encoded in the rest of the OID:
            oid_ip = parts[1]
        else:
            # no length, just use full sub-oid:
            oid_ip = sub_oid
        # move from dotted decimal to IPv6 format. Convert OID string into list of integers:
        ipv6_list = [int(octet) for octet in oid_ip.split('.')]
        # Pack the integers into a byte string
        ipv6_bytes = struct.pack('!16B', *ipv6_list)
        # convert to proper format:
        try:
            ipv6 = ipaddress.ip_address(ipv6_bytes)
            if ipv6.version == 6:  # valid!
                dprint(f"  IPv6={ipv6}")
                return str(ipv6)
            else:
                # invalid!
                dprint(f"  INVALID Ipv6 conversion, version return: {ipv6.version}")
                return ""
        except Exception as err:
            dprint(f"  IPv6 conversion failed - {err}")
            return ""

    dprint(f"  INVALID TYPE {addr_type}")
    return ""
