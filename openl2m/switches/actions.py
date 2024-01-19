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

from counters.constants import (
    COUNTER_CHANGES,
    COUNTER_ERRORS,
    COUNTER_VLAN_MANAGE,
)
from counters.models import counter_increment

from switches.connect.classes import Error
from switches.connect.constants import POE_PORT_ADMIN_ENABLED, POE_PORT_ADMIN_DISABLED

from switches.constants import (
    LOG_SAVE_SWITCH,
    LOG_TYPE_CHANGE,
    LOG_TYPE_ERROR,
    LOG_CHANGE_INTERFACE_ALIAS,
    LOG_CHANGE_INTERFACE_DOWN,
    LOG_CHANGE_INTERFACE_UP,
    LOG_CHANGE_INTERFACE_PVID,
    LOG_CHANGE_INTERFACE_POE_UP,
    LOG_CHANGE_INTERFACE_POE_DOWN,
    LOG_VLAN_CREATE,
    LOG_VLAN_DELETE,
    LOG_VLAN_EDIT,
)
from switches.models import Log
from switches.utils import dprint, get_remote_ip

from switches.permissions import (
    get_group_and_switch,
    get_connection_if_permitted,
    get_interface_to_change,
    user_can_write,
    log_write_denied,
)


#
# Change admin status, ie port Enable/Disable
#
def perform_interface_admin_change(request, group_id, switch_id, interface_key, new_state):
    """
    Set the admin status of an interface, ie admin up or down.

    Params:
        request: Request() object
        group_id(int): SwitchGroup() pk
        switch_id: Switch() pk
        interface_key:  Interface() 'key' attribute
        new_state (bool): True if UP, False if DOWN

    Returns:
        boolean, Error() :
            boolean: True if successful, False if error occurred.
                    On error, Error() object will be set accordingly.
    """
    dprint(f"perform_interface_admin_change(g={group_id}, s={switch_id}, k={interface_key}, state={new_state})")

    status, info = user_can_write(request)
    if not status:
        log_write_denied(
            request=request, group_id=group_id, switch_id=switch_id, function="perform_interface_admin_change()"
        )
        return False, info

    group, switch = get_group_and_switch(request=request, group_id=group_id, switch_id=switch_id)
    connection, error = get_connection_if_permitted(request=request, group=group, switch=switch, write_access=True)

    if not connection:
        return False, error

    log = Log(
        user=request.user,
        ip_address=get_remote_ip(request),
        switch=switch,
        group=group,
    )

    interface, error = get_interface_to_change(connection=connection, interface_key=interface_key)
    if not interface:
        log.type = LOG_TYPE_ERROR
        log.description = f"Admin-Change: ERROR - {error.description}"
        log.save()
        counter_increment(COUNTER_ERRORS)
        return False, error

    log.if_name = interface.name

    if new_state:
        log.action = LOG_CHANGE_INTERFACE_UP
        state = "Enabled"
    else:
        log.action = LOG_CHANGE_INTERFACE_DOWN
        state = "Disabled"

    # are we requesting a change?
    if interface.admin_status == new_state:
        log.type = LOG_TYPE_ERROR
        log.description = f"Interface {interface.name}: Change requested to current state!"
        log.save()
        error = Error()
        error.description = f"New interface status is the same ({state}), please change status!"
        return False, error

    if not connection.set_interface_admin_status(interface, bool(new_state)):
        log.description = f"ERROR: {connection.error.description}"
        log.type = LOG_TYPE_ERROR
        log.save()
        counter_increment(COUNTER_ERRORS)
        return False, connection.error

    # indicate we need to save config!
    connection.set_save_needed(True)

    # and save data in session
    connection.save_cache()

    log.type = LOG_TYPE_CHANGE
    log.description = f"Interface {interface.name}: {state}"
    log.save()
    counter_increment(COUNTER_CHANGES)

    success = Error()
    success.status = False  # no error!
    success.description = f"Interface {interface.name} is now {state}"
    return True, success


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
        f"perform_interface_description_change(g={group_id}, s={switch_id}, i={interface_key}, d='{new_description}')"
    )

    status, info = user_can_write(request)
    if not status:
        log_write_denied(
            request=request, group_id=group_id, switch_id=switch_id, function="perform_interface_description_change()"
        )
        return False, info

    group, switch = get_group_and_switch(request=request, group_id=group_id, switch_id=switch_id)
    connection, error = get_connection_if_permitted(request=request, group=group, switch=switch, write_access=True)

    if connection is None:
        return False, error

    log = Log(
        user=request.user,
        ip_address=get_remote_ip(request),
        switch=switch,
        group=group,
        action=LOG_CHANGE_INTERFACE_ALIAS,
    )

    interface, error = get_interface_to_change(connection=connection, interface_key=interface_key)
    if not interface:
        log.type = LOG_TYPE_ERROR
        log.description = f"Description-Change: ERROR - {error.description}"
        log.save()
        counter_increment(COUNTER_ERRORS)
        return False, error

    log.if_name = interface.name

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
        log.description = f"ERROR: {connection.error.description}"
        log.type = LOG_TYPE_ERROR
        log.save()
        counter_increment(COUNTER_ERRORS)
        return False, connection.error

    # indicate we need to save config!
    connection.set_save_needed(True)

    # and save cachable/session data
    connection.save_cache()

    log.save()
    counter_increment(COUNTER_CHANGES)

    success = Error()
    success.status = False  # no error
    success.description = f"Interface {interface.name} description was changed!"
    return True, success


