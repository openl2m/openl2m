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
import inspect
import ipaddress
from ipware import get_client_ip
import logging
import pprint
import pytz
import re
import socket

from django.conf import settings
from django.http import HttpResponse
from django.http.request import HttpRequest
from django.shortcuts import render
from django.utils.timezone import get_default_timezone

# from switches.models import Switch, SwitchGroup
# from switches.connect.classes import Error

logger_console = logging.getLogger("openl2m.console")


def success_page(request: HttpRequest, group, switch, description: str) -> HttpResponse:
    """
    Generic function to return an 'function succeeded' page
    requires the http request(), Group(), Switch() objects
    and a string description of the success.
    """
    return render(
        request,
        'success_page.html',
        {
            'group': group,
            'switch': switch,
            'description': description,
        },
    )


def success_page_by_id(request: HttpRequest, group_id: int, switch_id: int, message: str) -> HttpResponse:
    """
    Generic function to return an 'function succeeded' page.

    Params:
        request: the HttpRequest() object
        group_id (int): pk of the SwitchGroup()
        switch_id (int): pk of the Switch()
        message (str): textual description to display.

    Returns:
        call to render() to generate html page.
    """
    return render(
        request,
        'success_page_by_id.html',
        {
            'group_id': group_id,
            'switch_id': switch_id,
            'message': message,
        },
    )


def warning_page(request: HttpRequest, group, switch, description: str) -> HttpResponse:
    """
    Generic function to return an warning page
    requires the http request(), Group() and Switch() objects,
    and a string description with the warning.
    """
    return render(
        request,
        'warning_page.html',
        {
            'group': group,
            'switch': switch,
            'description': description,
        },
    )


def warning_page_by_id(request: HttpRequest, group_id: int, switch_id: int, message: str) -> HttpResponse:
    """
    Generic function to return an warning page

    Params:
        request: the HttpRequest() object
        group_id (int): pk of the SwitchGroup()
        switch_id (int): pk of the Switch()
        message (str): textual description to display.

    Returns:
        call to render() to generate html page.
    """
    return render(
        request,
        'warning_page_by_id.html',
        {
            'group_id': group_id,
            'switch_id': switch_id,
            'message': message,
        },
    )


def error_page(request: HttpRequest, group, switch, error) -> HttpResponse:
    """
    Generic function to return an error page
    requires the http request(), Group(), Switch() and Error() objects
    """
    return render(
        request,
        'error_page.html',
        {
            'group': group,
            'switch': switch,
            'error': error,
        },
    )


def error_page_by_id(request: HttpRequest, group_id: int, switch_id: int, error) -> HttpResponse:
    """
    Generic function to return an error page
    requires the http request(), Group(), Switch() and Error() objects

    Params:
        request: the HttpRequest() object
        group_id (int): pk of the SwitchGroup()
        switch_id (int): pk of the Switch()
        error (object): Error() describing the problem.

    Returns:
        call to render() to generate html page.
    """
    return render(
        request,
        'error_page_by_id.html',
        {
            'group_id': group_id,
            'switch_id': switch_id,
            'error': error,
        },
    )


def dprint(var: str):
    """
    Output to the configured console logger if debugging is Enabled
    See settings.LOGGING as defined in openl2m/configuration.py
    """
    if settings.DEBUG:
        logger_console.debug(var)


def dvar(var, header: str = ""):
    """Debug print any variable with pprint

    Args:
        var (_type_): the variable to debug
        header (str, optional): optional header description. Defaults to "".
    """
    if settings.DEBUG:
        if header:
            logger_console.debug(header)
        # built-in types:
        if isinstance(var, (float, int, str, list, dict, tuple)):
            logger_console.debug(pprint.pformat(var))
        else:
            logger_console.debug(f"Type: {type(var)}, Values:")
            # use inspect.getmembers() to find attributes that are not functions:
            attribs = inspect.getmembers(var, lambda a: not (inspect.isroutine(a)))
            for attrib in attribs:
                # props is a list of all the object’s attributes and their current values,
                # wrapped in (name, value) tuples.
                # skip dunder (__) objects:
                if not attrib[0].startswith("__"):
                    logger_console.debug(pprint.pformat(attrib))


def time_duration(seconds: int) -> str:
    """
    show a nice string with the time duration from the seconds given
    """
    return str(datetime.timedelta(seconds=seconds)).rsplit('.', 2)[0]


