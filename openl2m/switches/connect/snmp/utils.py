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
import netaddr

from django.conf import settings
from switches.utils import dprint

"""
This file contains SNMP utility functions
"""


def decimal_to_hex_string_ethernet(decimals):
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


def bytes_ethernet_to_string(bytes):
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
