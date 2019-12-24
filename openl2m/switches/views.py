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
from datetime import date

import django
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.views.generic import View
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.html import mark_safe
from django.views.generic import View
from datetime import timedelta
from django.utils import timezone

from switches.models import *
from switches.constants import *
from switches.connect.connect import *
from switches.connect.constants import *
from switches.connect.snmp import *
from switches.connect.netmiko.netmiko import *
from switches.utils import *
from switches.tasks import bulkedit_job


@login_required
def switches(request):
    """
    This is the "home view", at "/"
    It shows the list of switches a user has access to
    """

    template_name = 'home.html'

    # back to the home screen, clear session cache
    # so we re-read switche as needed
    clear_session_oidcache(request)

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
    except Exception:
        log.type = LOG_TYPE_ERROR
        log.description = "SNMP ERROR: Viewing switch (%s)" % view
        log.save()
        error = Error()
        error.description = "Could not get SNMP object. Please contact your administrator to make sure switch data is correct in the database!"
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

    time_since_last_read = time_duration(time.time() - conn.basic_info_read_time)

    # finally, verify if this user can bulk-edit:
    if request.user.profile.bulk_edit and group.bulk_edit and switch.bulk_edit \
       and not group.read_only and not switch.read_only and not request.user.profile.read_only:
        bulk_edit = True
    else:
        bulk_edit = False

    return render(request, template_name, {
        'group': group,
        'switch': switch,
        'connection': conn,
        'logs': logs,
        'view': view,
        'cmd': cmd,
        'bulk_edit': bulk_edit,
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
    interface_list = request.POST.getlist('interfaces')

    # was anything submitted?
    if len(interface_list) == 0:
        return warning_page(request, group, switch, mark_safe("Please select at least 1 interface!"))

    if not interface_change and not poe_choice and new_pvid < 0 and not new_alias:
        return warning_page(request, group, switch, mark_safe("Please set at least 1 thing to change!"))

    # check if the new description/alias is allowed:
    if new_alias and settings.IFACE_ALIAS_NOT_ALLOW_REGEX:
        match = re.match(settings.IFACE_ALIAS_NOT_ALLOW_REGEX, new_alias)
        if match:
            log = Log()
            log.user = request.user
            log.ip_address = get_remote_ip(request)
            log.switch = switch
            log.group = group
            log.type = LOG_TYPE_ERROR
            log.action = LOG_CHANGE_BULK_EDIT
            log.description = "The description '%s' is not allowed!" % new_alias
            log.save()
            new_alias = ''

    # safety-check: is the new PVID is allowed:
    if new_pvid > 0:
        conn._set_allowed_vlans()
        if new_pvid not in conn.allowed_vlans.keys():
            log = Log()
            log.user = request.user
            log.ip_address = get_remote_ip(request)
            log.switch = switch
            log.group = group
            log.type = LOG_TYPE_ERROR
            log.action = LOG_CHANGE_BULK_EDIT
            log.description = "The new vlan '%d' is not allowed!" % new_pvid
            log.save()
            new_pvid = -1   # force no change!

    # now do the work, and log each change
    iface_count = 0
    success_count = 0
    error_count = 0
    outputs = []    # description of any errors found
    for if_index in interface_list:
        if_index = int(if_index)
        # OPTIMIZE: options.append("Interface index %s</br>" % if_index)
        iface = conn.get_interface_by_index(if_index)
        if not iface:
            error_count += 1
            outputs.append("ERROR: interface for index %s not found!" % if_index)
            continue
        iface_count += 1
        if interface_change:
            log = Log()
            log.user = request.user
            log.ip_address = get_remote_ip(request)
            log.if_index = if_index
            log.switch = switch
            log.group = group
            if iface.ifAdminStatus == IF_ADMIN_STATUS_UP:
                new_state = IF_ADMIN_STATUS_DOWN
                new_state_name = "Down"
                log.action = LOG_CHANGE_INTERFACE_DOWN
            else:
                new_state = IF_ADMIN_STATUS_UP
                new_state_name = "Up"
                log.action = LOG_CHANGE_INTERFACE_UP
            # make sure we cast the proper type here! Ie this needs an Integer()
            retval = conn._set(IF_ADMIN_STATUS + "." + str(if_index), new_state, 'i')
            if retval < 0:
                error_count += 1
                log.type = LOG_TYPE_ERROR
                log.description = "%s: Bulk-Edit Admin %s ERROR: %s" % \
                    (iface.name, new_state_name, conn.error.description)
            else:
                success_count += 1
                log.type = LOG_TYPE_CHANGE
                log.description = "%s: Bulk-Edit Admin set to %s" % \
                    (iface.name, new_state_name)
            outputs.append(log.description)
            log.save()

        if poe_choice != BULKEDIT_POE_NONE:
            if iface.poe_entry:
                log = Log()
                log.user = request.user
                log.ip_address = get_remote_ip(request)
                log.if_index = if_index
                log.switch = switch
                log.group = group
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
                    # make sure we cast the proper type here! Ie this needs an Integer()
                    retval = conn._set(POE_PORT_ADMINSTATUS + "." + iface.poe_entry.index, int(new_state), 'i')
                    if retval < 0:
                        error_count += 1
                        log.type = LOG_TYPE_ERROR
                        log.description = "%s: Bulk-Edit PoE %s ERROR: %s" % \
                            (iface.name, new_state_name, conn.error.description)
                    else:
                        success_count += 1
                        log.type = LOG_TYPE_CHANGE
                        log.description = "%s: Bulk-Edit PoE set to %s" % \
                            (iface.name, new_state_name)
                        outputs.append(log.description)
                        log.save()

                elif poe_choice == BULKEDIT_POE_DOWN_UP:
                    # Down / Up on interfaces with PoE Enabled:
                    if iface.poe_entry.admin_status == POE_PORT_ADMIN_ENABLED:
                        log.action = LOG_CHANGE_INTERFACE_POE_TOGGLE_DOWN_UP
                        # the PoE index is kept in the iface.poe_entry
                        # First disable PoE. Make sure we cast the proper type here! Ie this needs an Integer()
                        retval = conn._set("%s.%s" % (POE_PORT_ADMINSTATUS, iface.poe_entry.index), POE_PORT_ADMIN_DISABLED, 'i')
                        if retval < 0:
                            log.description = "ERROR: Bulk-Edit Toggle-Disable PoE on %s - %s " % (iface.name, conn.error.description)
                            log.type = LOG_TYPE_ERROR
                            log.save()
                            outputs.append(log.description)
                        else:
                            # successful power down, now delay
                            time.sleep(settings.POE_TOGGLE_DELAY)
                            # Now enable PoE again...
                            retval = conn._set("%s.%s" % (POE_PORT_ADMINSTATUS, iface.poe_entry.index), POE_PORT_ADMIN_ENABLED, 'i')
                            if retval < 0:
                                log.description = "ERROR: Bulk-Edit Toggle-Enable PoE on %s - %s " % (iface.name, conn.error.description)
                                log.type = LOG_TYPE_ERROR
                                outputs.append(log.description)
                                log.save()
                            else:
                                # all went well!
                                success_count += 1
                                log.type = LOG_TYPE_CHANGE
                                log.description = "%s: Bulk-Edit PoE Toggle Down/Up OK" % iface.name
                                outputs.append(log.description)
                                log.save()
                    else:
                        outputs.append("%s: Bulk-Edit PoE IGNORED, Poe NOT enabled" % iface.name)

            else:
                outputs.append("%s: not PoE capable - ignored!" % iface.name)

        if new_pvid > 0:
            # make sure we cast the proper type here! Ie this needs an Integer()
            retval = conn.set_interface_untagged_vlan(if_index, iface.untagged_vlan, new_pvid)
            log = Log()
            log.user = request.user
            log.ip_address = get_remote_ip(request)
            log.if_index = if_index
            log.switch = switch
            log.group = group
            log.action = LOG_CHANGE_INTERFACE_PVID
            if retval < 0:
                error_count += 1
                log.type = LOG_TYPE_ERROR
                log.description = "%s: Bulk-Edit Vlan change ERROR: %s" % \
                    (iface.name, conn.error.description)
            else:
                success_count += 1
                log.type = LOG_TYPE_ERROR
                log.description = "%s: Bulk-Edit Vlan set to %s" % (iface.name, new_pvid)
            outputs.append(log.description)
            log.save()

        if new_alias:
            iface_new_alias = new_alias
            # check if the original alias starts with a string we have to keep
            if settings.IFACE_ALIAS_KEEP_BEGINNING_REGEX:
                keep_format = "(^%s)" % settings.IFACE_ALIAS_KEEP_BEGINNING_REGEX
                match = re.match(keep_format, iface.ifAlias)
                if match:
                    # check of new submitted alias begins with this string:
                    match_new = re.match(keep_format, iface_new_alias)
                    if not match_new:
                        # required start string NOT found on new alias, so prepend it!
                        iface_new_alias = "%s %s" % (match[1], iface_new_alias)
                        outputs.append("%s: Bulk-Edit Description override: %s" % (iface.name, iface_new_alias))

            log = Log()
            log.user = request.user
            log.ip_address = get_remote_ip(request)
            log.if_index = if_index
            log.switch = switch
            log.group = group
            log.action = LOG_CHANGE_INTERFACE_ALIAS
            # make sure we cast the proper type here! Ie this needs an string
            retval = conn._set(IFMIB_ALIAS + "." + str(if_index), iface_new_alias, 'OCTETSTRING')
            if retval < 0:
                error_count += 1
                log.type = LOG_TYPE_ERROR
                log.description = "%s: Bulk-Edit Descr ERROR: %s" % \
                    (iface.name, conn.error.description)
                log.save()
                return error_page(request, group, switch, conn.error)
            else:
                success_count += 1
                log.type = LOG_TYPE_ERROR
                log.description = "%s: Bulk-Edit Descr set OK" % iface.name
            outputs.append(log.description)
            log.save()

    # log final results
    log = Log()
    log.user = request.user
    log.ip_address = get_remote_ip(request)
    log.switch = switch
    log.group = group
    log.type = LOG_TYPE_CHANGE
    log.action = LOG_CHANGE_BULK_EDIT
    if error_count > 0:
        log.type = LOG_TYPE_ERROR
        log.description = "Bulk Edits had errors! (see previous entries)"
    else:
        log.description = "Bulk Edits OK!"
    log.save()

    # indicate we need to save config!
    if success_count > 0:
        conn.set_save_needed(True)

    # now build the results page from the outputs
    description = "%s\n%s\n" % ("\n<div><strong>Results:</strong></div>",
                                "\n</br>".join(outputs))
    if error_count > 0:
        err = Error()
        err.description = "Bulk-Edit errors"
        err.details = description
        return error_page(request, group, switch, err)
    else:
        return success_page(request, group, switch, mark_safe(description))

@login_required
def switch_bulkedit_job(request, group_id, switch_id):
    """
    Handle the submission of the Bulk-Edit job, ie bulk changes at some time in the future.
    """
    group = get_object_or_404(SwitchGroup, pk=group_id)
    switch = get_object_or_404(Switch, pk=switch_id)

    if not rights_to_group_and_switch(request, group_id, switch_id):
        error = Error()
        error.description = "You do not have access to this switch"
        return error_page(request, group, switch, error)

    conn = get_connection_object(request, group, switch)

    bulkedit_job.apply_async(countdown=5, kwargs={'user_id': request.user.id, 'http_post': request.POST})

    description = "New Bulk-Edit job was submitted!"

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

    if iface.ifAlias == new_alias:
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
        match = re.match(keep_format, iface.ifAlias)
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

    if conn.is_save_needed() and conn.can_save_config():
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

    clear_session_oidcache(request)

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
        environment['Git version'] = repo
        sha = repo.head.object.hexsha
        short_sha = repo.git.rev_parse(sha, short=8)
        branch = repo.active_branch
        environment['Git version'] = "%s (%s)" % (branch, short_sha)
    except Exception:
        environment['Git version'] = 'Not found!'
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
    filter['timestamp__date'] = date.today()
    usage['Changes today'] = Log.objects.filter(**filter).count()

    filter = {}
    filter['type'] = int(LOG_TYPE_CHANGE)
    filter['timestamp__gte'] = timezone.now().date() - timedelta(days=7)
    usage['Changes last 7 days'] = Log.objects.filter(**filter).count()

    filter = {}
    filter['type'] = int(LOG_TYPE_CHANGE)
    filter['timestamp__gte'] = timezone.now().date() - timedelta(days=31)
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