def perform_interface_pvid_change(request, group_id, switch_id, interface_key, new_pvid):
    """
    Change the PVID untagged vlan on an interfaces.
    This still needs to handle dot1q trunked ports.

    Params:
        request: Request() object
        group_id(int): SwitchGroup() pk
        switch_id: Switch() pk
        interface_key:  Interface() 'key' attribute
        new_pvid (int): new untagged vlan.

    Returns:
        boolean, Error() :
            boolean: True if successful, False if error occurred.
                    On error, Error() object will be set accordingly.
    """
    dprint(f"perform_interface_pvid_change(g={group_id}, s={switch_id}, i={interface_key}, p={new_pvid})")

    status, info = user_can_write(request)
    if not status:
        log_write_denied(
            request=request, group_id=group_id, switch_id=switch_id, function="perform_interface_pvid_change()"
        )
        return False, info

    group, switch = get_group_and_switch(request=request, group_id=group_id, switch_id=switch_id)
    connection, error = get_connection_if_permitted(request=request, group=group, switch=switch, write_access=True)

    if connection is None:
        return False, error

    log = Log(
        user=request.user,
        ip_address=get_remote_ip(request),
        switch=switch,
        group=group,
        action=LOG_CHANGE_INTERFACE_PVID,
    )

    interface, error = get_interface_to_change(connection=connection, interface_key=interface_key)
    if not interface:
        log.type = LOG_TYPE_ERROR
        log.description = f"PVID-Change: ERROR - {error.description}"
        log.save()
        counter_increment(COUNTER_ERRORS)
        return False, error

    log.if_name = interface.name

    # this should not happen:
    if new_pvid == 0:
        log.type = LOG_TYPE_ERROR
        log.description = "Pvid-Change: new vlan = 0 (?)"
        log.save()
        counter_increment(COUNTER_ERRORS)
        error = Error()
        error.description = "Could not read new vlan (0?). Please contact your administrator!"
        return False, error

    # did the vlan change?
    if interface.untagged_vlan == new_pvid:
        error = Error()
        error.description = f"New vlan {interface.untagged_vlan} is the same, please change the vlan first!"
        return False, error

    # are we allowed to change to this vlan ?
    connection._set_allowed_vlans()
    if new_pvid not in connection.allowed_vlans.keys():
        log.type = LOG_TYPE_ERROR
        log.save()
        counter_increment(COUNTER_ERRORS)
        error = Error()
        error.description = f"New vlan {new_pvid} is not valid or allowed on this device"
        return False, error

    # make sure we cast the proper type here! Ie this needs an Integer()
    if not connection.set_interface_untagged_vlan(interface, new_pvid):
        log.description = f"ERROR: {connection.error.description}"
        log.type = LOG_TYPE_ERROR
        log.save()
        counter_increment(COUNTER_ERRORS)
        error = Error()
        error.description = f"Error setting untagged vlan on interface {interface.name}"
        error.details = connection.error.description
        return False, error

    log.type = LOG_TYPE_CHANGE
    log.description = f"Interface {interface.name}: new PVID = {new_pvid} (was {interface.untagged_vlan})"

    # indicate we need to save config!
    connection.set_save_needed(True)

    # and save cachable/session data
    connection.save_cache()

    # all OK, save log
    log.save()
    counter_increment(COUNTER_CHANGES)

    success = Error()
    success.status = False  # not an error
    success.description = f"Interface {interface.name} changed to vlan {new_pvid}"
    return True, success


