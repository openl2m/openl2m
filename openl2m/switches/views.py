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
import time
import traceback
import re

from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.models import User
from django.http import FileResponse
from django.urls import reverse
from django.utils.html import mark_safe
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.template import Template, Context
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View


from switches.actions import (
    perform_interface_admin_change,
    perform_interface_description_change,
    perform_interface_pvid_change,
    perform_interface_poe_change,
    perform_switch_save_config,
    perform_switch_vlan_add,
    perform_switch_vlan_edit,
    perform_switch_vlan_delete,
)

from switches.connect.classes import Error
from switches.models import (
    CommandTemplate,
    Switch,
    SwitchGroup,
    Log,
)
from switches.constants import (
    LOG_TYPE_VIEW,
    LOG_TYPE_CHANGE,
    LOG_TYPE_ERROR,
    LOG_TYPE_COMMAND,
    LOG_TYPE_CHOICES,
    LOG_ACTION_CHOICES,
    LOG_CHANGE_INTERFACE_DOWN,
    LOG_CHANGE_INTERFACE_UP,
    LOG_CHANGE_INTERFACE_POE_DOWN,
    LOG_CHANGE_INTERFACE_POE_UP,
    LOG_CHANGE_INTERFACE_POE_TOGGLE_DOWN_UP,
    LOG_CHANGE_INTERFACE_PVID,
    LOG_CHANGE_INTERFACE_ALIAS,
    LOG_CHANGE_BULK_EDIT,
    LOG_VIEW_SWITCHGROUPS,
    LOG_CONNECTION_ERROR,
    LOG_BULK_EDIT_TASK_START,
    LOG_VIEW_SWITCH,
    LOG_VIEW_ALL_LOGS,
    LOG_VIEW_ADMIN_STATS,
    LOG_VIEW_SWITCH_SEARCH,
    LOG_VIEW_DOWNLOAD_ARP_LLDP,
    LOG_VIEW_DOWNLOAD_INTERFACES,
    LOG_VIEW_TOP_ACTIVITY,
    LOG_EXECUTE_COMMAND,
    LOG_RELOAD_SWITCH,
    INTERFACE_STATUS_NONE,
    BULKEDIT_POE_NONE,
    BULKEDIT_POE_CHOICES,
    BULKEDIT_ALIAS_TYPE_CHOICES,
    BULKEDIT_INTERFACE_CHOICES,
    BULKEDIT_ALIAS_TYPE_REPLACE,
    BULKEDIT_ALIAS_TYPE_APPEND,
    BULKEDIT_POE_DOWN_UP,
    BULKEDIT_POE_CHANGE,
    BULKEDIT_POE_DOWN,
    BULKEDIT_POE_UP,
    LOG_TYPE_WARNING,
    INTERFACE_STATUS_CHANGE,
    INTERFACE_STATUS_DOWN,
    INTERFACE_STATUS_UP,
)
from switches.connect.connector import clear_switch_cache
from switches.connect.connect import get_connection_object
from switches.connect.constants import (
    POE_PORT_ADMIN_ENABLED,
    POE_PORT_ADMIN_DISABLED,
)
from switches.download import create_eth_neighbor_xls_file, create_interfaces_xls_file
from switches.myview import MyView
from switches.permissions import get_group_and_switch, get_connection_if_permitted, get_my_device_groups

from switches.stats import (
    get_environment_info,
    get_database_info,
    get_usage_info,
    get_top_changed_devices,
    get_top_viewed_devices,
    get_top_active_users,
)

from switches.utils import (
    success_page,
    warning_page,
    error_page,
    success_page_by_id,
    error_page_by_id,
    dprint,
    get_from_http_session,
    save_to_http_session,
    get_remote_ip,
    time_duration,
    string_contains_regex,
    string_matches_regex,
    get_choice_name,
)

from users.utils import user_can_bulkedit, user_can_edit_vlans, get_current_users
from counters.models import counter_increment
from counters.constants import (
    COUNTER_CHANGES,
    COUNTER_BULKEDITS,
    COUNTER_ERRORS,
    COUNTER_ACCESS_DENIED,
    COUNTER_COMMANDS,
    COUNTER_VIEWS,
    COUNTER_DETAILVIEWS,
)
from notices.models import Notice


def close_device(request):
    """Close out any session left over from the previous device user was looking at

    Args:
        request: the Request() object for the user's web session.

    Returns:
        n/a
    """

    # if we came here from a previous switch, call _close_device() to clear out old session as needed.
    if 'switch_id' in request.session.keys():
        dprint(f"CLOSING DEVICE: id={request.session['switch_id']}")
        # instantiate the previous device Connector() one more time to proper close sessions...
        try:
            switch = get_object_or_404(Switch, pk=request.session['switch_id'])
            conn = get_connection_object(request=request, group=False, switch=switch)
            conn._close_device()
            del conn
        except Exception as err:
            dprint(f"ERROR CLOSING DEVICE: {err}\n{traceback.format_exc()}\n")
            # log it, but ignore otherwize...
            log = Log(
                user=request.user,
                ip_address=get_remote_ip(request),
                switch=switch,
                # group=False,
                action=LOG_CONNECTION_ERROR,
                type=LOG_TYPE_ERROR,
                description=f"ERROR: Main menu trying to _close_device() for id {request.session['switch_id']}: {err}",
            )
            log.save()


class Switches(LoginRequiredMixin, View):
    """
    This is the "home view", at "/"
    It shows the list of switches a user has access to
    """

    def post(
        self,
        request,
    ):
        return self.get(request=request)

    def get(
        self,
        request,
    ):
        dprint("Switches() - GET called")

        template_name = "home.html"

        close_device(request=request)

        # clear session cache, so we re-read switches as needed
        clear_switch_cache(request)

        # save remote ip in session, so we can use it in current user display!
        save_to_http_session(request, "remote_ip", get_remote_ip(request))

        # find the groups with switches that we have rights to:
        groups = get_my_device_groups(request=request)
        save_to_http_session(request, "permissions", groups)

        # log my activity
        log = Log(
            user=request.user,
            ip_address=get_remote_ip(request),
            action=LOG_VIEW_SWITCHGROUPS,
            description="Viewing switch groups",
            type=LOG_TYPE_VIEW,
        )
        log.save()

        # are there any notices to users?
        notices = Notice.objects.active_notices()
        if notices:
            for notice in notices:
                messages.add_message(request=request, level=notice.priority, message=notice.content)

        # calculate column width, if set. Bootstrap uses 12 grid columns per page, max width we use is 2 grids
        if settings.TOPMENU_MAX_COLUMNS > 6:
            col_width = 2
            max_columns = 6
        else:
            col_width = int(12 / settings.TOPMENU_MAX_COLUMNS)
            max_columns = settings.TOPMENU_MAX_COLUMNS

        # render the template
        return render(
            request=request,
            template_name=template_name,
            context={
                "is_top_menu": True,
                "groups": groups,
                "group_count": len(groups),
                "col_width": col_width,
                "max_columns": max_columns,
            },
        )


