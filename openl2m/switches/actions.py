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
)
from counters.models import counter_increment

from switches.connect.classes import Error
from switches.constants import (
    LOG_SAVE_SWITCH,
    LOG_TYPE_CHANGE,
    LOG_TYPE_ERROR,
    LOG_CHANGE_INTERFACE_ALIAS,
)
from switches.models import Log
from switches.utils import dprint, get_remote_ip

from switches.permissions import (
    get_group_and_switch,
    get_connection_if_permitted,
)


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

    log.if_name = interface.name

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
