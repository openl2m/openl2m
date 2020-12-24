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
from switches.utils import dprint
from switches.connect.classes import EthernetAddress

"""
This file contains SNMP utility functions
"""


def decimal_to_hex_string_ethernet(decimals):
    """
    Convert SNMP decimal ethernet string "11.12.13.78.90.100"
    to hex value and colon-string "aa-bb-cc-11-22-33".
    """
    bytes = decimals.split('.')
    if len(bytes) == 6:
        mac = ''
        for byte in bytes:
            h = "%02X" % int(byte)
            if not mac:
                mac += h
            else:
                mac += "-%s" % h
        return mac
    return "00-00-00-00-00-00"


def bytes_ethernet_to_string(bytes):
    """
    Convert SNMP ethernet in 6-byte octetstring to defined ethernet string format.
    """
    if len(bytes) == 6:
        format = '%02X'
        separator = '-'
        eth_string = separator.join(format % ord(b) for b in bytes)
        dprint(f"bytes_ethernet_to_string() for {eth_string}")
        eth = EthernetAddress(eth_string)
        return str(eth)
    return ''