class SwitchSearch(LoginRequiredMixin, View):
    """
    search for a switch by name
    """

    def post(
        self,
        request,
    ):
        dprint("SwitchSearch() - POST called")

        if not settings.SWITCH_SEARCH_FORM:
            # we should not be here!
            return redirect(reverse("switches:groups"))

        # close any previous device
        close_device(request=request)

        # clear session cache, so we re-read switches as needed
        clear_switch_cache(request=request)

        search = str(request.POST.get("switchname", ""))
        # remove leading and trailing white spaceA
        search = search.strip()
        if not search:
            return redirect(reverse("switches:groups"))

        template_name = "search_results.html"

        # log my activity
        log = Log(
            user=request.user,
            ip_address=get_remote_ip(request),
            action=LOG_VIEW_SWITCH_SEARCH,
            description=f"Searching for switch '{search}'",
            type=LOG_TYPE_VIEW,
        )
        log.save()

        results = []
        result_groups = {}
        warning = False
        permissions = get_from_http_session(request, "permissions")

        if permissions and isinstance(permissions, dict):
            for group_id, group in permissions.items():
                if isinstance(group, dict):
                    group_name = group['name']
                    for switch_id, switch in group['members'].items():
                        name = switch['name']
                        hostname = switch['hostname']
                        description = switch['description']
                        default_view = switch['default_view']
                        # now check the name, hostname for the search pattern:
                        try:
                            if re.search(search, name, re.IGNORECASE) or re.search(search, hostname, re.IGNORECASE):
                                # regular user, add all occurances of device (likely just one!)
                                results.append(
                                    (str(group_id), str(switch_id), name, description, default_view, group_name)
                                )
                                result_groups[group_name] = True
                        except Exception:
                            # invalid search, just ignore!
                            warning = f"{search} - This is an invalid search pattern!"
                            break

        # render the template
        return render(
            request,
            template_name,
            {
                'warning': warning,
                'search': search,
                'results': results,
                'results_count': len(results),
                'group_count': len(result_groups),
            },
        )


class SwitchBasics(LoginRequiredMixin, View):
    """
    "basic" switch view, i.e. interface data only.
    Simply call switch_view() with proper parameter
    """

    def get(
        self,
        request,
        group_id,
        switch_id,
    ):
        dprint("SwitchBasics() - GET called")
        counter_increment(COUNTER_VIEWS)
        return switch_view(request=request, group_id=group_id, switch_id=switch_id, view="basic")

    def post(
        self,
        request,
        group_id,
        switch_id,
    ):
        dprint("SwitchBasics() - POST called")
        counter_increment(COUNTER_VIEWS)
        return switch_view(request=request, group_id=group_id, switch_id=switch_id, view="basic")


class SwitchDetails(LoginRequiredMixin, MyView):
    """
    "details" switch view, i.e. with Ethernet/ARP/LLDP data.
    Simply call switch_view() with proper parameter
    """

    def get(
        self,
        request,
        group_id,
        switch_id,
    ):
        dprint("SwitchDetails() - GET called")
        counter_increment(COUNTER_DETAILVIEWS)
        return switch_view(request=request, group_id=group_id, switch_id=switch_id, view="arp_lldp")

    def post(
        self,
        request,
        group_id,
        switch_id,
    ):
        dprint("SwitchDetails() - POST called")
        counter_increment(COUNTER_DETAILVIEWS)
        return switch_view(request=request, group_id=group_id, switch_id=switch_id, view="arp_lldp")


def switch_view(
    request,
    group_id,
    switch_id,
    view,
    command_id=-1,
    interface_name="",
    command_string="",
    command_template=False,
):
    """
    This shows the various data about a switch, either from a new SNMP read,
    from cached OID data, or an SSH command.
    This is includes enough to enable/disable interfaces and power,
    and change vlans. Depending on view, there may be more data needed,
    such as ethernet, arp & lldp tables.
    """

    template_name = "switch.html"

    group, switch = get_group_and_switch(request=request, group_id=group_id, switch_id=switch_id)

    log = Log(
        user=request.user,
        ip_address=get_remote_ip(request),
        switch=switch,
        group=group,
        action=LOG_VIEW_SWITCH,
        type=LOG_TYPE_VIEW,
        description=f"Viewing device ({view})",
    )

    if group is None or switch is None:
        log.type = LOG_TYPE_ERROR
        log.description = "Permission denied! ()"
        log.save()
        error = Error()
        error.status = True
        error.description = "Access denied!"
        counter_increment(COUNTER_ACCESS_DENIED)
        return error_page(request=request, group=False, switch=False, error=error)

    try:
        conn = get_connection_object(request, group, switch)
    except Exception:
        log.type = LOG_TYPE_ERROR
        log.action = LOG_CONNECTION_ERROR
        log.description = f"CONNECTION ERROR: Viewing device ({view})"
        log.save()
        error = Error()
        error.description = "We could not communicate with this device. Please contact your administrator to make sure the device is properly configured in OpenL2M!"
        error.details = traceback.format_exc()
        return error_page(request=request, group=group, switch=switch, error=error)

    # catch errors in case not trapped in drivers
    try:
        if not conn.get_basic_info():
            # errors
            log.type = LOG_TYPE_ERROR
            log.description = "ERROR in get_basic_switch_info()"
            log.save()
            return error_page(request=request, group=group, switch=switch, error=conn.error)

    except Exception as e:
        log.type = LOG_TYPE_ERROR
        log.description = (
            f"CAUGHT UNTRAPPED ERROR in get_basic_switch_info(): {repr(e)} ({str(type(e))})\n{traceback.format_exc()}"
        )
        dprint(log.description)
        log.save()
        return error_page(request=request, group=group, switch=switch, error=conn.error)

    dprint("Basic Info OK")

    if view == "arp_lldp":
        # catch errors in case not trapped in drivers
        try:
            if not conn.get_client_data():
                log.type = LOG_TYPE_ERROR
                log.description = "ERROR get_client_data()"
                log.save()
                # don't render error, since we have already read the basic interface data
                # Note that errors are already added to warnings!
                # return error_page(request=request, group=group, switch=switch, error=conn.error)
            dprint("ARP-LLDP Info OK")
        except Exception as e:
            log.type = LOG_TYPE_ERROR
            log.description = (
                f"CAUGHT UNTRAPPED ERROR in get_client_data(): {repr(e)} ({str(type(e))})\n{traceback.format_exc()}"
            )
            dprint(log.description)
            log.save()
            return error_page(request=request, group=group, switch=switch, error=conn.error)

    # done with reading switch data, so save cachable/session data
    conn.save_cache()

    # does this switch have any commands defined?
    cmd = False
    # check that we can process commands, and have valid commands assigned to switch
    if command_id > -1:
        # Exexute a specific Command object by ID, note rights are checked in run_command()!
        dprint("CALLING RUN_COMMAND()")
        counter_increment(COUNTER_COMMANDS)
        cmd = conn.run_command(command_id=command_id, interface_name=interface_name)
        if conn.error.status:
            # log it!
            log.type = LOG_TYPE_ERROR
            log.action = LOG_EXECUTE_COMMAND
            log.description = f"{cmd['error_descr']}: {cmd['error_details']}"
        else:
            # success !
            switch.update_command()
            log.type = LOG_TYPE_COMMAND
            log.action = LOG_EXECUTE_COMMAND
            log.description = cmd["command"]
        log.save()
    elif command_string:
        dprint("CALLING RUN_COMMAND_STRING")
        counter_increment(COUNTER_COMMANDS)
        cmd = conn.run_command_string(command_string=command_string)
        dprint(f"OUTPUT = {cmd}")
        if conn.error.status:
            # log it!
            log.type = LOG_TYPE_ERROR
            log.action = LOG_EXECUTE_COMMAND
            log.description = f"{cmd['error_descr']}: {cmd['error_details']}"
            log.save()
        else:
            # success !
            switch.update_command()
            log.type = LOG_TYPE_COMMAND
            log.action = LOG_EXECUTE_COMMAND
            log.description = cmd["command"]
            log.save()
            # if the result of a command template, we may need to parse the output:
            if command_template:
                # do we need to match output to show match/fail result?
                output = cmd["output"]
                if command_template.output_match_regex:
                    if string_contains_regex(cmd["output"], command_template.output_match_regex):
                        cmd["output"] = (
                            command_template.output_match_text if command_template.output_match_text else "OK!"
                        )
                    else:
                        cmd["output"] = (
                            command_template.output_fail_text if command_template.output_fail_text else "FAIL!"
                        )
                # do we need to filter (original) output to keep only matching lines?
                if command_template.output_lines_keep_regex:
                    matched_lines = ""
                    lines = output.splitlines()
                    for line in lines:
                        # we can probably improve performance by compiling the regex first...
                        if string_contains_regex(line, command_template.output_lines_keep_regex):
                            matched_lines = f"{matched_lines}\n{line}"
                    if matched_lines:
                        cmd["output"] += "\nPartial output:\n" + matched_lines

    else:
        # log the access:
        log.save()

    # get recent "non-viewing" activity for this switch
    # for now, show most recent 25 activities
    logs = (
        Log.objects.all()
        .filter(switch=switch, type__gt=LOG_TYPE_VIEW)
        .order_by("-timestamp")[: settings.RECENT_SWITCH_LOG_COUNT]
    )

    time_since_last_read = time_duration(time.time() - conn.basic_info_read_timestamp)

    # finally, verify what this user can do:
    bulk_edit = not conn.read_only and len(conn.interfaces) and user_can_bulkedit(request.user, group, switch)
    edit_vlans = (
        not conn.read_only
        and conn.can_edit_vlans
        and len(conn.interfaces)
        and user_can_edit_vlans(request.user, group, switch)
    )

    log_title = "Recent Activity"

    return render(
        request,
        template_name,
        {
            "group": group,
            "switch": switch,
            "connection": conn,
            "logs": logs,
            "log_title": log_title,
            "logs_link": True,
            "view": view,
            "cmd": cmd,
            "bulk_edit": bulk_edit,
            "edit_vlans": edit_vlans,
            "time_since_last_read": time_since_last_read,
        },
    )


