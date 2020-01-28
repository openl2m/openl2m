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
import time
import datetime
import traceback
import git
import json

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

from openl2m.celery import get_celery_info, is_celery_running
from switches.models import *
from switches.constants import *
from switches.connect.connect import *
from switches.connect.constants import *
from switches.connect.snmp import *
from switches.connect.netmiko.connector import *
from switches.utils import *
from switches.tasks import bulkedit_task, bulkedit_processor
from users.utils import *


@login_required
def switches(request):
    """
    This is the "home view", at "/"
    It shows the list of switches a user has access to
    """

    template_name = 'home.html'

    # back to the home screen, clear session cache
    # so we re-read switche as needed
    clear_session_oid_cache(request)

    # find the groups with switches that we have rights to:
    regular_user = True
    switchgroups = {}
    permissions = {}
    if request.user.is_superuser or request.user.is_staff:
        regular_user = False
        # optimize data queries, get all related field at once!
        groups = SwitchGroup.objects.all().order_by('name')

    else:
        # figure out what this users has access to.
        # Note we use the ManyToMany 'related_name' attribute for readability!
        groups = request.user.switchgroups.all().order_by('name')

    for group in groups:
        if group.switches.count():
            switchgroups[group.name] = group
            if regular_user:
                # set this group, and the switches, in web session to track permissions
                permissions[group.id] = {}
                for switch in group.switches.all():
                    if switch.status == SWITCH_STATUS_ACTIVE and switch.snmp_profile:
                        permissions[group.id][switch.id] = switch.id

    save_to_http_session(request, 'permissions', permissions)

    # log my activity
    log = Log()
    log.user = request.user
    log.ip_address = get_remote_ip(request)
    log.action = LOG_VIEW_SWITCHGROUPS
    log.description = "Viewing switch groups"
    log.type = LOG_TYPE_VIEW
    log.save()

    # render the template
    return render(request, template_name, {
        'groups': switchgroups,
        'group_count': len(switchgroups),
    })


@login_required
def switch_basics(request, group_id, switch_id):
    """
    "basic" switch view, i.e. interface data only.
    Simply call switch_view() with proper parameter
    """
    return switch_view(request, group_id, switch_id, 'basic')


@login_required
def switch_arp_lldp(request, group_id, switch_id):
    """
    "details" switch view, i.e. with Ethernet/ARP/LLDP data.
    Simply call switch_view() with proper parameter
    """
    return switch_view(request, group_id, switch_id, 'arp_lldp')


@login_required
def switch_hw_info(request, group_id, switch_id):
    """
    "hardware info" switch view, i.e. read detailed system hardware ("entity") data.
    Simply call switch_view() with proper parameter
    """
    return switch_view(request, group_id, switch_id, 'hw_info')


