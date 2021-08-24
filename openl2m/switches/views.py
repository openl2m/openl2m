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
import sys
import os
import socket
import time
import datetime
import traceback
import git
import json
import re

import django
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.views.generic import View
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.html import mark_safe
from django.views.generic import View
from django.utils import timezone
from django.core.paginator import Paginator
from django.shortcuts import redirect

from openl2m.celery import get_celery_info, is_celery_running
from switches.models import *
from switches.constants import *
from switches.connect.connector import clear_switch_cache
from switches.connect.connect import *
# from switches.connect.snmp.constants import *
# from switches.connect.snmp import *
from switches.utils import *
from switches.tasks import bulkedit_task, bulkedit_processor
from users.utils import *


@login_required(redirect_field_name=None)
def switches(request):
    """
    This is the "home view", at "/"
    It shows the list of switches a user has access to
    """

    template_name = 'home.html'

    # back to the home screen, clear session cache
    # so we re-read switches as needed
    clear_switch_cache(request)

    # save remote ip in session, so we can use it in current user display!
    save_to_http_session(request, "remote_ip", get_remote_ip(request))

    # find the groups with switches that we have rights to:
    switchgroups = {}
    permissions = {}
    if request.user.is_superuser or request.user.is_staff:
        # optimize data queries, get all related field at once!
        groups = SwitchGroup.objects.all().order_by('name')

    else:
        # figure out what this users has access to.
        # Note we use the ManyToMany 'related_name' attribute for readability!
        groups = request.user.switchgroups.all().order_by('name')

    for group in groups:
        if group.switches.count():
            switchgroups[group.name] = group
            # set this group, and the switches, in web session to track permissions
            permissions[int(group.id)] = {}
            for switch in group.switches.all():
                if switch.status == SWITCH_STATUS_ACTIVE:
                    # do we have a valid config:
                    if ((switch.connector_type == CONNECTOR_TYPE_SNMP and switch.snmp_profile) or
                       (switch.connector_type == CONNECTOR_TYPE_NAPALM and switch.napalm_device_type)):
                        # we save the names as well, so we can search them!
                        permissions[int(group.id)][int(switch.id)] = (switch.name, switch.hostname, switch.description)

    save_to_http_session(request, "permissions", permissions)

    # log my activity
    log = Log(user=request.user,
              ip_address=get_remote_ip(request),
              action=LOG_VIEW_SWITCHGROUPS,
              description="Viewing switch groups",
              type=LOG_TYPE_VIEW)
    log.save()

    # render the template
    return render(request, template_name, {
        'groups': switchgroups,
    })


@login_required(redirect_field_name=None)
def switch_search(request):
    """
    search for a switch by name
    """

    if not settings.SWITCH_SEARCH_FORM:
        return redirect(reverse('switches:groups'))

    search = str(request.POST.get('switchname', ''))
    if not search:
        return redirect(reverse('switches:groups'))

    template_name = "search_results.html"

    # log my activity
    log = Log(user=request.user,
              ip_address=get_remote_ip(request),
              action=LOG_VIEW_SWITCH_SEARCH,
              description=f"Searching for switch '{ search }'",
              type=LOG_TYPE_VIEW)
    log.save()

    results = []
    warning = False
    permissions = get_from_http_session(request, 'permissions')
    if permissions and isinstance(permissions, dict):
        for group_id in permissions.keys():
            switches = permissions[group_id]
            if isinstance(switches, dict):
                for switch_id in switches.keys():
                    (name, hostname, description) = switches[switch_id]
                    # now check the name, hostname for the search pattern:
                    try:
                        if re.search(search, name, re.IGNORECASE) or re.search(search, hostname, re.IGNORECASE):
                            results.append((str(group_id), str(switch_id), name, description))
                    except Exception as e:
                        # invalid search, just ignore!
                        warning = f"{search} - This is an invalid search pattern!"

    # render the template
    return render(request, template_name, {
        'warning': warning,
        'search': search,
        'results': results,
    })


@login_required
def switch_basics(request, group_id, switch_id):
    """
    "basic" switch view, i.e. interface data only.
    Simply call switch_view() with proper parameter
    """
    return switch_view(request=request, group_id=group_id, switch_id=switch_id, view='basic')


@login_required(redirect_field_name=None)
def switch_arp_lldp(request, group_id, switch_id):
    """
    "details" switch view, i.e. with Ethernet/ARP/LLDP data.
    Simply call switch_view() with proper parameter
    """
    return switch_view(request=request, group_id=group_id, switch_id=switch_id, view='arp_lldp')


@login_required(redirect_field_name=None)
def switch_hw_info(request, group_id, switch_id):
    """
    "hardware info" switch view, i.e. read detailed system hardware ("entity") data.
    Simply call switch_view() with proper parameter
    """
    return switch_view(request=request, group_id=group_id, switch_id=switch_id, view='hw_info')