#
# Bulk Edit interfaces on a switch
#
class SwitchBulkEdit(LoginRequiredMixin, View):
    """
    Change several interfaces at once.
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
    ):
        dprint("SwitchBulkEdit() - POST called")
        group, switch = get_group_and_switch(request=request, group_id=group_id, switch_id=switch_id)

        remote_ip = get_remote_ip(request)
        log = Log(
            user=request.user,
            ip_address=remote_ip,
            switch=switch,
            group=group,
            action=LOG_VIEW_SWITCH,
            type=LOG_TYPE_VIEW,
        )

        if group is None or switch is None:
            log.type = LOG_TYPE_ERROR
            log.description = "Permission denied!"
            log.save()
            error = Error()
            error.status = True
            error.description = "Access denied!"
            counter_increment(COUNTER_ACCESS_DENIED)
            return error_page(request=request, group=False, switch=False, error=error)

        counter_increment(COUNTER_BULKEDITS)

        # read the submitted form data:
        interface_change = int(request.POST.get("bulk_interface_change", INTERFACE_STATUS_NONE))
        poe_choice = int(request.POST.get("bulk_poe_change", BULKEDIT_POE_NONE))
        new_pvid = int(request.POST.get("bulk_vlan_change", -1))
        new_description = str(request.POST.get("bulk_new_description", ""))
        new_description_type = int(request.POST.get("bulk_new_description_type", BULKEDIT_ALIAS_TYPE_REPLACE))
        interface_list = request.POST.getlist("bulk_interface_list")

        # was anything submitted?
        if len(interface_list) == 0:
            return warning_page(
                request=request,
                group=group,
                switch=switch,
                description=mark_safe("Please select at least 1 interface!"),
            )

        if (
            interface_change == INTERFACE_STATUS_NONE
            and poe_choice == BULKEDIT_POE_NONE
            and new_pvid < 0
            and not new_description
        ):
            return warning_page(
                request=request,
                group=group,
                switch=switch,
                description=mark_safe("Please select at least 1 thing to change!"),
            )

        # perform some checks on valid data first:
        errors = []

        # check if the new description/description is allowed:
        if (
            new_description
            and new_description_type == BULKEDIT_ALIAS_TYPE_REPLACE
            and settings.IFACE_ALIAS_NOT_ALLOW_REGEX
        ):
            match = re.match(settings.IFACE_ALIAS_NOT_ALLOW_REGEX, new_description)
            if match:
                log = Log(
                    user=request.user,
                    ip_address=remote_ip,
                    switch=switch,
                    group=group,
                    type=LOG_TYPE_ERROR,
                    action=LOG_CHANGE_BULK_EDIT,
                    description=f"Description not allowed: {new_description}",
                )
                log.save()
                new_description = ""
                counter_increment(COUNTER_ERRORS)
                errors.append(f"The description is not allowed: {new_description}")

        # now we are ready to get a device connection
        try:
            conn = get_connection_object(request, group, switch)
        except Exception:
            log = Log(
                user=request.user,
                ip_address=remote_ip,
                switch=switch,
                group=group,
                action=LOG_CONNECTION_ERROR,
                type=LOG_TYPE_ERROR,
                description="Could not get connection",
            )
            log.save()
            error = Error()
            error.description = "Could not get connection. Please contact your administrator to make sure switch data is correct in the database!"
            error.details = "This is likely a configuration error, such as wrong SNMP settings."
            return error_page(request=request, group=group, switch=switch, error=error)

        # safety-check: is the new PVID allowed:
        if new_pvid > 0:
            conn._set_allowed_vlans()
            if new_pvid not in conn.allowed_vlans.keys():
                log = Log(
                    user=request.user,
                    ip_address=remote_ip,
                    switch=switch,
                    group=group,
                    type=LOG_TYPE_ERROR,
                    action=LOG_CHANGE_BULK_EDIT,
                    description=f"New vlan '{new_pvid}' is not allowed!",
                )
                log.save()
                new_pvid = -1  # force no change!
                errors.append(f"New vlan '{new_pvid}' is not allowed!")
                counter_increment(COUNTER_ERRORS)

        if len(errors) > 0:
            error = Error()
            error.description = "Some form values were invalid, please correct and resubmit!"
            error.details = mark_safe("\n<br>".join(errors))
            return error_page(request=request, group=group, switch=switch, error=error)

        # get the name of the interfaces as well (with the submitted if_key values)
        # so that we can show the names in the Log() objects
        # additionally, also get the current state, to be able to "undo" the update
        interfaces = {}  # dict() of interfaces to bulk edit
        for if_key in interface_list:
            dprint(f"BulkEdit for {if_key}")
            interface = conn.get_interface_by_key(if_key)
            if interface:
                interfaces[if_key] = interface.name

        # handle regular submit, execute now!
        results = bulkedit_processor(
            request=request,
            group=group,
            switch=switch,
            conn=conn,
            interface_change=interface_change,
            poe_choice=poe_choice,
            new_pvid=new_pvid,
            new_description=new_description,
            new_description_type=new_description_type,
            interfaces=interfaces,
        )

        # indicate we need to save config!
        if results["success_count"] > 0:
            conn.set_save_needed(True)
            # and save data in session
            conn.save_cache()

        # now build the results page from the outputs
        result_str = "\n<br>".join(results["outputs"])
        description = f"\n<div><strong>Bulk-Edit Results:</strong></div>\n<br>{result_str}"
        if results["error_count"] > 0:
            err = Error()
            err.description = "Bulk-Edit errors"
            err.details = mark_safe(description)
            return error_page(request=request, group=group, switch=switch, error=err)

        return success_page(request, group, switch, mark_safe(description))


#
# Note: there is duplicate code here!
#    This needs to be updated to use the actions.* functions.
#


def bulkedit_processor(
    request,
    group,
    switch,
    conn,
    interface_change,
    poe_choice,
    new_pvid,
    new_description,
    new_description_type,
    interfaces,
):
    """
    Function to handle the bulk edit processing, from form-submission or scheduled job.
    This will log each individual action per interface.
    Returns the number of successful action, number of error actions, and
    a list of outputs with text information about each action.
    """

    remote_ip = get_remote_ip(request)

    # log bulk edit arguments:
    log = Log(
        user=request.user,
        switch=switch,
        group=group,
        ip_address=remote_ip,
        action=LOG_BULK_EDIT_TASK_START,
        description=f"Interface Status={get_choice_name(BULKEDIT_INTERFACE_CHOICES, interface_change)}, "
        f"PoE Status={get_choice_name(BULKEDIT_POE_CHOICES, poe_choice)}, "
        f"Vlan={new_pvid}, "
        f"Descr Type={get_choice_name(BULKEDIT_ALIAS_TYPE_CHOICES, new_description_type)}, "
        f"Descr={new_description}",
        type=LOG_TYPE_CHANGE,
    )
    log.save()

    # this needs work:
    # conn = get_connection_object(request, group, switch)
    # if not request:
    # running asynchronously (as task), we need to read the device
    # to get access to interfaces.
    #        conn.get_basic_info()

    # now do the work, and log each change
    iface_count = 0
    success_count = 0
    error_count = 0
    outputs = []  # description of any errors found
    for if_key in interfaces:
        iface = conn.get_interface_by_key(if_key)
        if not iface:
            error_count += 1
            outputs.append(f"ERROR: (BulkEdit) interface for index '{if_key}' not found!")
            continue
        iface_count += 1

        # now check all the things we could be changing,
        # start with UP/DOWN state:
        if interface_change != INTERFACE_STATUS_NONE:
            log = Log(
                user=request.user,
                ip_address=remote_ip,
                if_name=iface.name,
                switch=switch,
                group=group,
            )
            current_state = iface.admin_status
            if interface_change == INTERFACE_STATUS_CHANGE:
                if iface.admin_status:
                    new_state = False
                    new_state_name = "Down"
                    log.action = LOG_CHANGE_INTERFACE_DOWN
                else:
                    new_state = True
                    new_state_name = "Up"
                    log.action = LOG_CHANGE_INTERFACE_UP

            elif interface_change == INTERFACE_STATUS_DOWN:
                new_state = False
                new_state_name = "Down"
                log.action = LOG_CHANGE_INTERFACE_DOWN

            elif interface_change == INTERFACE_STATUS_UP:
                new_state = True
                new_state_name = "Up"
                log.action = LOG_CHANGE_INTERFACE_UP

            # are we actually making a change?
            if new_state != current_state:
                # yes, apply the change:
                retval = conn.set_interface_admin_status(iface, new_state)
                if retval:
                    success_count += 1
                    log.type = LOG_TYPE_CHANGE
                    log.description = f"Interface {iface.name}: Admin set to {new_state_name}"
                    counter_increment(COUNTER_CHANGES)
                    conn.switch.update_change()
                else:
                    error_count += 1
                    log.type = LOG_TYPE_ERROR
                    log.description = f"Interface {iface.name}: Admin {new_state_name} ERROR: {conn.error.description}"
                    counter_increment(COUNTER_ERRORS)
            else:
                # already in wanted admin state:
                log.type = LOG_TYPE_CHANGE
                log.description = f"Interface {iface.name}: Ignored - already {new_state_name}"
            outputs.append(log.description)
            log.save()

        # next work on PoE state:
        if poe_choice != BULKEDIT_POE_NONE:
            if not iface.poe_entry:
                outputs.append(f"Interface {iface.name}: Ignored - not PoE capable")
            else:
                log = Log(
                    user=request.user,
                    ip_address=remote_ip,
                    if_name=iface.name,
                    switch=switch,
                    group=group,
                )
                current_state = iface.poe_entry.admin_status
                if poe_choice == BULKEDIT_POE_DOWN_UP:
                    # Down / Up on interfaces with PoE Enabled:
                    if iface.poe_entry.admin_status == POE_PORT_ADMIN_ENABLED:
                        log.action = LOG_CHANGE_INTERFACE_POE_TOGGLE_DOWN_UP
                        # First disable PoE
                        if not conn.set_interface_poe_status(iface, POE_PORT_ADMIN_DISABLED):
                            log.description = (
                                f"ERROR: Toggle-Disable PoE on interface {iface.name} - {conn.error.description}"
                            )
                            log.type = LOG_TYPE_ERROR
                            outputs.append(log.description)
                            log.save()
                            counter_increment(COUNTER_ERRORS)
                        else:
                            # successful power down
                            counter_increment(COUNTER_CHANGES)
                            conn.switch.update_change()
                            # now delay
                            time.sleep(settings.POE_TOGGLE_DELAY)
                            # Now enable PoE again...
                            if not conn.set_interface_poe_status(iface, POE_PORT_ADMIN_ENABLED):
                                log.description = (
                                    f"ERROR: Toggle-Enable PoE on interface {iface.name} - {conn.error.description}"
                                )
                                log.type = LOG_TYPE_ERROR
                                outputs.append(log.description)
                                log.save()
                                counter_increment(COUNTER_ERRORS)
                            else:
                                # all went well!
                                success_count += 1
                                log.type = LOG_TYPE_CHANGE
                                log.description = f"Interface {iface.name}: PoE Toggle Down/Up OK"
                                outputs.append(log.description)
                                log.save()
                                counter_increment(COUNTER_CHANGES)
                                conn.switch.update_change()
                    else:
                        outputs.append(f"Interface {iface.name}: PoE Down/Up IGNORED, PoE NOT enabled")

                else:
                    # just enable or disable:
                    if poe_choice == BULKEDIT_POE_CHANGE:
                        # the PoE index is kept in the iface.poe_entry
                        if iface.poe_entry.admin_status == POE_PORT_ADMIN_ENABLED:
                            new_state = POE_PORT_ADMIN_DISABLED
                            new_state_name = "Disabled"
                            log.action = LOG_CHANGE_INTERFACE_POE_DOWN
                        else:
                            new_state = POE_PORT_ADMIN_ENABLED
                            new_state_name = "Enabled"
                            log.action = LOG_CHANGE_INTERFACE_POE_UP

                    elif poe_choice == BULKEDIT_POE_DOWN:
                        new_state = POE_PORT_ADMIN_DISABLED
                        new_state_name = "Disabled"
                        log.action = LOG_CHANGE_INTERFACE_POE_DOWN

                    elif poe_choice == BULKEDIT_POE_UP:
                        new_state = POE_PORT_ADMIN_ENABLED
                        new_state_name = "Enabled"
                        log.action = LOG_CHANGE_INTERFACE_POE_UP

                    # are we actually making a change?
                    if new_state != current_state:
                        # yes, go do it:
                        if not conn.set_interface_poe_status(iface, new_state):
                            error_count += 1
                            log.type = LOG_TYPE_ERROR
                            log.description = (
                                f"Interface {iface.name}: PoE {new_state_name} ERROR: {conn.error.description}"
                            )
                            outputs.append(log.description)
                            log.save()
                            counter_increment(COUNTER_ERRORS)
                        else:
                            success_count += 1
                            log.type = LOG_TYPE_CHANGE
                            log.description = f"Interface {iface.name}: PoE {new_state_name}"
                            outputs.append(log.description)
                            log.save()
                            counter_increment(COUNTER_CHANGES)
                            conn.switch.update_change()
                    else:
                        # already in wanted power state:
                        outputs.append(f"Interface {iface.name}: Ignored, PoE already {new_state_name}")

        # do we want to change the untagged vlan:
        if new_pvid > 0:
            if iface.lacp_master_index > 0:
                # LACP member interface, we cannot edit the vlan!
                log = Log(
                    user=request.user,
                    ip_address=remote_ip,
                    if_name=iface.name,
                    switch=switch,
                    group=group,
                    type=LOG_TYPE_WARNING,
                    action=LOG_CHANGE_INTERFACE_PVID,
                    description=f"Interface {iface.name}: LACP Member, vlan set to {new_pvid} IGNORED!",
                )
                outputs.append(log.description)
                log.save()
            else:
                # make sure we cast the proper type here! Ie this needs an Integer()
                log = Log(
                    user=request.user,
                    ip_address=remote_ip,
                    if_name=iface.name,
                    switch=switch,
                    group=group,
                    action=LOG_CHANGE_INTERFACE_PVID,
                )
                if new_pvid != iface.untagged_vlan:
                    # new vlan, go set it:
                    if not conn.set_interface_untagged_vlan(iface, new_pvid):
                        error_count += 1
                        log.type = LOG_TYPE_ERROR
                        log.description = f"Interface {iface.name}: Vlan change ERROR: {conn.error.description} - {conn.error.details}"
                        outputs.append(f"Interface {iface.name}: Vlan change ERROR: {conn.error.description}")
                        counter_increment(COUNTER_ERRORS)
                    else:
                        success_count += 1
                        log.type = LOG_TYPE_CHANGE
                        log.description = f"Interface {iface.name}: Vlan set to {new_pvid}"
                        outputs.append(log.description)
                    log.save()
                    counter_increment(COUNTER_CHANGES)
                    conn.switch.update_change()
                else:
                    # already on desired vlan:
                    outputs.append(f"Interface {iface.name}: Ignored, vlan already {new_pvid}")

        # tired of the old interface description?
        if new_description:
            iface_new_description = ""
            # what are we supposed to do with the description/description?
            if new_description_type == BULKEDIT_ALIAS_TYPE_APPEND:
                iface_new_description = f"{iface.description} {new_description}"
                # outputs.append(f"Interface {iface.name}: Description Append: {iface_new_description}")
            elif new_description_type == BULKEDIT_ALIAS_TYPE_REPLACE:
                # check if the original description starts with a string we have to keep:
                if settings.IFACE_ALIAS_KEEP_BEGINNING_REGEX:
                    keep_format = f"(^{settings.IFACE_ALIAS_KEEP_BEGINNING_REGEX})"
                    match = re.match(keep_format, iface.description)
                    if match:
                        # beginning match, but check if new submitted description matches requirement:
                        match_new = re.match(keep_format, new_description)
                        if not match_new:
                            # required start string NOT found on new description, so prepend it!
                            iface_new_description = f"{match[1]} {new_description}"
                        else:
                            # new description matches beginning format, keep as is:
                            iface_new_description = new_description
                    else:
                        # no beginning match, just set new description:
                        iface_new_description = new_description
                else:
                    # nothing special, just set new description:
                    iface_new_description = new_description

            # elif new_description_type == BULKEDIT_ALIAS_TYPE_PREPEND:
            # To be implemented

            log = Log(
                user=request.user,
                ip_address=remote_ip,
                if_name=iface.name,
                switch=switch,
                group=group,
                action=LOG_CHANGE_INTERFACE_ALIAS,
            )
            if not conn.set_interface_description(iface, iface_new_description):
                error_count += 1
                log.type = LOG_TYPE_ERROR
                log.description = (
                    f"Interface {iface.name}: Descr ERROR: {conn.error.description} - {conn.error.details}"
                )
                log.save()
                counter_increment(COUNTER_ERRORS)
                outputs.append(f"Interface {iface.name}: Descr ERROR: {conn.error.description}")
            else:
                success_count += 1
                log.type = LOG_TYPE_CHANGE
                log.description = f"Interface {iface.name}: Descr set OK"
                counter_increment(COUNTER_CHANGES)
                conn.switch.update_change()
                outputs.append(log.description)
            log.save()

    # log final results
    log = Log(
        user=request.user,
        ip_address=remote_ip,
        switch=switch,
        group=group,
        type=LOG_TYPE_CHANGE,
        action=LOG_CHANGE_BULK_EDIT,
    )
    if error_count > 0:
        log.type = LOG_TYPE_ERROR
        log.description = "Bulk Edits had errors! (see previous entries)"
    else:
        log.description = "Bulk Edits OK!"
    log.save()

    results = {
        "success_count": success_count,
        "error_count": error_count,
        "outputs": outputs,
    }
    return results


#
# Manage vlans on a device
#
class SwitchVlanManage(LoginRequiredMixin, View):
    """
    Manage vlan to a device. Form data will be POST-ed.

    Params:
        request:    HttpRequest() object
        group_id (int): SwitchGroup() pk
        switch_id (int): Switch() pk

    Returns:
        render() via success_page or error_page with appropriate success or failure info.
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
    ):
        dprint("SwitchVlanManage() - POST called")

        # parse form items, validate vlan id:
        try:
            vlan_id = int(request.POST.get("vlan_id", -1))
        except:
            # on any error, set vlan = -1:
            vlan_id = -1
        # and vlan name:
        vlan_name = str(request.POST.get("vlan_name", "")).strip()

        if request.POST.get("vlan_create"):
            dprint("switch_vlan_manage(create)")
            retval, info = perform_switch_vlan_add(
                request=request, group_id=group_id, switch_id=switch_id, vlan_id=vlan_id, vlan_name=vlan_name
            )
            if not retval:
                return error_page_by_id(request=request, group_id=group_id, switch_id=switch_id, error=info)
            return success_page_by_id(request, group_id=group_id, switch_id=switch_id, message=info.description)

        if request.POST.get("vlan_edit"):
            dprint("switch_vlan_manage(edit)")
            retval, info = perform_switch_vlan_edit(
                request=request, group_id=group_id, switch_id=switch_id, vlan_id=vlan_id, vlan_name=vlan_name
            )
            if not retval:
                return error_page_by_id(request=request, group_id=group_id, switch_id=switch_id, error=info)
            return success_page_by_id(request, group_id=group_id, switch_id=switch_id, message=info.description)

        if request.POST.get("vlan_delete"):
            dprint("switch_vlan_manage(delete)")
            retval, info = perform_switch_vlan_delete(
                request=request, group_id=group_id, switch_id=switch_id, vlan_id=vlan_id
            )
            if not retval:
                return error_page_by_id(request=request, group_id=group_id, switch_id=switch_id, error=info)
            return success_page_by_id(request, group_id=group_id, switch_id=switch_id, message=info.description)

        error = Error()
        error.status = True
        error.description = f"UNKNOWN vlan management action: POST={dict(request.POST.items())}"
        return error_page_by_id(request=request, group_id=group_id, switch_id=switch_id, error=error)


