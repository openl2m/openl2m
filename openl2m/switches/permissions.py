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
import re

from django.conf import settings

from rest_framework import status as http_status
from rest_framework.reverse import reverse as rest_reverse

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
from switches.connect.connect import get_connection_object
from switches.models import Log, SwitchGroup
from switches.utils import dprint, get_remote_ip

# ###################################################
# Permission functions, used by Web UI and REST API #
#####################################################


def get_my_device_groups(request, group_id=-1, switch_id=-1):
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
    dprint("get_my_device_groups()")
    permitted = False
    if request.user.is_superuser or request.user.is_staff:
        dprint("  Superuser or Staff!")
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
                        "indent_level": switch.indent_level,
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
        permissions: dictionary as created by get_my_device_groups()
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
            dprint("  API - calling get_my_device_groups()")
            permissions, group, switch = get_my_device_groups(request=request, group_id=group_id, switch_id=switch_id)
            return group, switch
        dprint("RESTRequest() but request.auth NOT None!")

    # web ui, regular app or api browser
    dprint("  WEB UI - calling get_from_http_session")
    permissions = get_from_http_session(request=request, name="permissions")
    return get_group_switch_from_permissions(request, permissions, group_id, switch_id)


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


def perform_interface_description_change(request, group_id, switch_id, interface_key, new_description):
    """
    Change the description on an interface.

    Params:
        request: Request() object
        group_id(int): SwitchGroup() pk
        switch_id: Switch() pk
        interface_key:  Interface() 'key' attribute
        new_description (str): new description for Interface().

    Returns:
        boolean, Error() :
            boolean: True if successful, False if error occurred.
                    On error, Error() object will be set accordingly.
    """
    dprint(
        f"perform_interface_description_change(g={group_id}, s={switch_id}, k={interface_key}, d='{new_description}')"
    )
    group, switch = perform_user_rights_to_group_and_switch(request=request, group_id=group_id, switch_id=switch_id)
    connection, error = get_connection_if_permitted(request=request, group=group, switch=switch, write_access=True)

    if connection is None:
        return False, error

    dprint(f"  Key '{interface_key}' is type {type(interface_key)}")

    interface = connection.get_interface_by_key(str(interface_key))
    if not interface:
        log.type = LOG_TYPE_ERROR
        log.description = f"Description-Change: Error getting interface data for {interface_key}"
        log.save()
        counter_increment(COUNTER_ERRORS)
        error = Error()
        error.description = "Could not get interface data. Please contact your administrator!"
        return False, error

    # can the user manage the interface?
    if not interface.manageable:
        log.description = f"Can not manage {interface.name}: description edit not allowed!"
        log.type = LOG_TYPE_ERROR
        log.save()
        counter_increment(COUNTER_ERRORS)
        error = Error()
        error.description = "You can not manage this interface!"
        error.details = interface.unmanage_reason
        return False, error

    # are we allowed to change description ?
    if not interface.can_edit_description:
        log.description = f"Interface {interface.name} description edit not allowed!"
        log.type = LOG_TYPE_ERROR
        log.save()
        counter_increment(COUNTER_ERRORS)
        error = Error()
        error.code = http_status.HTTP_403_FORBIDDEN
        error.description = "You are not allowed to change the interface description!"
        return False, error

    # check the new description
    if interface.description == new_description:
        error = Error()
        error.description = "New description is the same, please change it first!"
        return False, error

    log.type = LOG_TYPE_CHANGE

    # check if the description is allowed:
    if settings.IFACE_ALIAS_NOT_ALLOW_REGEX:
        match = re.match(settings.IFACE_ALIAS_NOT_ALLOW_REGEX, new_description)
        if match:
            log.type = LOG_TYPE_ERROR
            log.description = "New description matches admin deny setting!"
            log.save()
            counter_increment(COUNTER_ERRORS)
            error = Error()
            error.code = http_status.HTTP_403_FORBIDDEN
            error.description = f"The description '{new_description}' is not allowed!"
            return False, error

    # check if the original description starts with a string we have to keep
    if settings.IFACE_ALIAS_KEEP_BEGINNING_REGEX:
        keep_format = f"(^{settings.IFACE_ALIAS_KEEP_BEGINNING_REGEX})"
        match = re.match(keep_format, interface.description)
        if match:
            # check of new submitted description begins with this string:
            match_new = re.match(keep_format, new_description)
            if not match_new:
                # required start string NOT found on new description, so prepend it!
                new_description = f"{match[1]} {new_description}"

    # log the work!
    log.description = f"Interface {interface.name}: Description = {new_description}"
    # and do the work:
    if not connection.set_interface_description(interface, new_description):
        log.description = f"ERROR: {conn.error.description}"
        log.type = LOG_TYPE_ERROR
        log.save()
        counter_increment(COUNTER_ERRORS)
        return False, conn.error

    # indicate we need to save config!
    connection.set_save_needed(True)

    # and save cachable/session data
    connection.save_cache()

    log.save()
    counter_increment(COUNTER_CHANGES)

    return True, None


def perform_switch_save_config(request, group_id, switch_id):
    """
    This will save the running config to flash/startup/whatever, on supported platforms

    Params:
        request: Request() object
        group_id(int): SwitchGroup() pk
        switch_id: Switch() pk

    Returns:
        boolean, Error() :
            boolean: True if successful, False if error occurred.
                    On error, Error() object will be set accordingly.
    """
    dprint("perform_switch_save_config()")

    group, switch = perform_user_rights_to_group_and_switch(request=request, group_id=group_id, switch_id=switch_id)
    connection, error = get_connection_if_permitted(request=request, group=group, switch=switch, write_access=True)

    if connection is None:
        return False, error

    log = Log(
        user=request.user,
        ip_address=get_remote_ip(request),
        switch=switch,
        group=group,
        action=LOG_SAVE_SWITCH,
        type=LOG_TYPE_CHANGE,
        description="Saving switch config",
    )

    if not connection.can_save_config:
        # we should not be called, since device cannot save or does not need to save config
        log.type = LOG_TYPE_ERROR
        log.description = f"Device cannot or does not need to save config"
        log.save()
        counter_increment(COUNTER_ERRORS)
        error = Error()
        error.description = "This switch model cannot save or does not need to save the config"
        return False, error

    # the following condition is ignored. If this is called from WebUI, we know "save_needed" state.
    # However, from API we have no state (the caller needs to track it), so we simply save when called!
    # if not connection.save_needed:
    #     log.type = LOG_TYPE_WARNING
    #     log.description = "Device does not need saving!"
    #     log.save()
    #     counter_increment(COUNTER_ERRORS)
    #     error = Error()
    #     error.description = log.description
    #     return True, error

    # we can save
    if connection.save_running_config() < 0:
        # an error happened!
        log.type = LOG_TYPE_ERROR
        log.description = f"Error saving config: {connection.error.description}"
        log.save()
        counter_increment(COUNTER_ERRORS)
        error = Error()
        error.description = log.description
        error.details = connection.error.details
        return False, error

    # clear save flag
    connection.set_save_needed(False)

    # save cachable/session data
    connection.save_cache()

    # all OK
    log.save()
    return True, None