def switch_view(request, group_id, switch_id, view, command_id=-1, interface_name=''):
    """
    This shows the various data about a switch, either from a new SNMP read,
    from cached OID data, or an SSH command.
    This is includes enough to enable/disable interfaces and power,
    and change vlans. Depending on view, there may be more data needed,
    such as ethernet, arp & lldp tables.
    """

    template_name = 'switch.html'

    group = get_object_or_404(SwitchGroup, pk=group_id)
    switch = get_object_or_404(Switch, pk=switch_id)

    if not rights_to_group_and_switch(request, group_id, switch_id):
        error = Error()
        error.description = "Access denied!"
        error.details = "You do not have access to this device!"
        return error_page(request=request, group=False, switch=False, error=error)

    log = Log(user=request.user,
              ip_address=get_remote_ip(request),
              switch=switch,
              group=group,
              action=LOG_VIEW_SWITCH,
              type=LOG_TYPE_VIEW,
              description=f"Viewing switch ({view})")

    try:
        conn = get_connection_object(request, group, switch)
    except Exception as e:
        log.type = LOG_TYPE_ERROR
        log.description = f"SNMP ERROR: Viewing switch ({view})"
        log.save()
        error = Error()
        error.description = "There was a failure communicating with this switch. Please contact your administrator to make sure switch data is correct in the database!"
        error.details = traceback.format_exc()
        return error_page(request=request, group=group, switch=switch, error=error)

    if not conn.get_basic_info():
        # errors
        log.type = LOG_TYPE_ERROR
        log.description = "ERROR in get_basic_switch_info()"
        log.save()
        return error_page(request=request, group=group, switch=switch, error=conn.error)

    dprint("Basic Info OK")

    if view == 'hw_info':
        if not conn.get_detailed_info():
            # errors
            log.type = LOG_TYPE_ERROR
            log.description = "ERROR in get_detailed_info()"
            log.save()
            # don't render error, since we have already read the basic interface data
            # Note that SNMP errors are already added to warnings!
            # return error_page(request=request, group=group, switch=switch, error=conn.error)
        dprint("Details Info OK")

    if view == 'arp_lldp':
        if not conn.get_client_data():
            log.type = LOG_TYPE_ERROR
            log.description = "ERROR get_client_data()"
            log.save()
            # don't render error, since we have already read the basic interface data
            # Note that errors are already added to warnings!
            # return error_page(request=request, group=group, switch=switch, error=conn.error)
        dprint("ARP-LLDP Info OK")

    # done with reading switch data, so save cachable/session data
    conn.save_cache()

    # does this switch have any commands defined?
    cmd = False
    # check that we can process commands, and have valid commands assigned to switch
    if command_id > -1:
        # Exexute a specific Command object by ID, note rights are checked in run_command()!
        dprint("CALLING RUN_COMMAND()")
        cmd = conn.run_command(command_id=command_id, interface_name=interface_name)
        if conn.error.status:
            # log it!
            log.type = LOG_TYPE_ERROR
            log.action = LOG_EXECUTE_COMMAND
            log.description = f"{cmd['error_descr']}: {cmd['error_details']}"
        else:
            # success !
            log.type = LOG_TYPE_COMMAND
            log.action = LOG_EXECUTE_COMMAND
            log.description = cmd['command']
        log.save()

    # get recent "non-viewing" activity for this switch
    # for now, show most recent 25 activities
    logs = Log.objects.all().filter(switch=switch, type__gt=LOG_TYPE_VIEW).order_by('-timestamp')[:settings.RECENT_SWITCH_LOG_COUNT]

    # are there any scheduled tasks for this switch?
    if settings.TASKS_ENABLED:
        task_process_running = is_celery_running()
        tasks = Task.objects.all().filter(switch=switch, status=TASK_STATUS_SCHEDULED).order_by('-eta')
    else:
        task_process_running = False
        tasks = False

    time_since_last_read = time_duration(time.time() - conn.basic_info_read_timestamp)

    # finally, verify what this user can do:
    bulk_edit = len(conn.interfaces) and user_can_bulkedit(request.user, group, switch)
    allow_tasks = user_can_run_tasks(request.user, group, switch)

    log_title = "Recent Activity"

    return render(request, template_name, {
        'group': group,
        'switch': switch,
        'connection': conn,
        'logs': logs,
        'log_title': log_title,
        'logs_link': True,
        'tasks': tasks,
        'task_process_running': task_process_running,
        'view': view,
        'cmd': cmd,
        'bulk_edit': bulk_edit,
        'allow_tasks': allow_tasks,
        'time_since_last_read': time_since_last_read,
    })


#
# Bulk Edit interfaces on a switch
#
@login_required(redirect_field_name=None)
def switch_bulkedit(request, group_id, switch_id):
    """
    Change several interfaces at once.
    """
    return bulkedit_form_handler(request, group_id, switch_id, False)


@login_required(redirect_field_name=None)
def switch_bulkedit_task(request, group_id, switch_id):
    """
    Change several interfaces at once, at some future time
    """
    return bulkedit_form_handler(request, group_id, switch_id, True)