#
# Change admin status, ie port Enable/Disable
#
class InterfaceAdminChange(LoginRequiredMixin, MyView):
    """
    Toggle the admin status of an interface, ie admin up or down.
    Params:
        request:  HttpRequest() object
        group_id: (int) the pk of the SwitchGroup()
        switch_id: (int) the pk of the Switch()
        interface_name: (str) the key or to the Interface() in the list of Interface()s
        new_state: (int) the desired state, 0=DOWN, 1=UP

    Returns:
        renders either OK or Error page, depending permissions and result.
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
        interface_name,
        new_state,
    ):
        dprint("InterfaceAdminChange() - POST called")
        retval, info = perform_interface_admin_change(
            request=request,
            group_id=group_id,
            switch_id=switch_id,
            interface_key=interface_name,
            new_state=bool(new_state),
        )
        if not retval:
            return error_page_by_id(request=request, group_id=group_id, switch_id=switch_id, error=info)

        # we don't know the name of the interface, only the key or id.
        # message = f"Interface {interface_name} description changed"
        # message = f"Interface description changed"
        return success_page_by_id(request=request, group_id=group_id, switch_id=switch_id, message=info.description)


class InterfaceDescriptionChange(LoginRequiredMixin, View):
    """
    Change the description on an interfaces.

    Params:
        request:  HttpRequest() object
        group_id: (int) the pk of the SwitchGroup()
        switch_id: (int) the pk of the Switch()
        interface_name: (str) the key or to the Interface() in the list of Interface()s

    Returns:
        renders either OK or Error page, depending permissions and result.
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
        interface_name,
    ):
        dprint("InterfaceDescriptionChange() - POST called")

        # read the submitted form data:
        # new_description = str(request.POST.get("new_description", ""))
        try:
            description = request.POST['new_description']
        except Exception:
            error = Error()
            error.description = "Missing required parameter: 'new_description'"
            return error_page_by_id(request=request, group_id=group_id, switch_id=switch_id, error=error)

        retval, error = perform_interface_description_change(
            request=request,
            group_id=group_id,
            switch_id=switch_id,
            interface_key=interface_name,
            new_description=description,
        )
        if not retval:
            return error_page_by_id(request=request, group_id=group_id, switch_id=switch_id, error=error)

        # we don't know the name of the interface, only the key or id.
        # message = f"Interface {interface_name} description changed"
        message = "Interface description changed"
        return success_page_by_id(request, group_id=group_id, switch_id=switch_id, message=message)


