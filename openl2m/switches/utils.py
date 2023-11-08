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
from django.shortcuts import render

import datetime
import pytz
import logging
import socket
import ipaddress
import re

from django.conf import settings
from django.utils.timezone import get_default_timezone

from rest_framework.reverse import reverse as rest_reverse
from rest_framework.request import Request as RESTRequest

from switches.constants import SWITCH_STATUS_ACTIVE, SWITCH_VIEW_BASIC


logger_console = logging.getLogger("openl2m.console")


def success_page(request, group, switch, description):
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


def success_page_by_id(request, group_id, switch_id, message):
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


def warning_page(request, group, switch, description):
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


def warning_page_by_id(request, group_id, switch_id, message):
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


def error_page(request, group, switch, error):
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


def error_page_by_id(request, group_id, switch_id, error):
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


def dprint(var):
    """
    Output to the configured console logger if debugging is Enabled
    See settings.LOGGING as defined in openl2m/configuration.py
    """
    if settings.DEBUG:
        logger_console.debug(var)


def ddump(obj, header=False):
    if settings.DEBUG:
        if header:
            logger_console.debug(header)
        logger_console.debug(f"Object = {type(obj)}")
        for attr in dir(obj):
            if hasattr(obj, attr):
                logger_console.debug("obj.%s = %s" % (attr, getattr(obj, attr)))


def time_duration(seconds):
    """
    show a nice string with the time duration from the seconds given
    """
    return str(datetime.timedelta(seconds=seconds)).rsplit('.', 2)[0]


def uptime_to_string(uptime):
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


def get_local_timezone_offset():
    """
    Get the offset as <-+00:00> of our local timezone
    This uses the settings.TIME_ZONE variable, if set.
    """
    return datetime.datetime.now(pytz.timezone(str(get_default_timezone()))).strftime('%z')


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


def string_matches_regex(string, regex):
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


def string_contains_regex(string, regex):
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


def get_ip_dns_name(ip):
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


def get_choice_name(choice_list, choice):
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


# ###################################################
# Permission functions, used by Web UI and REST API #
#####################################################


def get_my_device_permissions(request, group_id=-1, switch_id=-1):
    """
    find the SwitchGroups, and Switch()-es in those groups, that this user has rights to.
    For API use, group_id and switch_id are given. Then check if we have rights
    to this specific device, and return SwitchGroup() and Switch() objects.

    Args:
        request:  current Request() object
        group_id (int): the pk of the SwitchGroup()
        switch_id (int): the pk of the Switch()

    Returns:
        tuple of
        permissions:    dict of pk's of SwitchGroup() objects this user is member of,
                        each is a dict of active devices(switches).
        group:  SwitchGroup() object or None
        switch: Switch() object or None
    """
    permitted = False
    if request.user.is_superuser or request.user.is_staff:
        # optimize data queries, get all related field at once!
        switchgroups = SwitchGroup.objects.all().order_by("name")
    else:
        # figure out what this user has access to.
        # Note we use the ManyToMany 'related_name' attribute for readability!
        switchgroups = request.user.switchgroups.all().order_by("name")

    # now find active devices in these groups
    permissions = {}

    this_group = None
    this_switch = None

    for group in switchgroups:
        if group.switches.count():
            # set this group, and the switches, in web session to track permissions
            group_info = {
                'name': group.name,
                'description': group.description,
                'display_name': group.display_name,
                'read_only': group.read_only,
                'comments': group.comments,
            }
            members = {}
            for switch in group.switches.all():
                if switch.status == SWITCH_STATUS_ACTIVE:
                    # we save the names as well, so we can search them!
                    if switch.default_view == SWITCH_VIEW_BASIC:
                        url = rest_reverse(
                            "switches-api:api_switch_basic_view",
                            request=request,
                            kwargs={"group_id": group.id, "switch_id": switch.id},
                        )
                    else:
                        url = rest_reverse(
                            "switches-api:api_switch_detail_view",
                            request=request,
                            kwargs={"group_id": group.id, "switch_id": switch.id},
                        )
                    members[int(switch.id)] = {
                        "name": switch.name,
                        # "hostname": switch.hostname,
                        "description": switch.description,
                        "default_view": switch.default_view,
                        "default_view_name": switch.get_default_view_display(),
                        "url": url,
                        "url_add_vlan": rest_reverse(
                            "switches-api:api_switch_add_vlan",
                            request=request,
                            kwargs={"group_id": group.id, "switch_id": switch.id},
                        ),
                        "connector_type": switch.connector_type,
                        "connector_type_name": switch.get_connector_type_display(),
                        "read_only": switch.read_only,
                        "primary_ipv4": switch.primary_ip4,
                        "comments": switch.comments,
                    }
                    # is this the switch in the group we are looking for?
                    if switch.id == switch_id and group.id == group_id:
                        this_group = group
                        this_switch = switch
            group_info['members'] = members
            permissions[int(group.id)] = group_info
    return (permissions, this_group, this_switch)


def get_group_switch_from_permissions(request, permissions, group_id, switch_id):
    """Check access to the group and switch. Return the SwitchGroup and Switch objects

    Params:
        request:  HttpRequest() object
        permissions: dictionary as created by get_my_device_permissions()
        group_id: (int) SwitchGroup() pk
        switch_id: (int) Switch() pk

    Returns:
        group, switch:  SwitchGroup() or None, Switch() or None.
    """
    dprint(f"get_group_switch_from_permissions(group={group_id}, switch={switch_id})")
    group = None
    switch = None
    if permissions and isinstance(permissions, dict) and int(group_id) in permissions.keys():
        switches = permissions[int(group_id)]
        if isinstance(switches, dict) and int(switch_id) in switches.members.keys():
            dprint("  FOUND switch in group member")
            try:
                group = SwitchGroup().objects.filter(pk=group_id)
                switch = Switch().objects.filter(pk=switch_id)
            except Exception:
                group = None
                switch = None
                dprint("  GROUP or SWITCH OBJECT NOT FOUND!")
    return group, switch


def perform_user_rights_to_group_and_switch(request, group_id, switch_id):
    """
    Check if the current user has rights to this switch in this group.
    This handles both Session auth (web ui), and REST auth (api).
    Returns True if allowed, False if not!

    Params:
        request: Request() object.
        group_id (int): SwitchGroup() pk
        switch_id (int): Switch() pk

    Returns:
        group: SwitchGroup() object or None
        switch: Switch() object or None.
    """
    dprint("perform_user_rights_to_group_and_switch()")
    # web ui, or api using token ?
    if isinstance(request, RESTRequest):
        if request.auth != None:
            dprint("  API - calling get_my_device_permissions()")
            permissions, group, switch = get_my_device_permissions(
                request=request, group_id=group_id, switch_id=switch_id
            )
            return group, switch
        dprint("RESTRequest() bu request.auth NOT None!")

    # web ui, regular app or api browser
    dprint("  WEB UI - calling get_from_http_session")
    permissions = get_from_http_session(request=request, name="permissions")
    return get_group_switch_from_permissions(request, permissions, group_id, switch_id)