def bulkedit_form_handler(request, group_id, switch_id, is_task):
    """
    Handle the changing of several interfaces, as a future task or now.
    """
    group = get_object_or_404(SwitchGroup, pk=group_id)
    switch = get_object_or_404(Switch, pk=switch_id)

    if not rights_to_group_and_switch(request, group_id, switch_id):
        error = Error()
        error.description = "Access denied!"
        error.details = "You do not have access to this device!"
        return error_page(request=request, group=False, switch=False, error=error)

    try:
        conn = get_connection_object(request, group, switch)
    except Exception:
        log.type = LOG_TYPE_ERROR
        log.description = "Could not get connection"
        log.save()
        error = Error()
        error.description = "Could not get connection. Please contact your administrator to make sure switch data is correct in the database!"
        error.details = "This is likely a configuration error, such as wrong SNMP settings."
        return error_page(request=request, group=group, switch=switch, error=error)

    # read the submitted form data:
    interface_change = int(request.POST.get('interface_change', INTERFACE_STATUS_NONE))
    poe_choice = int(request.POST.get('poe_choice', BULKEDIT_POE_NONE))
    new_pvid = int(request.POST.get('new_pvid', -1))
    new_description = str(request.POST.get('new_description', ''))
    new_description_type = int(request.POST.get('new_description_type', BULKEDIT_ALIAS_TYPE_REPLACE))
    interface_list = request.POST.getlist('interface_list')
    remote_ip = get_remote_ip(request)
    save_config = bool(request.POST.get('save_config', False))

    # was anything submitted?
    if len(interface_list) == 0:
        return warning_page(request=request, group=group, switch=switch,
                            description=mark_safe("Please select at least 1 interface!"))

    if interface_change == INTERFACE_STATUS_NONE and poe_choice == BULKEDIT_POE_NONE and new_pvid < 0 and not new_description:
        return warning_page(request=request, group=group, switch=switch,
                            description=mark_safe("Please select at least 1 thing to change!"))

    # perform some checks on valid data first:
    errors = []

    # check if the new description/description is allowed:
    if new_description and new_description_type == BULKEDIT_ALIAS_TYPE_REPLACE and settings.IFACE_ALIAS_NOT_ALLOW_REGEX:
        match = re.match(settings.IFACE_ALIAS_NOT_ALLOW_REGEX, new_description)
        if match:
            log = Log(user=request.user,
                      ip_address=remote_ip,
                      switch=switch,
                      group=group,
                      type=LOG_TYPE_ERROR,
                      action=LOG_CHANGE_BULK_EDIT,
                      description=f"Description not allowed: {new_description}")
            log.save()
            new_description = ''
            errors.append(f"The description is not allowed: {new_description}")

    # safety-check: is the new PVID allowed:
    if new_pvid > 0:
        conn._set_allowed_vlans()
        if new_pvid not in conn.allowed_vlans.keys():
            log = Log(user=request.user,
                      ip_address=remote_ip,
                      switch=switch,
                      group=group,
                      type=LOG_TYPE_ERROR,
                      action=LOG_CHANGE_BULK_EDIT,
                      description=f"New vlan '{new_pvid}' is not allowed!")
            log.save()
            new_pvid = -1   # force no change!
            errors.append(f"New vlan '{new_pvid}' is not allowed!")

    if is_task:
        # we need a description
        task_description = str(request.POST.get('task_description', ''))
        if not task_description:
            errors.append("We need a description of this task!")
        # check format of ETA:
        eta = str(request.POST.get('task_eta', ''))
        if eta:
            # if you change the format here, you also need to change it
            # in the web form in the "_tab_if_bulkedit.html" template
            eta_with_tz = f"{eta} {get_local_timezone_offset()}"
            dprint(f"TASK ETA with TZ-offset: {eta_with_tz}")
            try:
                # this needs timezone parsing!
                eta_datetime = datetime.datetime.strptime(eta_with_tz, settings.TASK_SUBMIT_DATE_FORMAT)
            except Exception as e:
                # unsupported time format!
                errors.append("Invalid date/time format, please use YYYY-MM-DD HH:MM !")

    if len(errors) > 0:
        error = Error()
        error.description = "Some form values were invalid, please correct and resubmit!"
        error.details = mark_safe("\n<br>".join(errors))
        return error_page(request=request, group=group, switch=switch, error=error)

    # get the name of the interfaces as well (with the submitted if_key values)
    # so that we can show the names in the Task() and Log() objects
    # additionally, also get the current state, to be able to "undo" the update
    interfaces = {}     # dict() of interfaces to bulk edit
    undo_info = {}
    for if_key in interface_list:
        dprint(f"BulkEdit for {if_key}")
        interface = conn.get_interface_by_key(if_key)
        if interface:
            interfaces[if_key] = interface.name
            if is_task:
                # save the current state
                current = {}
                current['if_key'] = if_key
                current['name'] = interface.name    # for readability
                if new_pvid > 0:
                    current['pvid'] = interface.untagged_vlan
                if new_description:
                    current['description'] = interface.description
                if poe_choice != BULKEDIT_POE_NONE and interface.poe_entry:
                    current['poe_state'] = interface.poe_entry.admin_status
                if interface_change != INTERFACE_STATUS_NONE:
                    current['admin_state'] = interface.admin_status
                undo_info[if_key] = current

    if is_task:
        # log this first
        log = Log(user=request.user,
                  ip_address=remote_ip,
                  switch=switch,
                  group=group,
                  type=LOG_TYPE_CHANGE,
                  action=LOG_BULK_EDIT_TASK_SUBMIT,
                  description=f"Bulk Edit Task Submitted ({task_description}) to run at {eta}")
        log.save()

        # arguments for the task:
        args = {}
        args['user_id'] = request.user.id
        args['group_id'] = group_id
        args['switch_id'] = switch_id
        args['interface_change'] = interface_change
        args['poe_choice'] = poe_choice
        args['new_pvid'] = new_pvid
        args['new_description'] = new_description
        args['new_description_type'] = new_description_type
        args['interfaces'] = interfaces
        args['save_config'] = save_config
        # create a task to track progress
        task = Task(user=request.user,
                    group=group,
                    switch=switch,
                    eta=eta_datetime,
                    type=TASK_TYPE_BULKEDIT,
                    description=task_description,
                    arguments=json.dumps(args),
                    reverse_arguments=json.dumps(undo_info))
        task.save()

        # now go schedule the task
        try:
            celery_task_id = bulkedit_task.apply_async((task.id, request.user.id, group_id, switch_id,
                                                       interface_change, poe_choice, new_pvid,
                                                       new_description, new_description_type, interfaces, save_config),
                                                       eta=eta_datetime)
        except Exception as e:
            error = Error()
            error.description = "There was an error submitting your task. Please contact your administrator to make sure the job broker is running!"
            error.details = mark_safe(f"{repr(e)}<br><br>{traceback.format_exc()}")
            return error_page(request=request, group=group, switch=switch, error=error)

        # update task:
        task.status = TASK_STATUS_SCHEDULED
        task.celery_task_id = celery_task_id
        task.save()

        description = f"New Bulk-Edit task was submitted to run at {eta} (task id = {task.id})"
        return success_page(request, group, switch, mark_safe(description))

    # handle regular submit, execute now!
    results = bulkedit_processor(request, request.user.id, group_id, switch_id,
                                 interface_change, poe_choice, new_pvid,
                                 new_description, new_description_type, interfaces, False)

    # indicate we need to save config!
    if results['success_count'] > 0:
        conn.set_save_needed(True)
        # and save data in session
        conn.save_cache()

    # now build the results page from the outputs
    result_str = "\n<br>".join(results['outputs'])
    description = f"\n<div><strong>Results:</strong></div>\n<br>{result_str}"
    if results['error_count'] > 0:
        err = Error()
        err.description = "Bulk-Edit errors"
        err.details = mark_safe(description)
        return error_page(request=request, group=group, switch=switch, error=err)
    else:
        return success_page(request, group, switch, mark_safe(description))