class InterfacePvidChange(LoginRequiredMixin, View):
    """
    Change the PVID untagged vlan on an interfaces.
    This still needs to handle dot1q trunked ports.

    Params:
        request:  HttpRequest() object
        group_id: (int) the pk of the SwitchGroup()
        switch_id: (int) the pk of the Switch()
        interface_name: (str) the key or to the Interface() in the list of Interface()s

    Returns:
        renders either OK or Error page, depending permissions and result.
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
        interface_name,
    ):
        dprint("InterfacePvidChange() - POST called")

        # read the submitted form data:
        try:
            new_pvid = int(request.POST.get('new_pvid'))
        except Exception:
            error = Error()
            error.description = "Missing required parameter: 'new_pvid'"
            return error_page_by_id(request=request, group_id=group_id, switch_id=switch_id, error=error)

        retval, info = perform_interface_pvid_change(
            request=request,
            group_id=group_id,
            switch_id=switch_id,
            interface_key=interface_name,
            new_pvid=new_pvid,
        )
        if not retval:
            return error_page_by_id(request=request, group_id=group_id, switch_id=switch_id, error=info)

        return success_page_by_id(request, group_id=group_id, switch_id=switch_id, message=info.description)


#
# Change PoE status, i.e. port power Enable/Disable
#
class InterfacePoeChange(LoginRequiredMixin, MyView):
    """
    Change the PoE status of an interfaces.
    This still needs to be tested for propper PoE port to interface ifIndex mappings.

    Params:
        request:  HttpRequest() object
        group_id: (int) the pk of the SwitchGroup()
        switch_id: (int) the pk of the Switch()
        interface_name: (str) the key or to the Interface() in the list of Interface()s
        new_state: (int) either POE_PORT_ADMIN_ENABLED (1) or POE_PORT_ADMIN_DISABLED (2).

    Returns:
        renders either OK or Error page, depending permissions and result.
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
        interface_name,
        new_state,
    ):
        dprint("InterfacePoeChange() - POST called")

        # if new_state == POE_PORT_ADMIN_ENABLED:
        #     enable = True
        # else:
        #     enable = False
        enable = new_state == POE_PORT_ADMIN_ENABLED

        retval, info = perform_interface_poe_change(
            request=request,
            group_id=group_id,
            switch_id=switch_id,
            interface_key=interface_name,
            new_state=enable,
        )
        if not retval:
            return error_page_by_id(request=request, group_id=group_id, switch_id=switch_id, error=info)

        return success_page_by_id(request, group_id=group_id, switch_id=switch_id, message=info.description)