def perform_interface_poe_change(request, group_id, switch_id, interface_key, new_state):
    """
    Change the PoE status of an interfaces.

    Params:
        request: Request() object
        group_id(int): SwitchGroup() pk
        switch_id: Switch() pk
        interface_key:  Interface() 'key' attribute
        new_state (bool): True to set PoE Enabled, False to set PoE Disabled.

    Returns:
        boolean, Error() :
            boolean: True if successful, False if error occurred.
                    On error, Error() object will be set accordingly.
    """
    dprint(f"perform_interface_poe_change(g={group_id}, s={switch_id}, i={interface_key}, st={new_state})")

    status, info = user_can_write(request)
    if not status:
        log_write_denied(
            request=request, group_id=group_id, switch_id=switch_id, function="perform_interface_poe_change()"
        )
        return False, info

    group, switch = get_group_and_switch(request=request, group_id=group_id, switch_id=switch_id)
    connection, error = get_connection_if_permitted(request=request, group=group, switch=switch, write_access=True)

    if connection is None:
        return False, error

    log = Log(
        user=request.user,
        ip_address=get_remote_ip(request),
        switch=switch,
        group=group,
        action=LOG_CHANGE_INTERFACE_PVID,
    )

    interface, error = get_interface_to_change(connection=connection, interface_key=interface_key)
    if not interface:
        log.type = LOG_TYPE_ERROR
        log.description = f"Admin-Change: ERROR - {error.description}"
        log.save()
        counter_increment(COUNTER_ERRORS)
        return False, error

    log.if_name = interface.name

    if not interface.poe_entry:
        dprint("  NOT PoE Capable!")
        # should not happen...
        log.type = LOG_TYPE_ERROR
        log.description = f"Interface {interface.name} does not support PoE"
        error = Error()
        error.status = True
        error.description = log.descr
        log.save()
        counter_increment(COUNTER_ERRORS)
        return False, error

    log.type = LOG_TYPE_CHANGE
    if new_state:
        log.action = LOG_CHANGE_INTERFACE_POE_UP
        log.description = f"Interface {interface.name}: Enabling PoE"
        state = "Enabled"
        new_state = POE_PORT_ADMIN_ENABLED
    else:
        log.action = LOG_CHANGE_INTERFACE_POE_DOWN
        log.description = f"Interface {interface.name}: Disabling PoE"
        state = "Disabled"
        new_state = POE_PORT_ADMIN_DISABLED

    # do the work:
    retval = connection.set_interface_poe_status(interface, new_state)
    if retval < 0:
        log.description = f"ERROR: {connection.error.description}"
        log.type = LOG_TYPE_ERROR
        log.save()
        counter_increment(COUNTER_ERRORS)
        error = Error()
        error.description = log.description
        error.details = connection.error.details
        return False, error

    # indicate we need to save config!
    connection.set_save_needed(True)

    # and save cachable/session data
    connection.save_cache()

    log.save()
    counter_increment(COUNTER_CHANGES)
    success = Error()
    success.status = False  # no error
    success.description = f"Interface {interface.name} PoE is now {state}"
    return True, success


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

    status, info = user_can_write(request)
    if not status:
        log_write_denied(
            request=request, group_id=group_id, switch_id=switch_id, function="perform_switch_save_config()"
        )
        return False, info

    group, switch = get_group_and_switch(request=request, group_id=group_id, switch_id=switch_id)
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
        log.description = "Device cannot or does not need to save config"
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
    success = Error()
    success.status = False  # no error
    success.description = "Configuration was saved!"
    return True, success


