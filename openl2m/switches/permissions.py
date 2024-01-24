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

from rest_framework import status as http_status
from rest_framework.reverse import reverse as rest_reverse
from rest_framework.request import Request as RESTRequest

from counters.constants import (
    COUNTER_ERRORS,
    COUNTER_ACCESS_DENIED,
)
from counters.models import counter_increment

from switches.connect.classes import Error
from switches.constants import (
    LOG_TYPE_ERROR,
    LOG_CHANGE_INTERFACE_ALIAS,
    LOG_CONNECTION_ERROR,
    LOG_INTERFACE_NOT_FOUND,
    LOG_INTERFACE_DENIED,
    LOG_DENIED,
    SWITCH_STATUS_ACTIVE,
    SWITCH_VIEW_BASIC,
)
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
                            "switches-api:api_switch_vlan_add",
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
                    if switch.nms_id:
                        members[int(switch.id)]["nms_id"] = switch.nms_id
                    else:
                        members[int(switch.id)]["nms_id"] = ""
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
    if isinstance(request, RESTRequest) and request.auth is not None:
        # API user with Token, need to read groups every time:
        dprint("  API Token - calling get_my_device_groups()")
        groups = get_my_device_groups(request=request)
    else:
        # session based, ie. web ui, or api via ajax/browser, get groups from session store:
        dprint("  WEB UI or API with Session - calling get_from_http_session")
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
    dprint(f"get_connection_if_permitted(g={group} s={switch})")
    log = Log(
        user=request.user,
        ip_address=get_remote_ip(request),
        switch=switch,
        group=group,
        action=LOG_CHANGE_INTERFACE_ALIAS,
    )
    if group is None or switch is None:
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


def get_interface_to_change(connection, interface_key):
    """Get an Interface() object for the key given. Test if it is writable.

    Params:
        connection: valid Connection() object to the device.
        interface_key: key into the Connection.interfaces dict().

    Returns:
        connection, error:
            a valid Interface() or False on error.
            In former case, error=False, in latter case error=Error() object.
    """
    dprint("get_interface_to_change()")
    interface = connection.get_interface_by_key(interface_key)
    if not interface:
        log = Log(
            user=connection.request.user,
            ip_address=get_remote_ip(connection.request),
            switch=connection.switch,
            group=connection.group,
            type=LOG_TYPE_ERROR,
            action=LOG_INTERFACE_NOT_FOUND,
            description=f"Error getting interface data for {interface_key}",
        )
        log.save()
        counter_increment(COUNTER_ERRORS)
        error = Error()
        error.description = "Could not get interface data. Please contact your administrator!"
        error.details = "Sorry, no more details available!"
        return False, error

    # can the user manage the interface?
    if not interface.manageable:
        log = Log(
            user=connection.request.user,
            ip_address=get_remote_ip(connection.request),
            switch=connection.switch,
            group=connection.group,
            type=LOG_TYPE_ERROR,
            action=LOG_INTERFACE_DENIED,
            description=f"Can not manage interface '{interface.name}'",
        )
        log.save()
        counter_increment(COUNTER_ERRORS)
        error = Error()
        error.code = http_status.HTTP_403_FORBIDDEN
        error.description = "You can not manage this interface!"
        error.details = interface.unmanage_reason
        return False, error

    # return the interface:
    return interface, False


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
                dprint("   All OK")
            except Exception as err:
                dprint(f"   ERROR getting Group or Switch object: {err}")
                group = None
                switch = None
        else:
            dprint("  INVALID switch id!")
    else:
        dprint("  INVALID group id!")
    return group, switch


def user_can_write(request):
    """Validate the user can write changes. This means either Session auth (ie. WebUI),
       or an API Token() with the 'write_enabled" attribute set to True.

    Args:
        request (HttpRequest()): the HttpRequest of the caller.

    Returns:
        boolean, info:
            True if the user of this request can write, False if not.
            info is an Error() object with code and description set accordingly.
    """
    dprint(f"user_can_write(), request = {type(request)}")
    if hasattr(request, "auth"):
        if request.auth is not None:  # Token from REST API
            if not request.auth.write_enabled:
                error = Error()
                error.code = http_status.HTTP_403_FORBIDDEN
                error.description = "This token cannot write!"
                return False, error
    info = Error()
    info.status = False
    info.description = "All OK!"
    return True, info


def log_write_denied(request, group_id, switch_id, function):
    """
    Log a message indicating writing to device was denied.

    Params:
        request: Request() object
        group_id(int): SwitchGroup() pk
        switch_id: Switch() pk
        function (str): the change function was attempted but denied.

    Returns:
        nothing
    """
    dprint(f"log_write_denied(g={group_id}, s={switch_id}, function={function})")
    log = Log(
        user=request.user,
        ip_address=get_remote_ip(request),
        type=LOG_TYPE_ERROR,
        action=LOG_DENIED,
        description=f"{function}: Writing denied to switch {switch_id} in group {group_id}",
    )
    log.save()
    counter_increment(COUNTER_ACCESS_DENIED)