#
# Toggle PoE status Down then Up
#
class InterfacePoeDownUp(LoginRequiredMixin, MyView):
    """
    Toggle the PoE status of an interfaces. I.e disable, wait some, then enable again.
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
        interface_name,
    ):
        dprint("InterfacePoeDownUp() - POST called")
        # disable power first:
        retval, info = perform_interface_poe_change(
            request=request,
            group_id=group_id,
            switch_id=switch_id,
            interface_key=interface_name,
            new_state=False,
        )
        if not retval:
            return error_page_by_id(request=request, group_id=group_id, switch_id=switch_id, error=info)

        # delay to let the device cold-boot properly
        time.sleep(settings.POE_TOGGLE_DELAY)

        # and enable again:
        retval, info = perform_interface_poe_change(
            request=request,
            group_id=group_id,
            switch_id=switch_id,
            interface_key=interface_name,
            new_state=True,
        )
        if not retval:
            return error_page_by_id(request=request, group_id=group_id, switch_id=switch_id, error=info)

        description = "Interface PoE was toggled!"
        return success_page_by_id(request=request, group_id=group_id, switch_id=switch_id, message=description)


class SwitchSaveConfig(LoginRequiredMixin, MyView):
    """
    This will save the running config to flash/startup/whatever, on supported platforms
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
    ):
        dprint("SwitchSaveConfig() - POST called")
        retval, error = perform_switch_save_config(
            request=request,
            group_id=group_id,
            switch_id=switch_id,
        )
        if not retval:
            return error_page_by_id(request=request, group_id=group_id, switch_id=switch_id, error=error)

        return success_page_by_id(request, group_id=group_id, switch_id=switch_id, message="Configuration was saved.")