#
# Change admin status, ie port Enable/Disable
#
@login_required(redirect_field_name=None)
def interface_admin_change(request, group_id, switch_id, interface_name, new_state):
    """
    Toggle the admin status of an interface, ie admin up or down.
    """
    group = get_object_or_404(SwitchGroup, pk=group_id)
    switch = get_object_or_404(Switch, pk=switch_id)

    if not rights_to_group_and_switch(request, group_id, switch_id):
        error = Error()
        error.description = "Access denied!"
        error.details = "You do not have access to this device!"
        return error_page(request=request, group=False, switch=False, error=error)

    log = Log(user=request.user,
              ip_address=get_remote_ip(request),
              switch=switch,
              group=group,
              if_name=interface_name)

    try:
        conn = get_connection_object(request, group, switch)
    except Exception:
        log.type = LOG_TYPE_ERROR
        log.description = "Could not get connection"
        log.save()
        error = Error()
        error.description = "Could not get connection. Please contact your administrator to make sure switch data is correct in the database!"
        error.details = "This is likely a configuration error, such as incorrect SNMP settings."
        return error_page(request=request, group=group, switch=switch, error=error)

    interface = conn.get_interface_by_key(interface_name)
    if not interface:
        log.type = LOG_TYPE_ERROR
        log.description = f"Admin-Change: Error getting interface data for {interface_name}"
        log.save()
        error = Error()
        error.description = "Could not get interface data. Please contact your administrator!"
        error.details = "Sorry, no more details available!"
        return error_page(request=request, group=group, switch=switch, error=error)

    log.type = LOG_TYPE_CHANGE
    if new_state:
        log.action = LOG_CHANGE_INTERFACE_UP
        log.description = f"Interface {interface.name}: Enabled"
        state = "Enabled"
    else:
        log.action = LOG_CHANGE_INTERFACE_DOWN
        log.description = f"Interface {interface.name}: Disabled"
        state = "Disabled"

    if not conn.set_interface_admin_status(interface, bool(new_state)):
        log.description = f"ERROR: {conn.error.description}"
        log.type = LOG_TYPE_ERROR
        log.save()
        return error_page(request=request, group=group, switch=switch, error=conn.error)

    # indicate we need to save config!
    conn.set_save_needed(True)

    # and save data in session
    conn.save_cache()

    log.save()

    description = f"Interface {interface.name} is now {state}"
    return success_page(request, group, switch, description)


@login_required(redirect_field_name=None)
def interface_description_change(request, group_id, switch_id, interface_name):
    """
    Change the ifAlias aka description on an interfaces.
    """
    group = get_object_or_404(SwitchGroup, pk=group_id)
    switch = get_object_or_404(Switch, pk=switch_id)

    if not rights_to_group_and_switch(request, group_id, switch_id):
        error = Error()
        error.description = "Access denied!"
        error.details = "You do not have access to this device!"
        return error_page(request=request, group=False, switch=False, error=error)

    log = Log(user=request.user,
              ip_address=get_remote_ip(request),
              switch=switch,
              group=group,
              if_name=interface_name)

    try:
        conn = get_connection_object(request, group, switch)
    except Exception:
        log.type = LOG_TYPE_ERROR
        log.description = "Could not get connection"
        log.save()
        error = Error()
        error.description = "Could not get connection. Please contact your administrator to make sure switch data is correct in the database!"
        error.details = "This is likely a configuration error, such as incorrect SNMP settings!"
        return error_page(request=request, group=group, switch=switch, error=error)

    interface = conn.get_interface_by_key(interface_name)
    if not interface:
        log.type = LOG_TYPE_ERROR
        log.description = f"Alias-Change: Error getting interface data for {interface_name}"
        log.save()
        error = Error()
        error.description = "Could not get interface data. Please contact your administrator!"
        error.details = "Sorry, no more details available!"
        return error_page(request=request, group=group, switch=switch, error=error)

    # read the submitted form data:
    new_description = str(request.POST.get('new_description', ''))

    if interface.description == new_description:
        description = "New description is the same, please change it first!"
        return warning_page(request=request, group=group, switch=switch, description=description)

    log.type = LOG_TYPE_CHANGE
    log.action = LOG_CHANGE_INTERFACE_ALIAS

    # are we allowed to change description ?
    if not interface.can_edit_description:
        log.description = f"Interface {interface.name} description edit not allowed"
        log.type = LOG_TYPE_ERROR
        log.save()
        error = Error()
        error.description = "You are not allowed to change the interface description"
        error.details = "Sorry, you do not have access!"
        return error_page(request=request, group=group, switch=switch, error=error)

    # check if the description is allowed:
    if settings.IFACE_ALIAS_NOT_ALLOW_REGEX:
        match = re.match(settings.IFACE_ALIAS_NOT_ALLOW_REGEX, new_description)
        if match:
            log.type = LOG_TYPE_ERROR
            log.description = "New description matches admin deny setting!"
            log.save()
            error = Error()
            error.description = f"The description '{new_description}' is not allowed!"
            return error_page(request=request, group=group, switch=switch, error=error)

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
    if not conn.set_interface_description(interface, new_description):
        log.description = f"ERROR: {conn.error.description}"
        log.type = LOG_TYPE_ERROR
        log.save()
        return error_page(request=request, group=group, switch=switch, error=conn.error)

    # indicate we need to save config!
    conn.set_save_needed(True)

    # and save cachable/session data
    conn.save_cache()

    log.save()

    description = f"Interface {interface.name} description changed"
    return success_page(request, group, switch, description)


@login_required(redirect_field_name=None)
def interface_pvid_change(request, group_id, switch_id, interface_name):
    """
    Change the PVID untagged vlan on an interfaces.
    This still needs to handle dot1q trunked ports.
    """
    group = get_object_or_404(SwitchGroup, pk=group_id)
    switch = get_object_or_404(Switch, pk=switch_id)

    if not rights_to_group_and_switch(request, group_id, switch_id):
        error = Error()
        error.description = "Access denied!"
        return error_page(request=request, group=False, switch=False, error=error)

    log = Log(user=request.user,
              ip_address=get_remote_ip(request),
              switch=switch,
              group=group,
              if_name=interface_name)

    try:
        conn = get_connection_object(request, group, switch)
    except Exception:
        log.type = LOG_TYPE_ERROR
        log.description = "Could not get connection"
        log.save()
        error = Error()
        error.description = "Could not get connection. Please contact your administrator to make sure switch data is correct in the database!"
        return error_page(request=request, group=group, switch=switch, error=error)

    interface = conn.get_interface_by_key(interface_name)
    if not interface:
        log.type = LOG_TYPE_ERROR
        log.description = f"Pvid-Change: Error getting interface data for {interface_name}"
        log.save()
        error = Error()
        error.description = "Could not get interface data. Please contact your administrator!"
        return error_page(request=request, group=group, switch=switch, error=error)

    # read the submitted form data:
    new_pvid = int(request.POST.get('new_pvid', 0))
    # did the vlan change?
    if interface.untagged_vlan == int(new_pvid):
        description = f"New vlan {interface.untagged_vlan} is the same, please change the vlan first!"
        return warning_page(request=request, group=group, switch=switch, description=description)

    log.type = LOG_TYPE_CHANGE
    log.action = LOG_CHANGE_INTERFACE_PVID
    log.description = f"Interface {interface.name}: new PVID = {new_pvid} (was {interface.untagged_vlan})"

    # are we allowed to change to this vlan ?
    conn._set_allowed_vlans()
    if not int(new_pvid) in conn.allowed_vlans.keys():
        log.action = LOG_CHANGE_INTERFACE_PVID + LOG_DENIED
        log.save()
        error = Error()
        error.status = True
        error.description = f"New vlan {new_pvid} is not valid on this switch"
        return error_page(request=request, group=group, switch=switch, error=error)

    # make sure we cast the proper type here! Ie this needs an Integer()
    if not conn.set_interface_untagged_vlan(interface, int(new_pvid)):
        log.description = f"ERROR: {conn.error.description}"
        log.type = LOG_TYPE_ERROR
        log.save()
        return error_page(request=request, group=group, switch=switch, error=conn.error)

    # indicate we need to save config!
    conn.set_save_needed(True)

    # and save cachable/session data
    conn.save_cache()

    # all OK, save log
    log.save()

    description = f"Interface {interface.name} changed to vlan {new_pvid}"
    return success_page(request, group, switch, description)


