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
import datetime
import pytz
import logging
import socket
import ipaddress

from django.conf import settings
from django.utils.timezone import get_default_timezone

from switches.constants import ETH_FORMAT_COLON, ETH_FORMAT_HYPHEN, ETH_FORMAT_CISCO

logger_debug = logging.getLogger("openl2m.debug")
logger_console = logging.getLogger("openl2m.console")


def dprint(var):
    """
    log to file if configured in settings.LOGGING
    via the Django/Python Logger() class.
    Additionally, print to console logger if debugging is Enabled
    """
    logger_debug.debug(var)
    if settings.DEBUG:
        logger_console.debug(var)


def time_duration(seconds):
    """
    show a nice string with the time duration from the seconds given
    """
    return str(datetime.timedelta(seconds=seconds)).rsplit('.', 2)[0]


def get_local_timezone_offset():
    """
    Get the offset as <-+00:00> of our local timezone
    This uses the settings.TIME_ZONE variable, if set.
    """
    return datetime.datetime.now(pytz.timezone(str(get_default_timezone()))).strftime('%z')


def bytes_to_hex_string_ethernet(bytes):
    """
    Convert SNMP ethernet in 6-byte octetstring format to hex string.
    Various final formats are supported, configured in settings
    """
    if len(bytes) == 6:
        if settings.ETH_FORMAT_UPPERCASE:
            format = '%02X'
        else:
            format = '%02x'

        if(settings.ETH_FORMAT == ETH_FORMAT_COLON):
            separator = ':'

        if(settings.ETH_FORMAT == ETH_FORMAT_HYPHEN):
            separator = '-'

        if(settings.ETH_FORMAT == ETH_FORMAT_CISCO):
            return "CISCO FORMAT TBD"

        return separator.join(format % ord(b) for b in bytes)

    return ''


def decimal_to_hex_string_ethernet(decimal):
    """
    Convert SNMP decimal ethernet string "11.12.13.78.90.100"
    to hex string. Various final formats are supported, configured in settings
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


def decimal_ethernet_to_oui(decimal):
    """
    Convert SNMP decimal ethernet string "11.12.13.78.90.100"
    to the OUI string "AA-BB-CC"
    """
    bytes = decimal.split('.')
    if len(bytes) == 6:
        oui_bytes = bytes[0:3]
        separator = '-'
        format = '%02X'
        return separator.join(format % int(b) for b in oui_bytes)
    return ''


def save_to_http_session(request, name, data):
    """
    Save an object in the http request session store
    """
    request.session[name] = data


def get_from_http_session(request, name, delete=False):
    """
    Retrieve an object from the http session store.
    If delete=True, object will be removed from the store
    """
    if name in request.session.keys():
        data = request.session[name]
        if delete:
            del request.session[name]
        return data
    else:
        return None


def get_remote_ip(request):
    """
    Return a string that represents the most likely client IP ip address
    """
    if request:
        # see: https://stackoverflow.com/questions/4581789/how-do-i-get-user-ip-address-in-django
        from ipware import get_client_ip
        (ip, routable) = get_client_ip(request)  # we need the request variable from the view!
        if ip is None:
            return '0.0.0.0'
        return str(ip)
    # not in web server context, return "0"
    return "0.0.0.0"


def is_valid_hostname_or_ip(data):
    """
    Check if the data given is either an IPv4 address, or a valid hostname.
    Return True if so, False otherwize.
    Note: this does not handle IPv6 yet!
    """
    # check IP v4 pattern first
    try:
        address = ipaddress.ip_address(data)
        if type(address) == ipaddress.IPv4Address:
            return True
        if type(address) == ipaddress.IPv6Address:
            return False    # v6 not supported for now!
        return False        # should not happen!
    except ValueError:
        # not IP v4 or v6!, so check hostname:
        try:
            ip4 = socket.gethostbyname(data)
            # note: this does IPv4 resolution. When we support IPv6, change to socket.getaddrinfo()
            return True
        except Exception:
            # fail gracefully!
            return False
    return False