def switch_view(request, group_id, switch_id, view, command_id=-1, interface_id=-1):
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
        error.description = "You do not have access to this switch"
        return error_page(request, group, switch, error)

    log = Log()
    log.user = request.user
    log.ip_address = get_remote_ip(request)
    log.switch = switch
    log.group = group
    log.action = LOG_VIEW_SWITCH
    log.type = LOG_TYPE_VIEW
    log.description = "Viewing switch (%s)" % view

    try:
        conn = get_connection_object(request, group, switch)
    except Exception as e:
        log.type = LOG_TYPE_ERROR
        log.description = "SNMP ERROR: Viewing switch (%s)" % view
        log.save()
        error = Error()
        error.description = "There was a failure communicating with this switch. Please contact your administrator to make sure switch data is correct in the database!"
        error.details = traceback.format_exc()
        return error_page(request, group, switch, error)

    if not conn.get_switch_basic_info():
        # errors
        log.type = LOG_TYPE_ERROR
        log.description = "ERROR in get_basic_switch_info()"
        log.save()
        return error_page(request, group, switch, conn.error)

    if view == 'hw_info':
        if not conn.get_switch_hardware_details():
            # errors
            log.type = LOG_TYPE_ERROR
            log.description = "ERROR in get_hardware_details()"
            log.save()
            # don't render error, since we have already read the basic interface data
            # Note that SNMP errors are already added to warnings!
            # return error_page(request, group, switch, conn.error)

    if view == 'arp_lldp':
        if not conn.get_switch_client_data():
            log.type = LOG_TYPE_ERROR
            log.description = "ERROR get_switch_client_data()"
            log.save()
            # don't render error, since we have already read the basic interface data
            # Note that errors are already added to warnings!
            # return error_page(request, group, switch, conn.error)

    # does this switch have any commands defined?
    cmd = False
    # we need a netmiko config before we can issue commands!
    if switch.netmiko_profile and switch.command_list:
        # default command dictionary info:
        cmd = {
            'state': 'list',        # 'list' or 'run'
            'id': 0,                # command chosen to run
            'output': '',           # output of chosen command
            'error_descr': '',      # if set, error that occured running command
            'error_details': '',    # and the details for above
        }

        if command_id > 0:
            """
            Exexute a specific Command object by ID
            """
            cmd['state'] = 'run'
            cmd['id'] = int(command_id)
            c = get_object_or_404(Command, pk=command_id)
            cmd['command'] = c.command
            if c.type == CMD_TYPE_INTERFACE and interface_id > 0:
                if interface_id in conn.interfaces.keys():
                    cmd['command'] = c.command % conn.interfaces[interface_id].name

            # log it first!
            log.type = LOG_TYPE_COMMAND
            log.action = LOG_EXECUTE_COMMAND
            log.description = cmd['command']
            # now go do it:
            nm = NetmikoConnector(switch)
            if nm.execute_command(cmd['command']):
                cmd['output'] = nm.output
                del nm
            else:
                # error occured, pass it on
                log.type = LOG_TYPE_ERROR
                log.description = "%s: %s" % (log.description, nm.error.description)
                cmd['error_descr'] = nm.error.description
                cmd['error_details'] = nm.error.details

    log.save()

    # get recent "non-viewing" activity for this switch
    # for now, show most recent 25 activities
    logs = Log.objects.all().filter(switch=switch, type__gt=LOG_TYPE_VIEW).order_by('-timestamp')[:25]

    # are there any scheduled tasks for this switch?
    if settings.TASKS_ENABLED:
        task_process_running = is_celery_running()
        tasks = Task.objects.all().filter(switch=switch, status=TASK_STATUS_SCHEDULED).order_by('-eta')
    else:
        tasks = False

    time_since_last_read = time_duration(time.time() - conn.basic_info_read_time)

    # finally, verify what this user can do:
    bulk_edit = user_can_bulkedit(request.user, group, switch)
    allow_tasks = user_can_run_tasks(request.user, group, switch)

    return render(request, template_name, {
        'group': group,
        'switch': switch,
        'connection': conn,
        'logs': logs,
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
@login_required
def switch_bulkedit(request, group_id, switch_id):
    """
    Change several interfaces at once.
    """
    return bulkedit_form_handler(request, group_id, switch_id, False)


@login_required
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
        error.description = "You do not have access to this switch"
        return error_page(request, group, switch, error)

    conn = get_connection_object(request, group, switch)

    # read the submitted form data:
    interface_change = bool(request.POST.get('interface_change', False))
    poe_choice = int(request.POST.get('poe_choice', False))
    new_pvid = int(request.POST.get('new_pvid', -1))
    new_alias = str(request.POST.get('new_alias', ''))
    interface_list = request.POST.getlist('interface_list')
    remote_ip = get_remote_ip(request)
    save_config = bool(request.POST.get('save_config', False))

    # was anything submitted?
    if len(interface_list) == 0:
        return warning_page(request, group, switch, mark_safe("Please select at least 1 interface!"))

    if not interface_change and not poe_choice and new_pvid < 0 and not new_alias:
        return warning_page(request, group, switch, mark_safe("Please select at least 1 thing to change!"))

    # perform some checks on valid data first:
    errors = []

    # check if the new description/alias is allowed:
    if new_alias and settings.IFACE_ALIAS_NOT_ALLOW_REGEX:
        match = re.match(settings.IFACE_ALIAS_NOT_ALLOW_REGEX, new_alias)
        if match:
            log = Log()
            log.user = request.user
            log.ip_address = remote_ip
            log.switch = switch
            log.group = group
            log.type = LOG_TYPE_ERROR
            log.action = LOG_CHANGE_BULK_EDIT
            log.description = "The description '%s' is not allowed!" % new_alias
            log.save()
            new_alias = ''
            errors.append("The description '%s' is not allowed!" % new_alias)

    # safety-check: is the new PVID allowed:
    if new_pvid > 0:
        conn._set_allowed_vlans()
        if new_pvid not in conn.allowed_vlans.keys():
            log = Log()
            log.user = request.user
            log.ip_address = remote_ip
            log.switch = switch
            log.group = group
            log.type = LOG_TYPE_ERROR
            log.action = LOG_CHANGE_BULK_EDIT
            log.description = "The new vlan '%d' is not allowed!" % new_pvid
            log.save()
            new_pvid = -1   # force no change!
            errors.append("The new vlan '%d' is not allowed!" % new_pvid)

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
            eta_with_tz = "%s %s" % (eta, get_local_timezone_offset())
            try:
                # this needs timezone parsing!
                eta_datetime = datetime.datetime.strptime(eta_with_tz, "%Y-%m-%d %H:%M %z")
            except Exception as e:
                # unsupported time format!
                errors.append("Invalid date/time format, please use YYYY-MM-DD HH:MM !")

    if len(errors) > 0:
        error = Error()
        error.description = "Some form values were invalid, please correct and resubmit!"
        error.details = mark_safe("\n<br>".join(errors))
        return error_page(request, group, switch, error)

    # get the name of the interfaces as well (with the submitted ifIndex values)
    # so that we can show the names in the Task() and Log() objects
    # additionally, also get the current state, to be able to "undo" the update
    interfaces = {}
    undo_info = {}
    for index in interface_list:
        if_index = int(index)
        if if_index in conn.interfaces.keys():
            iface = conn.interfaces[if_index]
            interfaces[if_index] = iface.name
            if is_task:
                # save the current state
                current = {}
                current['if_index'] = if_index
                current['name'] = iface.name    # for readability
                if new_pvid > 0:
                    current['pvid'] = iface.untagged_vlan
                if new_alias:
                    current['description'] = iface.alias
                if poe_choice != BULKEDIT_POE_NONE and iface.poe_entry:
                    current['poe_state'] = iface.poe_entry.admin_status
                if interface_change:
                    current['admin_state'] = iface.admin_status
                undo_info[if_index] = current

    if is_task:
        # log this first
        log = Log()
        log.user = request.user
        log.ip_address = get_remote_ip(request)
        log.switch = switch
        log.group = group
        log.type = LOG_TYPE_CHANGE
        log.action = LOG_BULK_EDIT_TASK_SUBMIT
        log.description = "Bulk Edit Task Submitted (%s) to run at %s" % (task_description, eta)
        log.save()

        # create a task to track progress
        task = Task()
        task.user = request.user
        task.group = group
        task.switch = switch
        task.eta = eta_datetime
        task.type = TASK_TYPE_BULKEDIT
        task.description = task_description
        args = {}
        args['user_id'] = request.user.id
        args['group_id'] = group_id
        args['switch_id'] = switch_id
        args['interface_change'] = interface_change
        args['poe_choice'] = poe_choice
        args['new_pvid'] = new_pvid
        args['new_alias'] = new_alias
        args['interfaces'] = interfaces
        args['save_config'] = save_config
        task.arguments = json.dumps(args)
        task.reverse_arguments = json.dumps(undo_info)
        task.save()

        # now go schedule the task
        try:
            celery_task_id = bulkedit_task.apply_async((task.id, request.user.id, group_id, switch_id,
                                                       interface_change, poe_choice, new_pvid,
                                                       new_alias, interfaces, save_config),
                                                       eta=eta_datetime)
        except Exception as e:
            error = Error()
            error.description = "There was an error submitting your task. Please contact your administrator to make sure the job broker is running!"
            error.details = mark_safe("%s<br><br>%s" % (repr(e), traceback.format_exc()))
            return error_page(request, group, switch, error)

        # update task:
        task.status = TASK_STATUS_SCHEDULED
        task.celery_task_id = celery_task_id
        task.save()

        description = "New Bulk-Edit task was submitted to run at %s (task id = %s)" % (eta, task.id)
        return success_page(request, group, switch, mark_safe(description))

    # handle regular submit, execute now!
    results = bulkedit_processor(request, request.user.id, group_id, switch_id,
                                 interface_change, poe_choice, new_pvid,
                                 new_alias, interfaces, False)

    # indicate we need to save config!
    if results['success_count'] > 0:
        conn.set_save_needed(True)

    # now build the results page from the outputs
    description = "%s\n%s\n" % ("\n<div><strong>Results:</strong></div>",
                                "\n<br>".join(results['outputs']))
    if results['error_count'] > 0:
        err = Error()
        err.description = "Bulk-Edit errors"
        err.details = mark_safe(description)
        return error_page(request, group, switch, err)
    else:
        return success_page(request, group, switch, mark_safe(description))


#
# Change admin status, ie port Enable/Disable
#
@login_required
def interface_admin_change(request, group_id, switch_id, interface_id, new_state):
    """
    Toggle the admin status of an interface, ie admin up or down.
    """
    group = get_object_or_404(SwitchGroup, pk=group_id)
    switch = get_object_or_404(Switch, pk=switch_id)

    if not rights_to_group_and_switch(request, group_id, switch_id):
        error = Error()
        error.description = "You do not have access to this switch"
        return error_page(request, group, switch, error)

    conn = get_connection_object(request, group, switch)
    iface = conn.get_interface_by_index(interface_id)

    log = Log()
    log.user = request.user
    log.ip_address = get_remote_ip(request)
    log.switch = switch
    log.group = group
    log.if_index = interface_id
    log.type = LOG_TYPE_CHANGE
    if new_state == IF_ADMIN_STATUS_UP:
        log.action = LOG_CHANGE_INTERFACE_UP
        log.description = "Interface %s: Enabled" % iface.name
        state = "Enabled"
    else:
        log.action = LOG_CHANGE_INTERFACE_DOWN
        log.description = "Interface %s: Disabled" % iface.name
        state = "Disabled"

    # make sure we cast the proper type here! Ie this needs an Integer()
    retval = conn._set(IF_ADMIN_STATUS + "." + str(interface_id), new_state, 'i')
    if retval < 0:
        log.description = "ERROR: " + conn.error.description
        log.type = LOG_TYPE_ERROR
        log.save()
        return error_page(request, group, switch, conn.error)

    # indicate we need to save config!
    conn.set_save_needed(True)

    log.save()

    description = 'Interface "%s" is now %s' % (iface.name, state)
    return success_page(request, group, switch, description)


@login_required
def interface_alias_change(request, group_id, switch_id, interface_id):
    """
    Change the ifAlias aka description on an interfaces.
    """
    group = get_object_or_404(SwitchGroup, pk=group_id)
    switch = get_object_or_404(Switch, pk=switch_id)

    if not rights_to_group_and_switch(request, group_id, switch_id):
        error = Error()
        error.description = "You do not have access to this switch"
        return error_page(request, group, switch, error)

    conn = get_connection_object(request, group, switch)
    iface = conn.get_interface_by_index(interface_id)

    # read the submitted form data:
    new_alias = str(request.POST.get('new_alias', ''))

    if iface.alias == new_alias:
        description = "New description is the same, please change it first!"
        return warning_page(request, group, switch, description)

    log = Log()
    log.user = request.user
    log.ip_address = get_remote_ip(request)
    log.switch = switch
    log.group = group
    log.if_index = interface_id
    log.type = LOG_TYPE_CHANGE
    log.action = LOG_CHANGE_INTERFACE_ALIAS

    # are we allowed to change alias ?
    if not iface.can_edit_alias:
        log.description = "Interface %s description edit not allowed" % iface.name
        log.type = LOG_TYPE_ERROR
        log.save()
        error = Error()
        error.description = "You are not allowed to change the interface description"
        return error_page(request, group, switch, error)

    # check if the alias is allowed:
    if settings.IFACE_ALIAS_NOT_ALLOW_REGEX:
        match = re.match(settings.IFACE_ALIAS_NOT_ALLOW_REGEX, new_alias)
        if match:
            log.type = LOG_TYPE_ERROR
            log.save()
            error = Error()
            error.description = "The description '%s' is not allowed!" % new_alias
            return error_page(request, group, switch, error)

    # check if the original alias starts with a string we have to keep
    if settings.IFACE_ALIAS_KEEP_BEGINNING_REGEX:
        keep_format = "(^%s)" % settings.IFACE_ALIAS_KEEP_BEGINNING_REGEX
        match = re.match(keep_format, iface.alias)
        if match:
            # check of new submitted alias begins with this string:
            match_new = re.match(keep_format, new_alias)
            if not match_new:
                # required start string NOT found on new alias, so prepend it!
                new_alias = "%s %s" % (match[1], new_alias)

    # log the work!
    log.description = "Interface %s: Description = %s" % (iface.name, new_alias)

    # make sure we cast the proper type here! Ie this needs an string
    retval = conn._set(IFMIB_ALIAS + "." + str(interface_id), new_alias, 'OCTETSTRING')
    if retval < 0:
        log.description = "ERROR: %s" % conn.error.description
        log.type = LOG_TYPE_ERROR
        log.save()
        return error_page(request, group, switch, conn.error)

    # indicate we need to save config!
    conn.set_save_needed(True)

    log.save()

    description = 'Interface "%s" description changed' % iface.name
    return success_page(request, group, switch, description)


@login_required
def interface_pvid_change(request, group_id, switch_id, interface_id):
    """
    Change the PVID untagged vlan on an interfaces.
    This still needs to handle dot1q trunked ports.
    """
    group = get_object_or_404(SwitchGroup, pk=group_id)
    switch = get_object_or_404(Switch, pk=switch_id)

    if not rights_to_group_and_switch(request, group_id, switch_id):
        error = Error()
        error.description = "You do not have access to this switch"
        return error_page(request, group, switch, error)

    conn = get_connection_object(request, group, switch)
    iface = conn.get_interface_by_index(interface_id)

    # read the submitted form data:
    new_pvid = int(request.POST.get('new_pvid', 0))
    # did the vlan change?
    if iface.untagged_vlan == int(new_pvid):
        description = "New vlan %d is the same, please change the vlan first!" % iface.untagged_vlan
        return warning_page(request, group, switch, description)

    # stuff to do here, so start a log entry...
    log = Log()
    log.user = request.user
    log.ip_address = get_remote_ip(request)
    log.switch = switch
    log.group = group
    log.if_index = interface_id
    log.type = LOG_TYPE_CHANGE
    log.action = LOG_CHANGE_INTERFACE_PVID
    log.description = "Interface %s: new PVID = %s (was %s)" % (iface.name, str(new_pvid), str(iface.untagged_vlan))

    # are we allowed to change to this vlan ?
    conn._set_allowed_vlans()
    if not int(new_pvid) in conn.allowed_vlans.keys():
        log.action = LOG_CHANGE_INTERFACE_PVID + LOG_DENIED
        log.save()
        error = Error()
        error.status = True
        error.description = "New vlan %d is not valid on this switch" % new_pvid
        return error_page(request, group, switch, error)

    # make sure we cast the proper type here! Ie this needs an Integer()
    retval = conn.set_interface_untagged_vlan(int(interface_id), iface.untagged_vlan, int(new_pvid))
    if retval < 0:
        log.description = "ERROR: %s" % conn.error.description
        log.type = LOG_TYPE_ERROR
        log.save()
        return error_page(request, group, switch, conn.error)

    # indicate we need to save config!
    conn.set_save_needed(True)

    # all OK, save log
    log.save()

    description = 'Interface "%s" changed to vlan %d' % (iface.name, new_pvid)
    return success_page(request, group, switch, description)


#
# Change PoE status, i.e. port power Enable/Disable
#
@login_required
def interface_poe_change(request, group_id, switch_id, interface_id, new_state):
    """
    Change the PoE status of an interfaces.
    This still needs to be tested for propper PoE port to interface ifIndex mappings.
    """
    group = get_object_or_404(SwitchGroup, pk=group_id)
    switch = get_object_or_404(Switch, pk=switch_id)

    if not rights_to_group_and_switch(request, group_id, switch_id):
        error = Error()
        error.status = True
        error.description = "You do not have access to this switch"
        return error_page(request, group, switch, error)

    conn = get_connection_object(request, group, switch)
    iface = conn.get_interface_by_index(interface_id)

    log = Log()
    log.user = request.user
    log.ip_address = get_remote_ip(request)
    log.switch = switch
    log.group = group
    log.if_index = interface_id
    log.type = LOG_TYPE_CHANGE
    if new_state == POE_PORT_ADMIN_ENABLED:
        log.action = LOG_CHANGE_INTERFACE_POE_UP
        log.description = "Interface %s: Enabling PoE" % iface.name
        state = "Enabled"
    else:
        log.action = LOG_CHANGE_INTERFACE_POE_DOWN
        log.description = "Interface %s: Disabling PoE" % iface.name
        state = "Disabled"

    if not iface.poe_entry:
        # should not happen...
        log.type = LOG_TYPE_ERROR
        log.description = "Interface %s does not support PoE" % iface.name
        error = Error()
        error.status = True
        error.description = log.descr
        log.save()
        return error_page(request, group, switch, error)

    # the PoE index is kept in the iface.poe_entry

    # make sure we cast the proper type here! Ie this needs an Integer()
    retval = conn._set(POE_PORT_ADMINSTATUS + "." + iface.poe_entry.index, int(new_state), 'i')
    if retval < 0:
        log.description = "ERROR: " + conn.error.description
        log.type = LOG_TYPE_ERROR
        log.save()
        return error_page(request, group, switch, conn.error)

    # indicate we need to save config!
    conn.set_save_needed(True)

    log.save()

    description = 'Interface "%s" PoE is now %s' % (iface.name, state)
    return success_page(request, group, switch, description)


#
# Toggle PoE status Down then Up
#
@login_required
def interface_poe_down_up(request, group_id, switch_id, interface_id):
    """
    Toggle the PoE status of an interfaces. I.e disable, wait some, then enable again.
    """
    group = get_object_or_404(SwitchGroup, pk=group_id)
    switch = get_object_or_404(Switch, pk=switch_id)

    if not rights_to_group_and_switch(request, group_id, switch_id):
        error = Error()
        error.status = True
        error.description = "You do not have access to this switch"
        return error_page(request, group, switch, error)

    conn = get_connection_object(request, group, switch)
    iface = conn.get_interface_by_index(interface_id)

    log = Log()
    log.user = request.user
    log.ip_address = get_remote_ip(request)
    log.switch = switch
    log.group = group
    log.if_index = interface_id
    log.type = LOG_TYPE_CHANGE
    log.action = LOG_CHANGE_INTERFACE_POE_TOGGLE_DOWN_UP
    log.description = "Interface %s: PoE Toggle Down-Up" % iface.name

    if not iface.poe_entry:
        # should not happen...
        log.type = LOG_TYPE_ERROR
        log.description = "Interface %s does not support PoE" % iface.name
        error = Error()
        error.status = True
        error.description = log.descr
        log.save()
        return error_page(request, group, switch, error)

    # the PoE information (index) is kept in the iface.poe_entry
    if not iface.poe_entry.admin_status == POE_PORT_ADMIN_ENABLED:
        # should not happen...
        log.type = LOG_TYPE_ERROR
        log.description = "Interface %s does not have PoE enabled" % iface.name
        error = Error()
        error.status = True
        error.description = log.descr
        log.save()
        return error_page(request, group, switch, error)

    # First disable PoE. Make sure we cast the proper type here! Ie this needs an Integer()
    retval = conn._set("%s.%s" % (POE_PORT_ADMINSTATUS, iface.poe_entry.index), POE_PORT_ADMIN_DISABLED, 'i')
    if retval < 0:
        log.description = "ERROR: Toggle-Disable PoE on %s - %s " % (iface.name, conn.error.description)
        log.type = LOG_TYPE_ERROR
        log.save()
        return error_page(request, group, switch, conn.error)

    # delay to let the device cold-boot properly
    time.sleep(settings.POE_TOGGLE_DELAY)

    # Now enable PoE again...
    retval = conn._set("%s.%s" % (POE_PORT_ADMINSTATUS, iface.poe_entry.index), POE_PORT_ADMIN_ENABLED, 'i')
    if retval < 0:
        log.description = "ERROR: Toggle-Enable PoE on %s - %s " % (iface.name, conn.error.description)
        log.type = LOG_TYPE_ERROR
        log.save()
        return error_page(request, group, switch, conn.error)

    # no state change, so no save needed!
    log.save()

    description = 'Interface "%s" PoE was toggled!' % iface.name
    return success_page(request, group, switch, description)


@login_required
def switch_save_config(request, group_id, switch_id, view):
    """
    This will save the running config via SNMP, on supported platforms
    """
    group = get_object_or_404(SwitchGroup, pk=group_id)
    switch = get_object_or_404(Switch, pk=switch_id)

    if not rights_to_group_and_switch(request, group_id, switch_id):
        error = Error()
        error.description = "You do not have access to this switch"
        return error_page(request, group, switch, error)

    log = Log()
    log.user = request.user
    log.ip_address = get_remote_ip(request)
    log.switch = switch
    log.group = group
    log.action = LOG_SAVE_SWITCH
    log.type = LOG_TYPE_CHANGE
    log.description = "Saving switch config"

    try:
        conn = get_connection_object(request, group, switch)
    except Exception:
        log.type = LOG_TYPE_ERROR
        log.description = "Getting SNMP data (%s)" % view
        log.save()
        error = Error()
        error.description = "Could not get connection. Please contact your administrator to make sure switch data is correct in the database!"
        return error_page(request, group, switch, error)

    if conn.can_save_config() and conn.get_save_needed():
        # we can save
        retval = conn.save_running_config()
        if retval < 0:
            # an error happened!
            log.type = LOG_TYPE_ERROR
            log.save()
            return error_page(request, group, switch, conn.error)

        # clear save flag
        conn.set_save_needed(False)

    else:
        log.type = LOG_TYPE_ERROR
        log.description = "Can not save config"
        log.save()
        error = Error()
        error.description = "This switch model cannot save or does not need to save the config"
        return error_page(request, group, switch, error)

    # all OK
    log.save()

    description = 'Config was saved for "%s"' % switch.name
    return success_page(request, group, switch, description)


@login_required
def switch_cmd_output(request, group_id, switch_id):
    """
    Go parse a global switch command that was submitted in the form
    """
    command_id = int(request.POST.get('command_id', ''))
    return switch_view(request, group_id, switch_id, 'basic', command_id)


@login_required
def interface_cmd_output(request, group_id, switch_id, interface_id):
    """
    Parse the interface-specific form and build the commands
    """
    command_id = int(request.POST.get('command_id', ''))
    return switch_view(request, group_id, switch_id, 'basic', command_id, interface_id)


@login_required
def switch_reload(request, group_id, switch_id, view):
    """
    This forces a new reading of basic switch SNMP data
    """

    group = get_object_or_404(SwitchGroup, pk=group_id)
    switch = get_object_or_404(Switch, pk=switch_id)

    if not rights_to_group_and_switch(request, group_id, switch_id):
        error = Error()
        err.description = "You do not have access to this switch"
        return error_page(request, group, switch, error)

    log = Log()
    log.user = request.user
    log.ip_address = get_remote_ip(request)
    log.switch = switch
    log.group = group
    log.description = "Reloading SNMP (basic)"
    log.action = LOG_RELOAD_SWITCH
    log.type = LOG_TYPE_VIEW
    log.save()

    clear_session_oid_cache(request)

    return switch_view(request, group_id, switch_id, view)


@login_required
def show_stats(request):
    """
    This shows various site statistics
    """

    template_name = 'admin_stats.html'

    # log my activity
    log = Log()
    log.user = request.user
    log.ip_address = get_remote_ip(request)
    log.type = LOG_TYPE_VIEW
    log.action = LOG_VIEW_ADMIN_STATS
    log.description = "Viewing Site Statistics"
    log.save()

    environment = {}    # OS environment information
    environment['Python'] = "%s.%s.%s" % (sys.version_info[0], sys.version_info[1], sys.version_info[2])
    uname = os.uname()
    environment['OS'] = "%s (%s)" % (uname.sysname, uname.release)
    environment['Django'] = django.get_version()
    import git
    try:
        repo = git.Repo(search_parent_directories=True)
        sha = repo.head.object.hexsha
        short_sha = repo.git.rev_parse(sha, short=8)
        branch = repo.active_branch
        commit_date = time.strftime("%a, %d %b %Y %H:%M UTC", time.gmtime(repo.head.object.committed_date))
        environment['Git version'] = "%s (%s)" % (branch, short_sha)
        environment['Git commit'] = commit_date
    except Exception:
        environment['Git version'] = 'Not found!'
    # Celery task processing information
    if settings.TASKS_ENABLED:
        celery_info = get_celery_info()
        if celery_info['stats'] is None:
            environment['Tasks'] = "Enabled, NOT running"
        else:
            environment['Tasks'] = "Enabled and running"
    else:
        environment['Tasks'] = "Disabled"
    environment['OpenL2M version'] = settings.VERSION

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

    # render the template
    return render(request, template_name, {
        'db_items': db_items,
        'usage': usage,
        'environment': environment,
    })


#
# "Administrative" views
#

@login_required
def admin_activity(request):
    """
    This shows recent activity
    """

    template_name = 'admin_activity.html'

    # what do we have rights to:
    if not request.user.is_superuser and not request.user.is_staff:
        # get them out of here!
        # log my activity
        log = Log()
        log.user = request.user
        log.ip_address = get_remote_ip(request)
        log.type = LOG_TYPE_ERROR
        log.action = LOG_VIEW_ALL_LOGS
        log.description = "Not Allowed to View All Logs"
        log.save()
        error = Error()
        error.status = True
        error.description = "You do not have access to this page!"
        return error_page(request, '', error)

    # log my activity
    log = Log()
    log.user = request.user
    log.ip_address = get_remote_ip(request)
    log.type = LOG_TYPE_VIEW
    log.action = LOG_VIEW_ALL_LOGS

    # look at query string, and filter as needed
    filter = {}
    if len(request.GET) > 0:
        # this contains a QueryString() object, a Django-defined class

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
        if(len(filter) > 0):
            logs = Log.objects.all().filter(**filter).order_by('-timestamp')[:50]
            log.description = "Viewing filtered logs: %s" % filter
        else:
            logs = Log.objects.all().order_by('-timestamp')[:50]
            log.description = "Viewing all logs"
    else:
        # if not, show most recent 50 activities
        logs = Log.objects.all().order_by('-timestamp')[:50]
        log.description = "Viewing all logs"

    log.save()

    # render the template
    return render(request, template_name, {
        'logs': logs,
        'filter': filter,
        'types': LOG_TYPE_CHOICES,
        'actions': LOG_ACTION_CHOICES,
        'switches': Switch.objects.all().order_by('name'),
        'switchgroups': SwitchGroup.objects.all().order_by('name'),
        'users': User.objects.all().order_by('username'),
    })


@login_required
def tasks(request):
    """
    This shows scheduled tasks for users
    """
    if not user_can_access_task(request, False):
        e = Error()
        e.description = "You cannot schedule tasks. If this is an error, please contact your administrator!"
        return error_page(request, False, False, e)

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

    # log my activity
    log = Log()
    log.user = request.user
    log.ip_address = get_remote_ip(request)
    log.type = LOG_TYPE_VIEW
    log.action = LOG_VIEW_TASKS
    log.description = "Viewing tasks"
    log.save()

    # return success_page(request, False, False, "Task page!")
    return render(request, template_name, {
        'tasks': tasks,
        'task_process_running': task_process_running,
    })


@login_required
def task_details(request, task_id):
    """
    This shows details of a scheduled task
    """
    template_name = 'task_details.html'

    task = get_object_or_404(Task, pk=task_id)

    if not user_can_access_task(request, task):
        # log my activity
        log = Log()
        log.user = request.user
        log.ip_address = get_remote_ip(request)
        log.type = LOG_TYPE_ERROR
        log.action = LOG_VIEW_TASK_DETAILS
        log.description = "You do not have permission to view task %d details!" % task_id
        log.save()
        error = Error()
        error.description = log.description
        return error_page(request, False, False, error)

    # log my activity
    log = Log()
    log.user = request.user
    log.ip_address = get_remote_ip(request)
    log.type = LOG_TYPE_VIEW
    log.action = LOG_VIEW_TASK_DETAILS
    log.description = "Viewing task %d details" % task_id
    log.save()

    task_process_running = is_celery_running()

    # render the template
    return render(request, template_name, {
        'task': task,
        'task_process_running': task_process_running,
    })


@login_required
def task_delete(request, task_id):
    """
    This deleted a scheduled task
    """
    task = get_object_or_404(Task, pk=task_id)

    if not user_can_access_task(request, task):
        log = Log()
        log.user = request.user
        log.ip_address = get_remote_ip(request)
        log.action = LOG_TASK_DELETE
        log.type = LOG_TYPE_ERROR
        log.description = "You do not have permission to delete task %d !" % task_id
        log.save()
        error = Error()
        error.description = log.description
        return error_page(request, False, False, error)

    if not is_celery_running():
        description = "The Task Process is NOT running, so we cannot delete this task at the moment!"
        return warning_page(request, False, False, description)

    # log my activity
    log = Log()
    log.user = request.user
    log.ip_address = get_remote_ip(request)
    log.action = LOG_TASK_DELETE
    if task_revoke(task, False):
        log.type = LOG_TYPE_CHANGE
        log.description = "Task %d deleted" % task_id
        log.save()
        return success_page(request, False, False, "Task %d has been deleted!" % task_id)
    else:
        log.description = "Error deleting task %d !" % task_id
        log.type = LOG_TYPE_ERROR
        log.save()
        error = Error()
        error.description = log.description
        return error_page(request, False, False, error)


@login_required
def task_terminate(request, task_id):
    """
    This terminates a hung (or running) task
    Only callable by admins or staff!
    """
    if not request.user.is_superuser and not request.user.is_staff:
        log = Log()
        log.user = request.user
        log.ip_address = get_remote_ip(request)
        log.action = LOG_TASK_TERMINATE
        log.type = LOG_TYPE_ERROR
        log.description = "You do not have permission to terminate task %d. Please contact an administrator!" % task_id
        log.save()
        error = Error()
        error.description = log.description
        return error_page(request, False, False, error)

    task = get_object_or_404(Task, pk=task_id)

    if not is_celery_running():
        description = "The Task Process is NOT running, so we cannot terminate this task at the moment!"
        return warning_page(request, False, False, description)

    # log my activity
    log = Log()
    log.user = request.user
    log.ip_address = get_remote_ip(request)
    log.action = LOG_TASK_TERMINATE
    if task_revoke(task, True):
        log.type = LOG_TYPE_CHANGE
        log.description = "Task %d terminated" % task_id
        log.save()
        return success_page(request, False, False, "Task %d has been terminated (killed)!" % task_id)
    else:
        log.type = LOG_TYPE_ERROR
        log.description = "Error terminating task %d" % task_id
        log.save()
        error = Error()
        error.description = log.description
        return error_page(request, False, False, error)


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
    if str(group_id) in permissions.keys():
        switches = permissions[str(group_id)]
        if str(switch_id) in switches.keys():
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
        if str(task.group.id) in permisssions.keys():
            #  if member of group there is no need to check switch!
            return True
    # deny others
    return False