#
# Change PoE status, i.e. port power Enable/Disable
#
@login_required(redirect_field_name=None)
def interface_poe_change(request, group_id, switch_id, interface_name, new_state):
    """
    Change the PoE status of an interfaces.
    This still needs to be tested for propper PoE port to interface ifIndex mappings.
    """
    group = get_object_or_404(SwitchGroup, pk=group_id)
    switch = get_object_or_404(Switch, pk=switch_id)

    if not rights_to_group_and_switch(request, group_id, switch_id):
        error = Error()
        error.status = True
        error.description = "Access denied!"
        return error_page(request=request, group=False, switch=False, error=error)

    log = Log(user=request.user,
              ip_address=get_remote_ip(request),
              switch=switch,
              group=group,
              if_name=interface_name)

    try:
        conn = get_connection_object(request, group, switch)
    except Exception:
        log.type = LOG_TYPE_ERROR
        log.description = "Could not get connection"
        log.save()
        error = Error()
        error.description = "Could not get connection. Please contact your administrator to make sure switch data is correct in the database!"
        return error_page(request=request, group=group, switch=switch, error=error)

    interface = conn.get_interface_by_key(interface_name)
    if not interface:
        log.type = LOG_TYPE_ERROR
        log.description = f"PoE-Change: Error getting interface data for {interface_name}"
        log.save()
        error = Error()
        error.description = "Could not get interface data. Please contact your administrator!"
        return error_page(request=request, group=group, switch=switch, error=error)

    log.type = LOG_TYPE_CHANGE
    if new_state == POE_PORT_ADMIN_ENABLED:
        log.action = LOG_CHANGE_INTERFACE_POE_UP
        log.description = f"Interface {interface.name}: Enabling PoE"
        state = "Enabled"
    else:
        log.action = LOG_CHANGE_INTERFACE_POE_DOWN
        log.description = f"Interface {interface.name}: Disabling PoE"
        state = "Disabled"

    if not interface.poe_entry:
        # should not happen...
        log.type = LOG_TYPE_ERROR
        log.description = f"Interface {interface.name} does not support PoE"
        error = Error()
        error.status = True
        error.description = log.descr
        log.save()
        return error_page(request=request, group=group, switch=switch, error=error)

    # do the work:
    retval = conn.set_interface_poe_status(interface, new_state)
    if retval < 0:
        log.description = f"ERROR: {conn.error.description}"
        log.type = LOG_TYPE_ERROR
        log.save()
        return error_page(request=request, group=group, switch=switch, error=conn.error)

    # indicate we need to save config!
    conn.set_save_needed(True)

    # and save cachable/session data
    conn.save_cache()

    log.save()

    description = f"Interface {interface.name} PoE is now {state}"
    return success_page(request, group, switch, description)


#
# Toggle PoE status Down then Up
#
@login_required(redirect_field_name=None)
def interface_poe_down_up(request, group_id, switch_id, interface_name):
    """
    Toggle the PoE status of an interfaces. I.e disable, wait some, then enable again.
    """
    group = get_object_or_404(SwitchGroup, pk=group_id)
    switch = get_object_or_404(Switch, pk=switch_id)

    if not rights_to_group_and_switch(request, group_id, switch_id):
        error = Error()
        error.status = True
        error.description = "Access denied!"
        return error_page(request=request, group=False, switch=False, error=error)

    log = Log(user=request.user,
              ip_address=get_remote_ip(request),
              switch=switch,
              group=group,
              if_name=interface_name)

    try:
        conn = get_connection_object(request, group, switch)
    except Exception:
        log.type = LOG_TYPE_ERROR
        log.description = "Could not get connection"
        log.save()
        error = Error()
        error.description = "Could not get connection. Please contact your administrator to make sure switch data is correct in the database!"
        return error_page(request=request, group=group, switch=switch, error=error)

    interface = conn.get_interface_by_key(interface_name)
    if not interface:
        log.type = LOG_TYPE_ERROR
        log.description = f"PoE-Down-Up: Error getting interface data for {interface_name}"
        log.save()
        error = Error()
        error.description = "Could not get interface data. Please contact your administrator!"
        return error_page(request=request, group=group, switch=switch, error=error)

    log.type = LOG_TYPE_CHANGE
    log.action = LOG_CHANGE_INTERFACE_POE_TOGGLE_DOWN_UP
    log.description = f"Interface {interface.name}: PoE Toggle Down-Up"

    if not interface.poe_entry:
        # should not happen...
        log.type = LOG_TYPE_ERROR
        log.description = f"Interface {interface.name} does not support PoE"
        error = Error()
        error.status = True
        error.description = log.descr
        log.save()
        return error_page(request=request, group=group, switch=switch, error=error)

    # the PoE information (index) is kept in the interface.poe_entry
    if not interface.poe_entry.admin_status == POE_PORT_ADMIN_ENABLED:
        # should not happen...
        log.type = LOG_TYPE_ERROR
        log.description = f"Interface {interface.name} does not have PoE enabled"
        error = Error()
        error.status = True
        error.description = log.descr
        log.save()
        return error_page(request=request, group=group, switch=switch, error=error)

    # disable PoE:
    if not conn.set_interface_poe_status(interface, POE_PORT_ADMIN_DISABLED):
        log.description = f"ERROR: Toggle-Disable PoE on {interface.name} - {conn.error.description}"
        log.type = LOG_TYPE_ERROR
        log.save()
        return error_page(request=request, group=group, switch=switch, error=conn.error)

    # delay to let the device cold-boot properly
    time.sleep(settings.POE_TOGGLE_DELAY)

    # and enable PoE again...
    if not conn.set_interface_poe_status(interface, POE_PORT_ADMIN_ENABLED):
        log.description = f"ERROR: Toggle-Enable PoE on {interface.name} - {conn.error.description}"
        log.type = LOG_TYPE_ERROR
        log.save()
        return error_page(request=request, group=group, switch=switch, error=conn.error)

    # no state change, so no save needed!
    log.save()

    # and save cachable/session data
    conn.save_cache()

    description = f"Interface {interface.name} PoE was toggled!"
    return success_page(request, group, switch, description)