def perform_switch_vlan_add(request, group_id, switch_id, vlan_id, vlan_name):
    """
    This will create a vlan on the device.

    Params:
        request: Request() object
        group_id(int): SwitchGroup() pk
        switch_id: Switch() pk
        vlan_id (int): the value for the new vlan
        vlan_name (str): the name of the new vlan

    Returns:
        boolean, Error() :
            boolean: True if successful, False if error occurred.
                    On error, Error() object will be set accordingly.

    """
    dprint("perform_switch_vlan_create()")

    status, info = user_can_write(request)
    if not status:
        log_write_denied(request=request, group_id=group_id, switch_id=switch_id, function="perform_switch_vlan_add()")
        return False, info

    group, switch = get_group_and_switch(request=request, group_id=group_id, switch_id=switch_id)
    connection, error = get_connection_if_permitted(request=request, group=group, switch=switch, write_access=True)

    if connection is None:
        return False, error

    if not request.user.is_superuser and not request.user.profile.vlan_edit:
        error = Error()
        error.description = "Access denied!"
        return False, error

    if connection.vlan_exists(vlan_id):
        error = Error()
        error.description = f"Vlan {vlan_id} already exists!"
        return False, error

    if not vlan_name:
        error = Error()
        error.description = "Please provide a vlan name!"
        return False, error

    # all OK, go create
    counter_increment(COUNTER_VLAN_MANAGE)
    status = connection.vlan_create(vlan_id=vlan_id, vlan_name=vlan_name)
    if status:
        log = Log(
            user=request.user,
            ip_address=get_remote_ip(request),
            switch=switch,
            group=group,
            action=LOG_VLAN_CREATE,
            type=LOG_TYPE_CHANGE,
            description=f"Vlan {vlan_id} ({vlan_name}) created.",
        )
        log.save()
        # need to save changes
        connection.set_save_needed(True)
        # and save data in session
        connection.save_cache()
        info = Error()
        info.status = False  # no error
        info.description = log.description
        return True, info
    else:
        error = Error()
        error.status = True
        error.description = f"Error creating vlan {vlan_id}!"
        error.details = connection.error.details
        log = Log(
            user=request.user,
            ip_address=get_remote_ip(request),
            switch=switch,
            group=group,
            action=LOG_VLAN_CREATE,
            type=LOG_TYPE_ERROR,
            description=f"Error creating vlan {vlan_id} ({vlan_name}): {connection.error.details}",
        )
        log.save()
        return False, error