def uptime_to_string(uptime: int) -> str:
    """
    Convert uptime in seconds to a nice string with days, hrs, mins, seconds
    """
    days = uptime // (24 * 3600)
    uptime = uptime % (24 * 3600)  # the "left over" seconds beyond the days
    hours = uptime // 3600
    uptime %= 3600  # the "left over" seconds beyond the hours
    minutes = uptime // 60
    uptime %= 60  # the remaining seconds
    return f"{days} Days {hours} Hrs {minutes} Mins {uptime} Secs"


def get_local_timezone_offset() -> str:
    """
    Get the offset as <-+00:00> of our local timezone
    This uses the settings.TIME_ZONE variable, if set.
    """
    return datetime.datetime.now(pytz.timezone(str(get_default_timezone()))).strftime('%z')


def save_to_http_session(request: HttpRequest, name: str, data):
    """
    Save an object in the http request session store
    """
    dprint(f"save_to_http_session({name})")
    request.session[name] = data
    request.session.modified = True


def get_from_http_session(request: HttpRequest, name: str, delete: bool = False):
    """
    Retrieve an object from the http session store.
    If delete=True, object will be removed from the store
    """
    dprint(f"get_from_http_session(name={name}, delete={delete})")
    if name in request.session.keys():
        data = request.session[name]
        if delete:
            del request.session[name]
            request.session.modified = True
        return data
    else:
        dprint("  NOT found in session cache!")
        return None


def get_remote_ip(request: HttpRequest) -> str:
    """
    Return a string that represents the most likely client IP ip address
    """
    if request:
        # see: https://stackoverflow.com/questions/4581789/how-do-i-get-user-ip-address-in-django
        (ip, routable) = get_client_ip(request)  # we need the request variable from the view!
        if ip is None:
            return '0.0.0.0'
        return str(ip)
    # not in web server context, return "0"
    return "0.0.0.0"


def is_valid_hostname_or_ip(data: str) -> bool:
    """
    Check if the data given is either an IPv4 address, or a valid hostname.
    Return True if so, False otherwize.
    Note: this does not handle IPv6 yet!
    """
    # check IP v4 pattern first
    try:
        address = ipaddress.ip_address(data)
        if type(address) is ipaddress.IPv4Address:
            return True
        if type(address) is ipaddress.IPv6Address:
            return False  # v6 not supported for now!
        return False  # should not happen!
    except ValueError:
        # not IP v4 or v6!, so check hostname:
        try:
            socket.gethostbyname(data)
            # note: this does IPv4 resolution. When we support IPv6, change to socket.getaddrinfo()
            return True
        except Exception:
            # fail gracefully!
            return False
    return False


def string_matches_regex(string: str, regex: str) -> bool:
    """
    Validate data with the given regular expression.
    string: the string to match
    regex: the regular expression to match the data to.
    returns True if match or no regex given. False otherwize
    """
    dprint(f"string_matches_regex(): string={string} regex={regex}")
    if regex:
        # match string against regex.
        # Note re.match() starts at beginning of string!
        match = re.match(regex, string)
        if match:
            dprint("  ==> PASS!")
            return True
        else:
            dprint("  ==> FAIL!")
            return False
    return True


def string_contains_regex(string: str, regex: str) -> bool:
    """
    Search string for an occurance of the given regular expression.
    string: the string to match
    regex: the regular expression to find anywhere in the (multi-line) string.
    returns True if found, or no regex given. False otherwize
    """
    dprint(f"string_contains_regex(): string={string} regex={regex}")
    if regex:
        # search string for regex, anywhere in string, hence we use re.search()!
        found = re.search(regex, string)
        if found:
            dprint("  ==> PASS!")
            return True
        else:
            dprint("  ==> FAIL!")
            return False
    return True


def get_ip_dns_name(ip: str) -> str:
    """Get the DNS PTR (reverse name) for the given IP4 or IP6 address.

    Args:
        ip(str):    string representing the IP address.

    Return:
        (str): either the FQDN for the ip address, or an empty string if not found.
    """
    try:
        # we use 'name required' to force an exception if reverse lookup not found:
        (hostname, port_name) = socket.getnameinfo((str(ip), 0), socket.NI_NAMEREQD)
    except Exception:
        hostname = ''
    return hostname


def get_choice_name(choice_list: list, choice) -> str:
    """Get the name of a choice

    Args:
        choice_list (list): a list of [index, name] items indicating choices

    Return:
        (str): the name of the choice requested, or a default value.
    """
    for item in choice_list:
        if item[0] == choice:
            return item[1]
    return "Invalid Choice!"