@login_required(redirect_field_name=None)
def switch_save_config(request, group_id, switch_id, view):
    """
    This will save the running config to flash/startup/whatever, on supported platforms
    """
    group = get_object_or_404(SwitchGroup, pk=group_id)
    switch = get_object_or_404(Switch, pk=switch_id)

    if not rights_to_group_and_switch(request, group_id, switch_id):
        error = Error()
        error.description = "Access denied!"
        return error_page(request=request, group=False, switch=False, error=error)

    log = Log(user=request.user,
              ip_address=get_remote_ip(request),
              switch=switch,
              group=group,
              action=LOG_SAVE_SWITCH,
              type=LOG_TYPE_CHANGE,
              description="Saving switch config")

    try:
        conn = get_connection_object(request, group, switch)
    except Exception:
        log.type = LOG_TYPE_ERROR
        log.description = "Could not get connection"
        log.save()
        error = Error()
        error.description = "Could not get connection. Please contact your administrator to make sure switch data is correct in the database!"
        return error_page(request=request, group=group, switch=switch, error=error)

    if conn.save_needed and conn.can_save_config():
        # we can save
        if conn.save_running_config() < 0:
            # an error happened!
            log.type = LOG_TYPE_ERROR
            log.save()
            return error_page(request=request, group=group, switch=switch, error=conn.error)

        # clear save flag
        conn.set_save_needed(False)

        # save cachable/session data
        conn.save_cache()

    else:
        log.type = LOG_TYPE_ERROR
        log.description = "Can not save config"
        log.save()
        error = Error()
        error.description = "This switch model cannot save or does not need to save the config"
        conn.set_save_needed(False)     # clear flag that should not be set in the first place!
        return error_page(request=request, group=group, switch=switch, error=error)

    # all OK
    log.save()

    description = f"Config was saved for {switch.name}"
    return success_page(request, group, switch, description)


@login_required(redirect_field_name=None)
def switch_cmd_output(request, group_id, switch_id):
    """
    Go parse a global switch command that was submitted in the form
    """
    command_id = int(request.POST.get('command_id', -1))
    return switch_view(request=request, group_id=group_id, switch_id=switch_id, view='basic', command_id=command_id)


@login_required(redirect_field_name=None)
def interface_cmd_output(request, group_id, switch_id, interface_name):
    """
    Parse the interface-specific form and build the commands
    """
    command_id = int(request.POST.get('command_id', -1))
    return switch_view(request=request, group_id=group_id, switch_id=switch_id, view='basic', command_id=command_id, interface_name=interface_name)


@login_required(redirect_field_name=None)
def switch_reload(request, group_id, switch_id, view):
    """
    This forces a new reading of basic switch SNMP data
    """

    group = get_object_or_404(SwitchGroup, pk=group_id)
    switch = get_object_or_404(Switch, pk=switch_id)

    if not rights_to_group_and_switch(request, group_id, switch_id):
        error = Error()
        error.description = "Access denied!"
        return error_page(request=request, group=False, switch=False, error=error)

    log = Log(user=request.user,
              ip_address=get_remote_ip(request),
              switch=switch,
              group=group,
              description="Reloading SNMP (basic)",
              action=LOG_RELOAD_SWITCH,
              type=LOG_TYPE_VIEW)
    log.save()

    clear_switch_cache(request)

    return switch_view(request=request, group_id=group_id, switch_id=switch_id, view=view)


@login_required(redirect_field_name=None)
def switch_activity(request, group_id, switch_id):
    """
    This shows recent activity for a specific switch
    """
    template_name = 'switch_activity.html'

    group = get_object_or_404(SwitchGroup, pk=group_id)
    switch = get_object_or_404(Switch, pk=switch_id)

    if not rights_to_group_and_switch(request, group_id, switch_id):
        error = Error()
        error.description = "Access denied!"
        return error_page(request=request, group=False, switch=False, error=error)

    # only show this switch. May add more filters later...
    filter = {}
    filter['switch_id'] = switch_id
    logs = Log.objects.all().filter(**filter).order_by('-timestamp')

    # setup pagination of the resulting activity logs
    page_number = int(request.GET.get('page', default=1))
    paginator = Paginator(logs, settings.PAGINATE_COUNT)    # Show set number of contacts per page.
    logs_page = paginator.get_page(page_number)

    # log my activity
    log = Log(user=request.user,
              ip_address=get_remote_ip(request),
              switch=switch,
              group=group,
              type=LOG_TYPE_VIEW,
              action=LOG_VIEW_ALL_LOGS,
              description=f"Viewing Switch Activity Logs (page {page_number})")
    log.save()

    # get the url to this switch:
    switch_url = reverse('switches:switch_basics', kwargs={'group_id': group.id, 'switch_id': switch.id})
    # formulate the title and link
    title = mark_safe(f"All Activity for <a href=\"{switch_url}\" data-toggle=\"tooltip\" title=\"Go back to switch\">{switch.name}</a>")
    # render the template
    return render(request, template_name, {
        'logs': logs_page,
        'paginator': paginator,
        'group': group,
        'switch': switch,
        'log_title': title,
        'logs_link': False,
    })


