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

#
# Functions that perform actions on interfaces, called by both the WEB UI and REST API
#
from django.conf import settings

from rest_framework import status as http_status
from rest_framework.reverse import reverse as rest_reverse
from rest_framework.request import Request as RESTRequest

from counters.constants import (
    COUNTER_CHANGES,
    COUNTER_ERRORS,
    COUNTER_ACCESS_DENIED,
)
from counters.models import counter_increment

from switches.connect.classes import Error
from switches.constants import (
    LOG_SAVE_SWITCH,
    LOG_TYPE_CHANGE,
    LOG_TYPE_ERROR,
    LOG_CHANGE_INTERFACE_ALIAS,
    LOG_CONNECTION_ERROR,
    LOG_DENIED,
    SWITCH_STATUS_ACTIVE,
    SWITCH_VIEW_BASIC,
)
import switches
from switches.connect.connect import get_connection_object
from switches.models import Log, Switch, SwitchGroup
from switches.utils import dprint, get_remote_ip, get_from_http_session

# ###################################################
# Permission functions, used by Web UI and REST API #
#####################################################


def get_my_device_groups(request):
    """
    Find the SwitchGroup()s, and Switch()s in those groups, that this user has rights to.
    Returns a dictionary of groups and the devices in those groups.

    Args:
        request:  current Request() object

    Returns:
        groups: dict of pk's of SwitchGroup() objects this user is member of,
                each is a dict of active devices(switches).
    """
    dprint("get_my_device_groups()")
    permitted = False
    if request.user.is_superuser or request.user.is_staff:
        dprint("  Superuser or Staff!")
        # optimize data queries, get all related field at once!
        groups = SwitchGroup.objects.all().order_by("name")
    else:
        # figure out what this user has access to.
        # Note we use the ManyToMany 'related_name' attribute for readability!
        dprint("  Regular user.")
        groups = request.user.switchgroups.all().order_by("name")

    # now find active devices in these groups
    permissions = {}

    this_group = None
    this_switch = None

    for group in groups:
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
                        "hostname": switch.hostname,
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
                        "indent_level": switch.indent_level,
                    }
            group_info['members'] = members
            permissions[int(group.id)] = group_info
    return permissions


def get_group_and_switch(request, group_id, switch_id):
    """
    Get the Group() and Switch() if the current user has rights.
    This handles both Session auth (web ui), and Token auth (api).

    Params:
        request: Request() object.
        group_id (int): SwitchGroup() pk
        switch_id (int): Switch() pk

    Returns:
        group: SwitchGroup() object or None
        switch: Switch() object or None.
    """
    dprint("get_group_and_switch()")
    # api using token, or session based ?
    if isinstance(request, RESTRequest) and request.auth != None:
        # API user with Token, need to read groups every time:
        dprint("  API Token - calling get_my_device_groups()")
        groups = get_my_device_groups(request=request)
    else:
        # session based, ie. web ui, or api via ajax/browser, get groups from session store:
        dprint("  WEB UI or API Session - calling get_from_http_session")
        groups = get_from_http_session(request=request, name="permissions")
    # dprint(f"user groups =\n{groups}\n\n")
    return _get_group_and_switch_from_permissions(permissions=groups, group_id=group_id, switch_id=switch_id)


def get_connection_if_permitted(request, group, switch, write_access=False):
    """Get a Connection() object if access to this switch is permitted.

    Params:
        request:  HttpRequest() object.
        group: SwitchGroup() object.
        switch: Switch() object

    Returns:
        connection, error:
            Connection() object if permitted, None if not.
            Error() object describing the error, e.g. access denied.

    """
    dprint("get_connection_if_permitted()")
    log = Log(
        user=request.user,
        ip_address=get_remote_ip(request),
        switch=switch,
        group=group,
        action=LOG_CHANGE_INTERFACE_ALIAS,
    )
    if not group or not switch:
        log.type = LOG_TYPE_ERROR
        log.action = LOG_DENIED
        log.description = "Access Denied!"
        log.save()
        counter_increment(COUNTER_ACCESS_DENIED)
        error = Error()
        error.status = True
        error.code = http_status.HTTP_403_FORBIDDEN
        error.description = "Access denied!"
        return False, error

    if write_access:
        if request.user.profile.read_only or group.read_only or switch.read_only:
            log.type = LOG_TYPE_ERROR
            log.action = LOG_DENIED
            log.description = "Access Denied! (group or switch is read-only)"
            log.save()
            counter_increment(COUNTER_ACCESS_DENIED)
            error = Error()
            error.status = True
            error.code = http_status.HTTP_403_FORBIDDEN
            error.description = "Access denied!"
            error.details = "User, Group or Switch is read-only!"
            return False, error

    try:
        connection = get_connection_object(request, group, switch)
    except Exception as err:
        dprint(f"  Error caught from get_connection_object(): {err}")
        log.type = LOG_TYPE_ERROR
        log.action = LOG_CONNECTION_ERROR
        log.description = "Could not get connection"
        log.save()
        counter_increment(COUNTER_ERRORS)
        error = Error()
        error.description = "Could not get connection. Please contact your administrator to make sure switch data is correct in the database!"
        error.details = "This is likely a configuration error, such as incorrect SNMP or Credentials settings!"
        return False, error

    return connection, None


def _get_group_and_switch_from_permissions(permissions, group_id, switch_id):
    """Check access to the group and switch.
       Return the full permissions, and requested SwitchGroup() and Switch() objects.

    Params:
        request:  HttpRequest() object
        permissions: dictionary as created by get_my_device_groups()
        group_id: (int) SwitchGroup() pk
        switch_id: (int) Switch() pk

    Returns:
        group, switch:  SwitchGroup() or None, Switch() or None.
    """
    group_id = int(group_id)
    switch_id = int(switch_id)
    dprint(f"_get_group_and_switch_from_permissions(group={group_id}, switch={switch_id})")
    group = None
    switch = None
    if permissions and isinstance(permissions, dict) and int(group_id) in permissions.keys():
        devices = permissions[int(group_id)]
        if isinstance(devices, dict) and int(switch_id) in devices['members'].keys():
            try:
                group = SwitchGroup.objects.get(pk=group_id)
                switch = Switch.objects.get(pk=switch_id)
            except Exception as err:
                group = None
                switch = None
    return group, switch
