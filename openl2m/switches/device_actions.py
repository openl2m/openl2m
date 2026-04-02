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
# DeviceActions class - performs actions on interfaces and switches,
# called by both the WEB UI and REST API.
#
import re

from django.conf import settings
from django.http.request import HttpRequest

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
    LOG_CHANGE_INTERFACE_VLANS,
    LOG_VLAN_CREATE,
    LOG_VLAN_DELETE,
    LOG_VLAN_EDIT,
)
from switches.models import Log
from switches.utils import dprint, get_remote_ip

from switches.permissions import (
    get_group_and_switch,
    get_connection_if_permitted,
    PERMISSION_INTERFACE_POE,
    get_interface_to_change,
    user_can_write,
    log_write_denied,
)

# Per SNMP MIB IfXTable, the ifAlias max size = 64, so limit all descriptions to that.
MAX_INTERFACE_DESCRIPTION_SIZE = 64


class DeviceActions:
    """
    Encapsulates actions that can be performed on network devices.
    Used by both the Web UI views and the REST API views.

    All public action methods return (bool, Error):
        bool: True on success, False on failure.
        Error: on success, Error.status=False with a description;
               on failure, Error with details about what went wrong.
    """

    def __init__(self, request: HttpRequest, group_id: int, switch_id: int):
        self.request = request
        self.group_id = group_id
        self.switch_id = switch_id
        self.group = None
        self.switch = None
        self.connection = None

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _check_write_permission(self, function_name: str):
        """Check if the current user has write permission.

        Returns:
            (True, None) if allowed.
            (False, Error) if denied.
        """
        status, info = user_can_write(self.request)
        if not status:
            log_write_denied(
                request=self.request,
                group_id=self.group_id,
                switch_id=self.switch_id,
                function=function_name,
            )
            return False, info
        return True, None

    def _get_connection(self):
        """Resolve group/switch and obtain a write-access connection.

        On success, sets self.group, self.switch, self.connection.

        Returns:
            (True, None) on success.
            (False, Error) on failure.
        """
        self.group, self.switch = get_group_and_switch(
            request=self.request, group_id=self.group_id, switch_id=self.switch_id
        )
        connection, error = get_connection_if_permitted(
            request=self.request, group=self.group, switch=self.switch, write_access=True
        )
        if connection is None:
            return False, error
        self.connection = connection
        return True, None

    def _create_log(self, **kwargs) -> Log:
        """Create a Log entry pre-filled with user, IP, switch, and group."""
        return Log(
            user=self.request.user,
            ip_address=get_remote_ip(self.request),
            switch=self.switch,
            group=self.group,
            **kwargs,
        )

    def _get_interface(self, interface_key: str, permission=None):
        """Look up the interface to change.

        Returns:
            (Interface, None) on success.
            (None, Error) on failure.
        """
        kwargs = {"connection": self.connection, "interface_key": interface_key}
        if permission is not None:
            kwargs["permission"] = permission
        return get_interface_to_change(**kwargs)

    def _log_error(self, log: Log, description: str):
        """Mark a log entry as an error, save it, and increment the error counter."""
        log.type = LOG_TYPE_ERROR
        log.description = description
        log.save()
        counter_increment(COUNTER_ERRORS)

    def _finish_success(self, log: Log, counter=COUNTER_CHANGES):
        """Common success epilogue: flag save needed, persist cache, save log, bump counters."""
        self.connection.set_save_needed(True)
        self.connection.save_cache()
        log.save()
        counter_increment(counter)
        self.switch.update_change()

    @staticmethod
    def _success_result(description: str):
        """Build a successful (True, Error) return value."""
        result = Error()
        result.status = False  # no error
        result.description = description
        return True, result

    @staticmethod
    def _error_result(description: str, details='', code=None):
        """Build a failed (False, Error) return value."""
        error = Error()
        error.status = True
        error.description = description
        if details:
            error.details = details
        if code is not None:
            error.code = code
        return False, error

    def _setup(self, function_name: str):
        """Common setup: check write permission, then get connection.

        Returns:
            (True, None) if ready to proceed.
            (False, Error) if denied or connection failed.
        """
        ok, error = self._check_write_permission(function_name)
        if not ok:
            return False, error
        return self._get_connection()

    # ------------------------------------------------------------------
    # Interface actions
    # ------------------------------------------------------------------

    def interface_admin_change(self, interface_key: str, new_state: bool):
        """Set the admin status of an interface, ie admin up or down.

        Params:
            interface_key: Interface() 'key' attribute
            new_state: True if UP, False if DOWN

        Returns:
            (bool, Error)
        """
        dprint(
            f"DeviceActions.interface_admin_change(g={self.group_id}, s={self.switch_id}, k={interface_key}, state={new_state})"
        )

        ok, error = self._setup("interface_admin_change()")
        if not ok:
            return False, error

        log = self._create_log()

        interface, error = self._get_interface(interface_key)
        if not interface:
            self._log_error(log, f"Admin-Change: ERROR - {error.description}")
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
            return self._error_result(f"New interface status is the same ({state}), please change status!")

        if not self.connection.set_interface_admin_status(interface, bool(new_state)):
            self._log_error(log, f"ERROR: {self.connection.error.description}")
            return False, self.connection.error

        log.type = LOG_TYPE_CHANGE
        log.description = f"Interface {interface.name}: {state}"
        self._finish_success(log)

        return self._success_result(f"Interface {interface.name} is now {state}")

    def interface_description_change(self, interface_key: str, new_description: str):
        """Change the description on an interface.

        Params:
            interface_key: Interface() 'key' attribute
            new_description: new description for the interface

        Returns:
            (bool, Error)
        """
        dprint(
            f"DeviceActions.interface_description_change(g={self.group_id}, s={self.switch_id}, i={interface_key}, d='{new_description}')"
        )

        # remove leading and trailing white space
        new_description = new_description.strip()

        ok, error = self._setup("interface_description_change()")
        if not ok:
            return False, error

        log = self._create_log(action=LOG_CHANGE_INTERFACE_ALIAS)

        # check size of submitted new description:
        if len(new_description) > MAX_INTERFACE_DESCRIPTION_SIZE:
            self._log_error(log, f"Description-Change: ERROR - new value too long (>{MAX_INTERFACE_DESCRIPTION_SIZE})")
            return False, error

        interface, error = self._get_interface(interface_key)
        if not interface:
            self._log_error(log, f"Description-Change: ERROR - {error.description}")
            return False, error

        log.if_name = interface.name

        # are we allowed to change description ?
        if not interface.can_edit_description:
            self._log_error(log, f"Interface {interface.name} description edit not allowed!")
            return self._error_result(
                "You are not allowed to change the interface description!",
                code=http_status.HTTP_403_FORBIDDEN,
            )

        # check the new description
        if interface.description == new_description:
            return self._error_result("New description is the same, please change it first!")

        log.type = LOG_TYPE_CHANGE

        # check if the description is allowed:
        if settings.IFACE_ALIAS_NOT_ALLOW_REGEX:
            match = re.match(settings.IFACE_ALIAS_NOT_ALLOW_REGEX, new_description)
            if match:
                self._log_error(log, "New description matches admin deny setting!")
                return self._error_result(
                    f"The description '{new_description}' is not allowed!",
                    code=http_status.HTTP_403_FORBIDDEN,
                )

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
        if not self.connection.set_interface_description(interface, new_description):
            self._log_error(log, f"ERROR: {self.connection.error.description}")
            return False, self.connection.error

        self._finish_success(log)

        return self._success_result(f"Interface {interface.name} description was changed!")

    def interface_pvid_change(self, interface_key: str, new_pvid: int):
        """Change the PVID untagged vlan on an interface.

        Params:
            interface_key: Interface() 'key' attribute
            new_pvid: new untagged vlan id

        Returns:
            (bool, Error)
        """
        dprint(
            f"DeviceActions.interface_pvid_change(g={self.group_id}, s={self.switch_id}, i={interface_key}, p={new_pvid})"
        )

        ok, error = self._setup("interface_pvid_change()")
        if not ok:
            return False, error

        log = self._create_log(action=LOG_CHANGE_INTERFACE_PVID)

        interface, error = self._get_interface(interface_key)
        if not interface:
            self._log_error(log, f"PVID-Change: ERROR - {error.description}")
            return False, error

        log.if_name = interface.name

        # this should not happen:
        if new_pvid == 0:
            self._log_error(log, "Pvid-Change: new vlan = 0 (?)")
            return self._error_result("Could not read new vlan (0?). Please contact your administrator!")

        # did the vlan change?
        if interface.untagged_vlan == new_pvid:
            return self._error_result(f"New vlan {interface.untagged_vlan} is the same, please change the vlan first!")

        # are we allowed to change to this vlan ?
        self.connection._set_allowed_vlans()
        if new_pvid not in self.connection.allowed_vlans.keys():
            self._log_error(log, log.description)
            return self._error_result(f"New vlan {new_pvid} is not valid or allowed on this device")

        # all OK, save old pvid
        old_pvid = interface.untagged_vlan

        # make sure we cast the proper type here! Ie this needs an Integer()
        if not self.connection.set_interface_untagged_vlan(interface, new_pvid):
            self._log_error(log, f"ERROR: {self.connection.error.description} - {self.connection.error.details}")
            return self._error_result(
                f"Error setting untagged vlan {new_pvid} on interface {interface.name}",
                details=f"{self.connection.error.description}: {self.connection.error.details}",
            )

        log.type = LOG_TYPE_CHANGE
        log.description = f"Interface {interface.name}: new PVID = {new_pvid} (was {old_pvid})"
        self._finish_success(log)

        return self._success_result(f"Interface {interface.name} changed to vlan {new_pvid}")

    def interface_poe_change(self, interface_key: str, new_state: bool):
        """Change the PoE status of an interface.

        Params:
            interface_key: Interface() 'key' attribute
            new_state: True to enable PoE, False to disable

        Returns:
            (bool, Error)
        """
        dprint(
            f"DeviceActions.interface_poe_change(g={self.group_id}, s={self.switch_id}, i={interface_key}, st={new_state})"
        )

        ok, error = self._setup("interface_poe_change()")
        if not ok:
            return False, error

        log = self._create_log(action=LOG_CHANGE_INTERFACE_PVID)

        interface, error = self._get_interface(interface_key, permission=PERMISSION_INTERFACE_POE)
        if not interface:
            self._log_error(log, f"Admin-Change: ERROR - {error.description}")
            return False, error

        log.if_name = interface.name

        if not interface.poe_entry:
            dprint("  NOT PoE Capable!")
            # should not happen...
            self._log_error(log, f"Interface {interface.name} does not support PoE")
            return self._error_result(f"Interface {interface.name} does not support PoE")

        log.type = LOG_TYPE_CHANGE
        if new_state:
            log.action = LOG_CHANGE_INTERFACE_POE_UP
            log.description = f"Interface {interface.name}: Enabling PoE"
            state = "Enabled"
            poe_state = POE_PORT_ADMIN_ENABLED
        else:
            log.action = LOG_CHANGE_INTERFACE_POE_DOWN
            log.description = f"Interface {interface.name}: Disabling PoE"
            state = "Disabled"
            poe_state = POE_PORT_ADMIN_DISABLED

        # do the work:
        if not self.connection.set_interface_poe_status(interface, poe_state):
            self._log_error(log, f"ERROR: {self.connection.error.description} - {self.connection.error.details}")
            return False, self.connection.error

        self._finish_success(log)

        return self._success_result(f"Interface {interface.name} PoE is now {state}")

    def interface_tags_edit(self, interface_key: str, pvid: int, tagged_vlans: list, allow_all: bool = False):
        """Change the untagged pvid and 802.1q (tagged/trunked) vlans on an interface.

        Params:
            interface_key: Interface() 'key' attribute
            pvid: integer vlan id to set as untagged vlan
            tagged_vlans: integer list of vlan id's to set on interface
            allow_all: if set, all vlans are allowed on trunk

        Returns:
            (bool, Error)
        """
        dprint(
            f"DeviceActions.interface_tags_edit(group={self.group_id}, switch={self.switch_id}, int={interface_key}, pvid={pvid}, tagged_vlans={tagged_vlans}, allow_all={allow_all})"
        )

        # Note: this method does NOT call _setup() because the original code
        # did not call user_can_write() — it relies on the tags-edit permission check below.
        ok, error = self._get_connection()
        if not ok:
            return False, error

        """ Implementation notes:
        If we allow tags-edit for regular, non-admin users, we need to parse carefully!
        In that case, we will allow adding/deleting vlans the user has access to,
        and SHOULD NOT CHANGE NON-PERMITTED VLANS !!!!
        Ie. this requires looking at the interface current tagged vlans,
        and mashing this up with the requested vlans...

        Currently, permissions are set in Connector()._set_interfaces_permissions(),
        in switches/connect/connector.py, around line 1775
        """

        log = self._create_log(action=LOG_CHANGE_INTERFACE_VLANS)

        dprint("CONNECTION type = {type(self.connection)}")
        # verify we allow trunk editing and driver can handle interface mode change:
        if not settings.ALLOW_TAGS_EDIT or not self.connection.can_edit_tags:
            log.type = LOG_TYPE_ERROR
            log.description = "Permission denied to 802.1Q vlan edit!"
            log.save()
            return self._error_result("Permission denied!")

        interface, error = self._get_interface(interface_key)
        if not interface:
            self._log_error(log, f"Can not get interface: ERROR - {error.description}")
            return False, error

        log.if_name = interface.name

        # call the interface vlan edit function:
        if not self.connection.set_interface_vlans(
            interface=interface, untagged_vlan=pvid, tagged_vlans=tagged_vlans, allow_all=allow_all
        ):
            self._log_error(log, f"ERROR: {self.connection.error.description} - {self.connection.error.details}")
            return False, self.connection.error

        log.type = LOG_TYPE_CHANGE
        log.description = (
            f"Interface {interface.name} vlans set to untagged={pvid}, tagged={tagged_vlans} with allow_all={allow_all}"
        )
        self._finish_success(log)

        return self._success_result(f"Interface {interface.name} vlans have been set!")

    # ------------------------------------------------------------------
    # Switch-level actions
    # ------------------------------------------------------------------

    def switch_save_config(self):
        """Save the running config to flash/startup on supported platforms.

        Returns:
            (bool, Error)
        """
        dprint("DeviceActions.switch_save_config()")

        ok, error = self._setup("switch_save_config()")
        if not ok:
            return False, error

        log = self._create_log(
            action=LOG_SAVE_SWITCH,
            type=LOG_TYPE_CHANGE,
            description="Saving switch config",
        )

        if not self.connection.can_save_config:
            self._log_error(log, "Device cannot or does not need to save config")
            return self._error_result("This switch model cannot save or does not need to save the config")

        # we can save
        if not self.connection.save_running_config():
            self._log_error(log, f"Error saving config: {self.connection.error.description}")
            return self._error_result(
                f"Error saving config: {self.connection.error.description}",
                details=self.connection.error.details,
            )

        # clear save flag
        self.connection.set_save_needed(False)
        # save cachable/session data
        self.connection.save_cache()
        # all OK
        self.switch.update_change()
        log.save()
        return self._success_result("Configuration was saved!")

    def switch_vlan_add(self, vlan_id: int, vlan_name: str):
        """Create a vlan on the device.

        Params:
            vlan_id: the value for the new vlan
            vlan_name: the name of the new vlan

        Returns:
            (bool, Error)
        """
        dprint("DeviceActions.switch_vlan_add()")

        ok, error = self._setup("switch_vlan_add()")
        if not ok:
            return False, error

        if not self.request.user.is_superuser and not self.request.user.profile.vlan_edit:
            return self._error_result("Access denied!")

        if vlan_id < 1:
            return self._error_result(f"Invalid new vlan id: '{vlan_id}'")

        if self.connection.vlan_exists(vlan_id):
            return self._error_result(f"Vlan {vlan_id} already exists!")

        # remove leading and trailing white space
        vlan_name = vlan_name.strip()
        if not vlan_name:
            if self.connection.can_set_vlan_name:
                return self._error_result("Please provide a vlan name!")
            # set to reasonable default to show in WebUI until refreshed from device.
            vlan_name = f"VLAN{vlan_id}"

        # all OK, go create
        counter_increment(COUNTER_VLAN_MANAGE)
        if self.connection.vlan_create(vlan_id=vlan_id, vlan_name=vlan_name):
            log = self._create_log(
                action=LOG_VLAN_CREATE,
                type=LOG_TYPE_CHANGE,
                description=f"Vlan {vlan_id} ({vlan_name}) created.",
            )
            log.save()
            # need to save changes
            self.connection.set_save_needed(True)
            # and save data in session
            self.connection.save_cache()
            self.switch.update_change()
            return self._success_result(log.description)

        # an error occured:
        log = self._create_log(
            action=LOG_VLAN_CREATE,
            type=LOG_TYPE_ERROR,
            description=f"Error creating vlan {vlan_id} ({vlan_name}): {self.connection.error.details}",
        )
        log.save()
        return self._error_result(
            f"Error creating vlan {vlan_id}!",
            details=self.connection.error.details,
        )

    def switch_vlan_delete(self, vlan_id: int):
        """Delete a vlan on the device.

        Params:
            vlan_id: the vlan to delete

        Returns:
            (bool, Error)
        """
        dprint("DeviceActions.switch_vlan_delete()")

        ok, error = self._setup("switch_vlan_delete()")
        if not ok:
            return False, error

        if not self.request.user.is_superuser:
            # Only superuser can delete!
            return self._error_result("Access Denied: you need to be SuperUser to delete a VLAN")

        if not self.connection.vlan_exists(vlan_id):
            return self._error_result(f"Vlan {vlan_id} does not exist!")

        # go delete:
        if self.connection.vlan_delete(vlan_id=vlan_id):
            log = self._create_log(
                action=LOG_VLAN_DELETE,
                type=LOG_TYPE_CHANGE,
                description=f"Vlan {vlan_id} deleted.",
            )
            log.save()
            # need to save changes
            self.connection.set_save_needed(True)
            # and save data in session
            self.connection.save_cache()
            counter_increment(COUNTER_VLAN_MANAGE)
            self.switch.update_change()
            return self._success_result(f"Vlan {vlan_id} was deleted!")

        # an error occured:
        log = self._create_log(
            action=LOG_VLAN_DELETE,
            type=LOG_TYPE_ERROR,
            description=f"Error deleting vlan {vlan_id}: {self.connection.error.details}",
        )
        log.save()
        return self._error_result(
            f"Error deleting vlan {vlan_id}!",
            details=self.connection.error.details,
        )

    def switch_vlan_edit(self, vlan_id: int, vlan_name: str):
        """Edit a vlan name on the device.

        Params:
            vlan_id: the vlan to edit
            vlan_name: the new name for the vlan

        Returns:
            (bool, Error)
        """
        dprint("DeviceActions.switch_vlan_edit()")

        ok, error = self._setup("switch_vlan_edit()")
        if not ok:
            return False, error

        if not self.connection.vlan_exists(vlan_id):
            return self._error_result(f"Vlan {vlan_id} does not exist!")

        if not vlan_name:
            return self._error_result("Vlan name can not be empty!")

        if self.connection.vlan_edit(vlan_id=vlan_id, vlan_name=vlan_name):
            log = self._create_log(
                action=LOG_VLAN_EDIT,
                type=LOG_TYPE_CHANGE,
                description=f"Vlan {vlan_id} renamed to '{vlan_name}'",
            )
            log.save()
            # need to save changes
            self.connection.set_save_needed(True)
            # and save data in session
            self.connection.save_cache()
            counter_increment(COUNTER_VLAN_MANAGE)
            self.switch.update_change()
            return self._success_result(f"Updated name for vlan {vlan_id} to '{vlan_name}'")

        # an error occured:
        log = self._create_log(
            action=LOG_VLAN_EDIT,
            type=LOG_TYPE_ERROR,
            description=f"Error updating vlan {vlan_id} name to '{vlan_name}': {self.connection.error.details}",
        )
        log.save()
        return self._error_result(
            f"Error updating vlan {vlan_id}!",
            details=self.connection.error.details,
        )
