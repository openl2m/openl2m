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
    COUNTER_ACCESS_DENIED,
)
from counters.models import counter_increment

from switches.connect.classes import Error
from switches.constants import (
    LOG_TYPE_CHANGE,
    LOG_TYPE_ERROR,
    LOG_CHANGE_INTERFACE_ALIAS,
    LOG_CONNECTION_ERROR,
    LOG_DENIED,
)
from switches.connect.connect import get_connection_object
from switches.models import Log
from switches.utils import dprint, get_remote_ip, perform_user_rights_to_group_and_switch


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
    log = Log(
        user=request.user,
        ip_address=get_remote_ip(request),
        switch=switch,
        group=group,
        action=LOG_CHANGE_INTERFACE_ALIAS,
        if_name=interface_key,
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
        if request.user.read_only or group.read_only or switch.read_only:
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
        conn = get_connection_object(request, group, switch)
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

    return Connection, None


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
        log.description = f"Alias-Change: Error getting interface data for {interface_key}"
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

    if not connection.save_needed:
        # this is unlikely to happen
        log.type = LOG_TYPE_ERROR
        log.description = "Device does not need saving!"
        log.save()
        counter_increment(COUNTER_ERRORS)
        error = Error()
        error.description = log.description
        return False, error

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
    conn.set_save_needed(False)

    # save cachable/session data
    conn.save_cache()

    # all OK
    log.save()
    return True, None