def perform_switch_vlan_delete(request, group_id, switch_id, vlan_id):
    """
    This will create a vlan on the device.

    Params:
        request: Request() object
        group_id(int): SwitchGroup() pk
        switch_id: Switch() pk
        vlan_id (int): the value for the new vlan
        vlan_name (str): the name of the new vlan

    Returns:
        boolean, Error() :
            boolean: True if successful, False if error occurred.
                    On error, Error() object will be set accordingly.
    """
    dprint("perform_switch_vlan_delete()")

    status, info = user_can_write(request)
    if not status:
        log_write_denied(
            request=request, group_id=group_id, switch_id=switch_id, function="perform_switch_vlan_delete()"
        )
        return False, info

    group, switch = get_group_and_switch(request=request, group_id=group_id, switch_id=switch_id)
    connection, error = get_connection_if_permitted(request=request, group=group, switch=switch, write_access=True)

    if connection is None:
        return False, error

    if not request.user.is_superuser:
        # Only superuser can delete!
        error = Error()
        error.description = "Access Denied: you need to be SuperUser to delete a VLAN"
        return False, error

    if not connection.vlan_exists(vlan_id):
        error = Error()
        error.description = f"Vlan {vlan_id} does not exist!"
        return False, error

    # go delete:
    status = connection.vlan_delete(vlan_id=vlan_id)
    if status:
        log = Log(
            user=request.user,
            ip_address=get_remote_ip(request),
            switch=switch,
            group=group,
            action=LOG_VLAN_DELETE,
            type=LOG_TYPE_CHANGE,
            description=f"Vlan {vlan_id} deleted.",
        )
        log.save()
        # need to save changes
        connection.set_save_needed(True)
        # and save data in session
        connection.save_cache()
        counter_increment(COUNTER_VLAN_MANAGE)
        info = Error()
        info.status = False  # no error
        info.description = f"Vlan {vlan_id} was deleted!"
        return True, info
    else:
        error = Error()
        error.status = True
        error.description = "Error deleting vlan {vlan_id}!"
        error.details = connection.error.details
        log = Log(
            user=request.user,
            ip_address=get_remote_ip(request),
            switch=switch,
            group=group,
            action=LOG_VLAN_DELETE,
            type=LOG_TYPE_ERROR,
            description=f"Error deleting vlan {vlan_id}: {connection.error.details}",
        )
        log.save()
        return False, error


def perform_switch_vlan_edit(request, group_id, switch_id, vlan_id, vlan_name):
    """
    This will create a vlan on the device.

    Params:
        request: Request() object
        group_id(int): SwitchGroup() pk
        switch_id: Switch() pk
        vlan_id (int): the value for the new vlan
        vlan_name (str): the name of the new vlan

    Returns:
        boolean, Error() :
            boolean: True if successful, False if error occurred.
                    On error, Error() object will be set accordingly.
    """
    dprint("perform_switch_vlan_edit()")

    status, info = user_can_write(request)
    if not status:
        log_write_denied(request=request, group_id=group_id, switch_id=switch_id, function="perform_switch_vlan_edit()")
        return False, info

    group, switch = get_group_and_switch(request=request, group_id=group_id, switch_id=switch_id)
    connection, error = get_connection_if_permitted(request=request, group=group, switch=switch, write_access=True)

    if connection is None:
        return False, error

    if not connection.vlan_exists(vlan_id):
        error = Error()
        error.description = f"Vlan {vlan_id} does not exist!"
        return False, error

    if not vlan_name:
        error = Error()
        error.description = "Vlan name can not be empty!"
        return False, error

    status = connection.vlan_edit(vlan_id=vlan_id, vlan_name=vlan_name)
    if status:
        log = Log(
            user=request.user,
            ip_address=get_remote_ip(request),
            switch=switch,
            group=group,
            action=LOG_VLAN_EDIT,
            type=LOG_TYPE_CHANGE,
            description=f"Vlan {vlan_id} renamed to '{vlan_name}'",
        )
        log.save()
        # need to save changes
        connection.set_save_needed(True)
        # and save data in session
        connection.save_cache()
        counter_increment(COUNTER_VLAN_MANAGE)
        info = Error()
        info.status = False  # no error
        info.description = f"Updated name for vlan {vlan_id} to '{vlan_name}'"
        return True, info
    else:
        error = Error()
        error.status = True
        error.description = f"Error updating vlan {vlan_id}!"
        error.details = connection.error.details
        log = Log(
            user=request.user,
            ip_address=get_remote_ip(request),
            switch=switch,
            group=group,
            action=LOG_VLAN_EDIT,
            type=LOG_TYPE_ERROR,
            description=f"Error updating vlan {vlan_id} name to '{vlan_name}': {connection.error.details}",
        )
        log.save()
        return False, error