@login_required(redirect_field_name=None)
def show_stats(request):
    """
    This shows various site statistics
    """

    template_name = 'admin_stats.html'

    # log my activity
    log = Log(user=request.user,
              ip_address=get_remote_ip(request),
              type=LOG_TYPE_VIEW,
              action=LOG_VIEW_ADMIN_STATS,
              description="Viewing Site Statistics")
    log.save()

    environment = {}    # OS environment information
    environment['Python'] = f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}"
    uname = os.uname()
    environment['OS'] = f"{uname.sysname} ({uname.release})"
    hostname = socket.gethostname()
    environment['Hostname'] = f"{hostname}"
    environment['Django'] = django.get_version()
    import git
    try:
        repo = git.Repo(search_parent_directories=True)
        sha = repo.head.object.hexsha
        short_sha = repo.git.rev_parse(sha, short=8)
        branch = repo.active_branch
        commit_date = time.strftime("%a, %d %b %Y %H:%M UTC", time.gmtime(repo.head.object.committed_date))
        environment['Git version'] = f"{branch} ({short_sha})"
        environment['Git commit'] = commit_date
    except Exception:
        environment['Git version'] = 'Not found!'
    # Celery task processing information
    if settings.TASKS_ENABLED:
        celery_info = get_celery_info()
        if not celery_info or celery_info['stats'] is None:
            environment['Tasks'] = "Enabled, NOT running"
        else:
            environment['Tasks'] = "Enabled and running"
    else:
        environment['Tasks'] = "Disabled"
    environment['OpenL2M version'] = f"{settings.VERSION} ({settings.VERSION_DATE})"

    db_items = {}   # database object item counts
    db_items['Switches'] = Switch.objects.count()
    # need to calculate switchgroup count, as we count only groups with switches!
    group_count = 0
    for group in SwitchGroup.objects.all():
        if group.switches.count():
            group_count += 1
    db_items['Switch Groups'] = group_count
    db_items['Vlans'] = VLAN.objects.count()
    db_items['Vlan Groups'] = VlanGroup.objects.count()
    db_items['SNMP Profiles'] = SnmpProfile.objects.count()
    db_items['Netmiko Profiles'] = NetmikoProfile.objects.count()
    db_items['Commands'] = Command.objects.count()
    db_items['Command Lists'] = CommandList.objects.count()
    db_items['Tasks'] = Task.objects.count()
    db_items['Log Entries'] = Log.objects.count()

    usage = {}  # usage statistics

    filter = {}
    filter['type'] = int(LOG_TYPE_CHANGE)
    filter['timestamp__date'] = datetime.date.today()
    usage['Changes today'] = Log.objects.filter(**filter).count()

    filter = {}
    filter['type'] = int(LOG_TYPE_CHANGE)
    filter['timestamp__gte'] = timezone.now().date() - datetime.timedelta(days=7)
    usage['Changes last 7 days'] = Log.objects.filter(**filter).count()

    filter = {}
    filter['type'] = int(LOG_TYPE_CHANGE)
    filter['timestamp__gte'] = timezone.now().date() - datetime.timedelta(days=31)
    usage['Changes last 31 days'] = Log.objects.filter(**filter).count()

    filter = {}
    filter['type'] = int(LOG_TYPE_CHANGE)
    usage['Changes logged'] = Log.objects.filter(**filter).count()

    user_list = get_current_users()

    # render the template
    return render(request, template_name, {
        'db_items': db_items,
        'usage': usage,
        'environment': environment,
        'user_list': user_list,
    })


#
# "Administrative" views
#

@login_required(redirect_field_name=None)
def admin_activity(request):
    """
    This shows recent activity
    """

    template_name = 'admin_activity.html'

    # what do we have rights to:
    if not request.user.is_superuser and not request.user.is_staff:
        # get them out of here!
        # log my activity
        log = Log(user=request.user,
                  ip_address=get_remote_ip(request),
                  type=LOG_TYPE_ERROR,
                  action=LOG_VIEW_ALL_LOGS,
                  description="Not Allowed to View All Logs")
        log.save()
        error = Error()
        error.status = True
        error.description = "You do not have access to this page!"
        return error_page(request=request, group=False, switch=False, error=error)

    # log my activity
    log = Log(user=request.user,
              ip_address=get_remote_ip(request),
              type=LOG_TYPE_VIEW,
              action=LOG_VIEW_ALL_LOGS)

    page_number = int(request.GET.get('page', default=1))

    # look at query string, and filter as needed
    filter = {}
    if len(request.GET) > 0:
        if request.GET.get('type', ''):
            filter['type'] = int(request.GET['type'])
        if request.GET.get('action', ''):
            filter['action'] = int(request.GET['action'])
        if request.GET.get('user', ''):
            filter['user_id'] = int(request.GET['user'])
        if request.GET.get('switch', ''):
            filter['switch_id'] = int(request.GET['switch'])
        if request.GET.get('group', ''):
            filter['group_id'] = int(request.GET['group'])

    # now set the filter, if found
    if(len(filter) > 0):
        logs = Log.objects.all().filter(**filter).order_by('-timestamp')
        log.description = f"Viewing filtered logs: {filter} (page {page_number})"
        title = 'Filtered Activities'
    else:
        logs = Log.objects.all().order_by('-timestamp')
        log.description = f"Viewing all logs (page {page_number})"
        title = 'All Activities'
    log.save()

    # setup pagination of the resulting activity logs
    paginator = Paginator(logs, settings.PAGINATE_COUNT)    # Show set number of contacts per page.
    logs_page = paginator.get_page(page_number)

    # render the template
    return render(request, template_name, {
        'logs': logs_page,
        'paginator': paginator,
        'filter': filter,
        'types': LOG_TYPE_CHOICES,
        'actions': LOG_ACTION_CHOICES,
        'switches': Switch.objects.all().order_by('name'),
        'switchgroups': SwitchGroup.objects.all().order_by('name'),
        'users': User.objects.all().order_by('username'),
        'log_title': title,
        'logs_link': False,
    })


@login_required(redirect_field_name=None)
def tasks(request):
    """
    This shows scheduled tasks for users
    """
    if not user_can_access_task(request, False):
        error = Error()
        error.description = "You cannot schedule tasks. If this is an error, please contact your administrator!"
        return error_page(request=request, group=False, switch=False, error=error)

    template_name = 'tasks.html'

    task_process_running = is_celery_running()
    if request.user.is_superuser:
        # show all types of tasks
        tasks = Task.objects.all().filter().order_by('status', '-eta')
    else:
        # only show non-deleted to regular users
        tasks = Task.objects.all().filter(user=request.user).exclude(status=TASK_STATUS_DELETED).order_by('status', '-eta')
        if tasks.count() == 0:
            return success_page(request, False, False, "You have not scheduled any tasks!")

    page_number = int(request.GET.get('page', default=1))

    # log my activity
    log = Log(user=request.user,
              ip_address=get_remote_ip(request),
              type=LOG_TYPE_VIEW,
              action=LOG_VIEW_TASKS,
              description=f"Viewing tasks (page {page_number})")
    log.save()

    paginator = Paginator(tasks, settings.PAGINATE_COUNT)    # Show set number of contacts per page.
    tasks_page = paginator.get_page(page_number)

    return render(request, template_name, {
        'tasks': tasks_page,
        'paginator': paginator,
        'task_process_running': task_process_running,
    })


