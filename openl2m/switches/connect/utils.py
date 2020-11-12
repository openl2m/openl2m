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
"""
Various utility functions
"""
from django.conf import settings

from switches.constants import ETH_FORMAT_COLON, ETH_FORMAT_HYPHEN, ETH_FORMAT_CISCO


def decimal_to_hex_string_ethernet(decimal):
    """
    Convert SNMP decimal ethernet string "11.12.13.78.90.100" to colon-string.
    """
    format = settings.ETH_FORMAT
    bytes = decimal.split('.')
    if len(bytes) == 6:
        mac = ''
        for byte in bytes:
            if settings.ETH_FORMAT_UPPERCASE:
                h = "%02X" % int(byte)
            else:
                h = "%02x" % int(byte)

            if(settings.ETH_FORMAT == ETH_FORMAT_COLON):
                if not mac:
                    mac += h
                else:
                    mac += ":%s" % h

            if(settings.ETH_FORMAT == ETH_FORMAT_HYPHEN):
                if not mac:
                    mac += h
                else:
                    mac += "-%s" % h

            if(settings.ETH_FORMAT == ETH_FORMAT_CISCO):
                return "CISCO FORMAT TBD"

        return mac
    return False


def bytes_ethernet_to_string(bytes):
    """
    Convert SNMP ethernet in 6-byte octetstring format to colong-string format.
    """
    if len(bytes) == 6:
        if settings.ETH_FORMAT_UPPERCASE:
            format = '%02X'
        else:
            format = '%02x'
        separator = ':'
        return separator.join(format % ord(b) for b in bytes)

    return ''


def bytes_ethernet_to_oui(bytes):
    """
    Convert SNMP ethernet in 6-byte octetstring
    to the OUI string "AA-BB-CC"
    """
    if len(bytes) == 6:
        oui_bytes = bytes[0:3]
        separator = '-'
        format = '%02X'
        return separator.join(format % ord(b) for b in oui_bytes)
    return ''


def ethernet_to_oui(ethernet_string):
    """
    Convert SNMP decimal ethernet string "11:AB:12:CD:13:EF"
    to the OUI string "11-AA-12"
    """
    bytes = decimal.split(':')
    if len(bytes) == 6:
        oui_bytes = bytes[0:3]
        separator = '-'
        format = '%02X'
        return separator.join(format % int(b) for b in oui_bytes)
    return ''