class SwitchCmdOutput(LoginRequiredMixin, View):
    """
    Go parse a global switch command that was submitted in the form
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
    ):
        dprint("SwitchCmdOutput() - POST called")

        command_id = int(request.POST.get("command_id", -1))
        return switch_view(
            request=request,
            group_id=group_id,
            switch_id=switch_id,
            view="basic",
            command_id=command_id,
        )


class SwitchCmdTemplateOutput(LoginRequiredMixin, View):
    """
    Go parse a switch command template that was submitted in the form
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
    ):
        dprint("SwitchCmdTemplateOutput() - POST called")

        group, switch = get_group_and_switch(request=request, group_id=group_id, switch_id=switch_id)

        if group is None or switch is None:
            log = Log(
                user=request.user,
                ip_address=get_remote_ip(request),
                switch=switch,
                group=group,
                type=LOG_TYPE_ERROR,
                description="Permission denied!",
            )
            log.save()
            error = Error()
            error.status = True
            error.description = "Access denied!"
            counter_increment(COUNTER_ACCESS_DENIED)
            return error_page(request=request, group=False, switch=False, error=error)

        template_id = int(request.POST.get("template_id", -1))
        t = get_object_or_404(CommandTemplate, pk=template_id)

        # now build the command template:
        values = {}
        errors = False
        error_string = ""

        #
        # do field / list validation here. This can likely be simplified - needs work!
        #
        # do we need to parse field1:
        if "{{field1}}" in t.template:
            field1 = request.POST.get("field1", False)
            if field1:
                if string_matches_regex(field1, t.field1_regex):
                    values["field1"] = str(field1)
                else:
                    errors = True
                    error_string = f"{t.field1_name} - Invalid entry: {field1}"
            else:
                # not found in form (or empty), but reqired!
                errors = True
                error_string = f"{t.field1_name} - cannot be blank!"

        # do we need to parse field2:
        if "{{field2}}" in t.template:
            field2 = request.POST.get("field2", False)
            if field2:
                if string_matches_regex(field2, t.field2_regex):
                    values["field2"] = str(field2)
                else:
                    errors = True
                    error_string += f"<br/>{t.field2_name} - Invalid entry: {field2}"
            else:
                # not found in form (or empty), but reqired!
                errors = True
                error_string += f"<br/>{t.field2_name} - cannot be blank!"

        # do we need to parse field3:
        if "{{field3}}" in t.template:
            field3 = request.POST.get("field3", False)
            if field3:
                if string_matches_regex(field3, t.field3_regex):
                    values["field3"] = str(field3)
                else:
                    errors = True
                    error_string += f"<br/>{t.field3_name} - Invalid entry: {field3}"
            else:
                # not found in form (or empty), but reqired!
                errors = True
                error_string += f"<br/>{t.field3_name} - cannot be blank!"

        # do we need to parse field4:
        if "{{field4}}" in t.template:
            field4 = request.POST.get("field4", False)
            if field4:
                if string_matches_regex(field4, t.field4_regex):
                    values["field4"] = str(field4)
                else:
                    errors = True
                    error_string += f"<br/>{t.field4_name} - Invalid entry: {field4} "
            else:
                # not found in form (or empty), but reqired!
                errors = True
                error_string += f"<br/>{t.field4_name} - cannot be blank!"

        # do we need to parse field5:
        if "{{field5}}" in t.template:
            field5 = request.POST.get("field5_regex", False)
            if field5:
                if string_matches_regex(field5, t.field5_regex):
                    values["field5"] = str(field5)
                else:
                    errors = True
                    error_string += f"<br/>{t.field5_name} - Invalid entry: {field5}"
            else:
                # not found in form (or empty), but reqired!
                errors = True
                error_string += f"<br/>{t.field5_name} - cannot be blank!"

        # do we need to parse field6:
        if "{{field6}}" in t.template:
            field6 = request.POST.get("field6", False)
            if field6:
                if string_matches_regex(field1, t.field6_regex):
                    values["field6"] = str(field6)
                else:
                    errors = True
                    error_string += f"<br/>{t.field6_name} - Invalid entry: {field6} "
            else:
                # not found in form (or empty), but reqired!
                errors = True
                error_string += f"<br/>{t.field6_name} - cannot be blank!"

        # do we need to parse field7:
        if "{{field7}}" in t.template:
            field7 = request.POST.get("field7", False)
            if field7:
                if string_matches_regex(field7, t.field7_regex):
                    values["field7"] = str(field7)
                else:
                    errors = True
                    error_string += f"<br/>{t.field7_name} - Invalid entry: {field7}"
            else:
                # not found in form (or empty), but reqired!
                errors = True
                error_string += f"<br/>{t.field7_name} - cannot be blank!"

        # do we need to parse field8:
        if "{{field8}}" in t.template:
            field8 = request.POST.get("field8", False)
            if field8:
                if string_matches_regex(field8, t.field8_regex):
                    values["field8"] = str(field8)
                else:
                    errors = True
                    error_string += f"<br/>{t.field8_name} - Invalid entry: {field8}"
            else:
                # not found in form (or empty), but reqired!
                errors = True
                error_string += f"<br/>{t.field8_name} - cannot be blank!"

        # and the pick lists:
        # do we need to parse list1:
        if "{{list1}}" in t.template:
            list1 = request.POST.get("list1", False)
            if list1:
                values["list1"] = str(list1)
            else:
                # not found in form (or empty), but reqired (unlikely to happen for list)!
                errors = True
                error_string += f"<br/>{t.list1_name} - cannot be blank!"

        # do we need to parse list2:
        if "{{list2}}" in t.template:
            list2 = request.POST.get("list2", False)
            if list2:
                values["list2"] = str(list2)
            else:
                # not found in form (or empty), but reqired (unlikely to happen for list)!
                errors = True
                error_string += f"<br/>{t.list2_name} - cannot be blank!"

        # do we need to parse list3:
        if "{{list3}}" in t.template:
            list3 = request.POST.get("list3", False)
            if list3:
                values["list3"] = str(list3)
            else:
                # not found in form (or empty), but reqired (unlikely to happen for list)!
                errors = True
                error_string += f"<br/>{t.list3_name} - cannot be blank!"

        # do we need to parse list4:
        if "{{list4}}" in t.template:
            list4 = request.POST.get("list4", False)
            if list4:
                values["list4"] = str(list4)
            else:
                # not found in form (or empty), but reqired (unlikely to happen for list)!
                errors = True
                error_string += f"<br/>{t.list4_name} - cannot be blank!"

        # do we need to parse list5:
        if "{{list5}}" in t.template:
            list5 = request.POST.get("list5", False)
            if list5:
                values["list5"] = str(list5)
            else:
                # not found in form (or empty), but reqired (unlikely to happen for list)!
                errors = True
                error_string += f"<br/>{t.list5_name} - cannot be blank!"

        if errors:
            error = Error()
            error.description = mark_safe(error_string)
            return error_page(request=request, group=group, switch=switch, error=error)

        # now do the template expansion, i.e. Jinja2 rendering:
        template = Template(t.template)
        context = Context(values)
        command = template.render(context)

        return switch_view(
            request=request,
            group_id=group_id,
            switch_id=switch_id,
            view="basic",
            command_id=-1,
            interface_name="",
            command_string=command,
            command_template=t,
        )


class InterfaceCmdOutput(LoginRequiredMixin, View):
    """
    Parse the interface-specific command form and build the commands
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
        interface_name,
    ):
        dprint("InterfaceCmdOutput() - POST called")
        command_id = int(request.POST.get("command_id", -1))
        return switch_view(
            request=request,
            group_id=group_id,
            switch_id=switch_id,
            view="basic",
            command_id=command_id,
            interface_name=interface_name,
        )


class SwitchReload(LoginRequiredMixin, MyView):
    """
    This forces a new reading of device data
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
        view,
    ):
        dprint("SwitchReload() - POST called")

        group, switch = get_group_and_switch(request=request, group_id=group_id, switch_id=switch_id)

        if group is None or switch is None:
            log = Log(
                user=request.user,
                ip_address=get_remote_ip(request),
                switch=switch,
                group=group,
                type=LOG_TYPE_ERROR,
                description="Permission denied!",
            )
            log.save()
            error = Error()
            error.status = True
            error.description = "Access denied!"
            counter_increment(COUNTER_ACCESS_DENIED)
            return error_page(request=request, group=False, switch=False, error=error)

        log = Log(
            user=request.user,
            ip_address=get_remote_ip(request),
            switch=switch,
            group=group,
            description=f"Reloading device ({view})",
            action=LOG_RELOAD_SWITCH,
            type=LOG_TYPE_VIEW,
        )
        log.save()

        clear_switch_cache(request)
        counter_increment(COUNTER_VIEWS)

        return switch_view(request=request, group_id=group_id, switch_id=switch_id, view=view)


class SwitchActivity(LoginRequiredMixin, View):
    """
    This shows recent activity logs for a specific device
    """

    def get(
        self,
        request,
        group_id,
        switch_id,
    ):
        dprint("SwitchActivity() - GET called")
        template_name = "switch_activity.html"
        group, switch = get_group_and_switch(request=request, group_id=group_id, switch_id=switch_id)

        if group is None or switch is None:
            log = Log(
                user=request.user,
                ip_address=get_remote_ip(request),
                switch=switch,
                group=group,
                type=LOG_TYPE_ERROR,
                description="Permission denied!",
            )
            log.save()
            error = Error()
            error.status = True
            error.description = "Access denied!"
            counter_increment(COUNTER_ACCESS_DENIED)
            return error_page(request=request, group=False, switch=False, error=error)

        # only show this switch. May add more filters later...
        filter_values = {"switch_id": switch_id}
        logs = Log.objects.all().filter(**filter_values).order_by("-timestamp")

        # setup pagination of the resulting activity logs
        page_number = int(request.GET.get("page", default=1))
        paginator = Paginator(logs, settings.PAGINATE_COUNT)  # Show set number of contacts per page.
        logs_page = paginator.get_page(page_number)

        # log my activity
        log = Log(
            user=request.user,
            ip_address=get_remote_ip(request),
            switch=switch,
            group=group,
            type=LOG_TYPE_VIEW,
            action=LOG_VIEW_ALL_LOGS,
            description=f"Viewing Switch Activity Logs (page {page_number})",
        )
        log.save()

        # get the url to this switch:
        switch_url = reverse("switches:switch_basics", kwargs={"group_id": group.id, "switch_id": switch.id})
        # formulate the title and link
        title = mark_safe(
            f'All Activity for <a href="{switch_url}" data-bs-toggle="tooltip" title="Go back to switch">{switch.name}</a>'
        )
        # render the template
        return render(
            request,
            template_name,
            {
                "logs": logs_page,
                "paginator": paginator,
                "group": group,
                "switch": switch,
                "log_title": title,
                "logs_link": False,
            },
        )