@login_required(redirect_field_name=None)
def task_details(request, task_id):
    """
    This shows details of a scheduled task
    """
    template_name = 'task_details.html'

    task = get_object_or_404(Task, pk=task_id)

    if not user_can_access_task(request, task):
        # log my activity
        log = Log(user=request.user,
                  ip_address=get_remote_ip(request),
                  type=LOG_TYPE_ERROR,
                  action=LOG_VIEW_TASK_DETAILS,
                  description=f"You do not have permission to view task {task_id} details!")
        log.save()
        error = Error()
        error.description = log.description
        return error_page(request=request, group=False, switch=False, error=error)

    # log my activity
    log = Log(user=request.user,
              ip_address=get_remote_ip(request),
              type=LOG_TYPE_VIEW,
              action=LOG_VIEW_TASK_DETAILS,
              description=f"Viewing task {task_id} details")
    log.save()

    task_process_running = is_celery_running()

    # render the template
    return render(request, template_name, {
        'task': task,
        'task_process_running': task_process_running,
    })


@login_required(redirect_field_name=None)
def task_delete(request, task_id):
    """
    This deleted a scheduled task
    """
    task = get_object_or_404(Task, pk=task_id)

    if not user_can_access_task(request, task):
        log = Log(user=request.user,
                  ip_address=get_remote_ip(request),
                  action=LOG_TASK_DELETE,
                  type=LOG_TYPE_ERROR,
                  description=f"You do not have permission to delete task {task_id} !")
        log.save()
        error = Error()
        error.description = log.description
        return error_page(request=request, group=False, switch=False, error=error)

    if not is_celery_running():
        description = "The Task Process is NOT running, so we cannot delete this task at the moment!"
        return warning_page(request=request, group=False, switch=False, description=description)

    # log my activity
    log = Log(user=request.user,
              ip_address=get_remote_ip(request),
              action=LOG_TASK_DELETE)
    if task_revoke(task, False):
        log.type = LOG_TYPE_CHANGE
        log.description = f"Task {task_id} deleted"
        log.save()
        return success_page(request, False, False, f"Task {task_id} has been deleted!")
    else:
        log.description = f"Error deleting task {task_id} !"
        log.type = LOG_TYPE_ERROR
        log.save()
        error = Error()
        error.description = log.description
        return error_page(request=request, group=False, switch=False, error=error)


@login_required(redirect_field_name=None)
def task_terminate(request, task_id):
    """
    This terminates a hung (or running) task
    Only callable by admins or staff!
    """
    if not request.user.is_superuser and not request.user.is_staff:
        log = Log(user=request.user,
                  ip_address=get_remote_ip(request),
                  action=LOG_TASK_TERMINATE,
                  type=LOG_TYPE_ERROR,
                  description=f"You do not have permission to terminate task {task_id}. Please contact an administrator!")
        log.save()
        error = Error()
        error.description = log.description
        return error_page(request=request, group=False, switch=False, error=error)

    task = get_object_or_404(Task, pk=task_id)

    if not is_celery_running():
        description = "The Task Process is NOT running, so we cannot terminate this task at the moment!"
        return warning_page(request=request, group=False, switch=False, description=description)

    # log my activity
    log = Log(user=request.user,
              ip_address=get_remote_ip(request),
              action=LOG_TASK_TERMINATE)
    if task_revoke(task, True):
        log.type = LOG_TYPE_CHANGE
        log.description = f"Task {task_id} terminated"
        log.save()
        return success_page(request, False, False, f"Task {task_id} has been terminated (killed)!")
    else:
        log.type = LOG_TYPE_ERROR
        log.description = f"Error terminating task {task_id}"
        log.save()
        error = Error()
        error.description = log.description
        return error_page(request=request, group=False, switch=False, error=error)


def task_revoke(task, terminate):
    """
    Does the actual works of deleting/revoking/terminating a tasks
    """
    from openl2m.celery import app
    try:
        result = app.control.revoke(task.celery_task_id, terminate=terminate)
    except Exception as e:
        # should probably log something here!
        return False
    # update the task:
    task.status = TASK_STATUS_DELETED
    task.save()
    return True


#
# UTILITY FUNCTIONS here
#

def success_page(request, group, switch, description):
    """
    Generic function to return an 'function succeeded' page
    requires the http request(), Group(), Switch() objects
    and a string description of the success.
    """
    return render(request, 'success_page.html', {
        'group': group,
        'switch': switch,
        'description': description,
    })


def warning_page(request, group, switch, description):
    """
    Generic function to return an warning page
    requires the http request(), Group() and Switch() objects,
    and a string description with the warning.
    """
    return render(request, 'warning_page.html', {
        'group': group,
        'switch': switch,
        'description': description,
    })


def error_page(request, group, switch, error):
    """
    Generic function to return an error page
    requires the http request(), Group(), Switch() and Error() objects
    """
    return render(request, 'error_page.html', {
        'group': group,
        'switch': switch,
        'error': error,
    })


def rights_to_group_and_switch(request, group_id, switch_id):
    """
    Check if the current user has rights to this switch in this group
    Returns True if allowed, False if not!
    """
    if request.user.is_superuser or request.user.is_staff:
        return True
    # for regular users, check permissions:
    permissions = get_from_http_session(request, 'permissions')
    if permissions and isinstance(permissions, dict) and \
       int(group_id) in permissions.keys():
       switches = permissions[int(group_id)]
       if isinstance(switches, dict) and int(switch_id) in switches.keys():
           return True
    return False


def user_can_access_task(request, task=False):
    """
    Check if the current user has rights to this task.
    This needs more work, for now keep it simle.
    Return True or False
    """
    if request.user.is_superuser or request.user.is_staff:
        return True
    if task:
        if task.user == request.user:
            return True
        # does the user have rights to the group of this task?
        permissions = get_from_http_session(request, 'permissions')
        if permissions and isinstance(permissions, dict) and \
           str(task.group.id) in permissions.keys():
            #  if member of group there is no need to check switch!
            return True
    # deny others
    return False