class ShowStats(LoginRequiredMixin, View):
    """
    This shows various site statistics
    """

    def get(
        self,
        request,
    ):
        dprint("ShowStats() - GET called")

        template_name = "admin_stats.html"

        # log my activity
        log = Log(
            user=request.user,
            ip_address=get_remote_ip(request),
            type=LOG_TYPE_VIEW,
            action=LOG_VIEW_ADMIN_STATS,
            description="Viewing Site Statistics",
        )
        log.save()

        environment = get_environment_info()
        db_items = get_database_info()
        usage = get_usage_info()
        user_list = get_current_users()

        # render the template
        return render(
            request,
            template_name,
            {
                "db_items": db_items,
                "usage": usage,
                "environment": environment,
                "user_list": user_list,
            },
        )


class ShowTop(LoginRequiredMixin, View):
    """
    This shows various Top-N activity usage statistics
    """

    def get(
        self,
        request,
    ):
        dprint("ShowTop() - GET called")

        template_name = "top_activity.html"

        # log my activity
        log = Log(
            user=request.user,
            ip_address=get_remote_ip(request),
            type=LOG_TYPE_VIEW,
            action=LOG_VIEW_TOP_ACTIVITY,
            description="Viewing Top Activity",
        )
        log.save()

        changed = get_top_changed_devices()
        viewed = get_top_viewed_devices()
        users = get_top_active_users()

        # render the template
        return render(
            request,
            template_name,
            {
                "changed": changed,
                "viewed": viewed,
                "users": users,
            },
        )


#
# "Administrative" views
#
class SwitchAdminActivity(LoginRequiredMixin, View):
    """
    This shows recent activity
    """

    def get(
        self,
        request,
    ):
        dprint("SwitchAdminActivity() - GET called")

        template_name = "admin_activity.html"

        # what do we have rights to:
        if not request.user.is_superuser and not request.user.is_staff:
            # get them out of here!
            # log my activity
            log = Log(
                user=request.user,
                ip_address=get_remote_ip(request),
                type=LOG_TYPE_ERROR,
                action=LOG_VIEW_ALL_LOGS,
                description="Not Allowed to View All Logs",
            )
            log.save()
            error = Error()
            error.status = True
            error.description = "You do not have access to this page!"
            counter_increment(COUNTER_ACCESS_DENIED)
            return error_page(request=request, group=False, switch=False, error=error)

        # log my activity
        log = Log(
            user=request.user,
            ip_address=get_remote_ip(request),
            type=LOG_TYPE_VIEW,
            action=LOG_VIEW_ALL_LOGS,
        )

        page_number = int(request.GET.get("page", default=1))

        # look at query string, and filter as needed
        filter_values = {}
        if len(request.GET) > 0:
            if request.GET.get("type", ""):
                filter_values["type"] = int(request.GET["type"])
            if request.GET.get("action", ""):
                filter_values["action"] = int(request.GET["action"])
            if request.GET.get("user", ""):
                filter_values["user_id"] = int(request.GET["user"])
            if request.GET.get("switch", ""):
                filter_values["switch_id"] = int(request.GET["switch"])
            if request.GET.get("group", ""):
                filter_values["group_id"] = int(request.GET["group"])

        # now set the filter, if found
        if len(filter_values) > 0:
            logs = Log.objects.all().filter(**filter_values).order_by("-timestamp")
            log.description = f"Viewing filtered logs: {filter_values} (page {page_number})"
            title = "Filtered Logs"
        else:
            logs = Log.objects.all().order_by("-timestamp")
            log.description = f"Viewing all logs (page {page_number})"
            title = "All Logs"
        log.save()

        # setup pagination of the resulting activity logs
        paginator = Paginator(logs, settings.PAGINATE_COUNT)  # Show set number of contacts per page.
        logs_page = paginator.get_page(page_number)

        # render the template
        return render(
            request,
            template_name,
            {
                "logs": logs_page,
                "paginator": paginator,
                "filter": filter,
                "types": LOG_TYPE_CHOICES,
                "actions": LOG_ACTION_CHOICES,
                "switches": Switch.objects.all().order_by("name"),
                "switchgroups": SwitchGroup.objects.all().order_by("name"),
                "users": User.objects.all().order_by("username"),
                "log_title": title,
                "logs_link": False,
            },
        )


class SwitchDownloadEthernetAndNeighbors(LoginRequiredMixin, MyView):
    """
    Download list of known ethernet addressess on a device.
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
    ):
        dprint("SwitchDownloadEthernetAndNeighbors() - POST called")

        group, switch = get_group_and_switch(request=request, group_id=group_id, switch_id=switch_id)
        connection, error = get_connection_if_permitted(request=request, group=group, switch=switch)

        if connection is None:
            return error_page(request=request, group=group, switch=switch, error=error)

        log = Log(
            user=request.user,
            ip_address=get_remote_ip(request),
            switch=switch,
            group=group,
            type=LOG_TYPE_VIEW,
            action=LOG_VIEW_DOWNLOAD_ARP_LLDP,
        )
        # load ethernet, neighbor info, etc. again
        try:
            if not connection.get_client_data():
                log.type = LOG_TYPE_ERROR
                log.description = "ERROR get_client_data()"
                log.save()
                return error_page(request=request, group=group, switch=switch, error=connection.error)
        except Exception as e:
            log.type = LOG_TYPE_ERROR
            log.description = (
                f"CAUGHT UNTRAPPED ERROR in get_client_data(): {repr(e)} ({str(type(e))})\n{traceback.format_exc()}"
            )
            dprint(log.description)
            log.save()
            return error_page(request=request, group=group, switch=switch, error=connection.error)

        # create a temp file with the spreadsheet
        stream, error = create_eth_neighbor_xls_file(connection)
        if not stream:
            log.type = LOG_TYPE_ERROR
            log.description = f"{error.description}: {error.details}"
            log.save()
            return error_page(request=request, group=group, switch=switch, error=error)

        # create tbe download filename
        filename = f"{connection.switch.name}-ethernet-neighbor-info.xlsx"
        log.description = f"Downloading '{filename}'"
        log.save()
        return FileResponse(stream, as_attachment=True, filename=filename)


class SwitchDownloadInterfaces(LoginRequiredMixin, MyView):
    """
    Download a spreadsheet of visible interfaces on a device.
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
    ):
        dprint("SwitchDownloadInterfaces() - POST called")

        group, switch = get_group_and_switch(request=request, group_id=group_id, switch_id=switch_id)
        connection, error = get_connection_if_permitted(request=request, group=group, switch=switch)

        if connection is None:
            return error_page(request=request, group=group, switch=switch, error=error)

        log = Log(
            user=request.user,
            ip_address=get_remote_ip(request),
            switch=switch,
            group=group,
            type=LOG_TYPE_VIEW,
            action=LOG_VIEW_DOWNLOAD_INTERFACES,
        )
        # create a temp file with the spreadsheet
        stream, error = create_interfaces_xls_file(connection)
        if not stream:
            log.type = LOG_TYPE_ERROR
            log.description = f"{error.description}: {error.details}"
            log.save()
            return error_page(request=request, group=group, switch=switch, error=error)

        # create tbe download filename
        filename = f"{connection.switch.name}-interfaces.xlsx"
        log.description = f"Downloading '{filename}'"
        log.save()
        return FileResponse(stream, as_attachment=True, filename=filename)


class TestPage(LoginRequiredMixin, View):
    '''create a page to test html templates'''

    def get(
        self,
        request,
    ):
        dprint("TestPage() - GET called")
        # render the template
        return render(
            request,
            "test_page.html",
            {},
        )
