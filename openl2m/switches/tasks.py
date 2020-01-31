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

# Create your Celery scheduled tasks here
from __future__ import absolute_import, unicode_literals

import json
import traceback

from django.conf import settings
from django.core.mail import send_mail, mail_admins
from django.contrib.auth.models import User
from django.utils import timezone
from celery import shared_task

from switches.models import Switch, SwitchGroup, Log, Task
from switches.constants import *
from switches.connect.connect import get_connection_object
from switches.connect.snmp import *
from switches.utils import dprint


@shared_task
def bulkedit_task(task_id, user_id, group_id, switch_id,
                  interface_change, poe_choice, new_pvid,
                  new_alias, interfaces, save_config):

    log = Log()
    log.ip_address = "0.0.0.0"
    log.action = LOG_BULK_EDIT_TASK_END_ERROR
    log.type = LOG_TYPE_ERROR
    try:
        task = Task.objects.get(pk=int(task_id))
    except Exception as e:
        log.description = "Bulk-Edit task started with invalid task id %d" \
            % int(task_id)
        log.save()
        return
    try:
        user = User.objects.get(pk=int(user_id))
    except Exception as e:
        log.description = "Bulk-Edit task(id=%d) started with invalid user id (%d)" \
            % (task_id, int(user_id))
        log.save()
        return
    try:
        group = SwitchGroup.objects.get(pk=int(group_id))
    except Exception as e:
        log.description = "Bulk-Edit task(id=%d) started with invalid group id (%d)" \
            % (task_id, int(group_id))
        log.save()
        return
    try:
        switch = Switch.objects.get(pk=int(switch_id))
    except Exception as e:
        log.description = "Bulk-Edit task(id=%d) started with invalid switch id (%d)" \
            % (task_id, int(switch_id))
        log.save()
        return

    # log the start of the job
    log.user = user
    log.group = group
    log.switch = switch
    log.type = LOG_TYPE_CHANGE
    log.action = LOG_BULK_EDIT_TASK_START
    log.description = "Bulk-Edit task(id=%d) started" % int(task_id)
    log.save()

    task.status = TASK_STATUS_RUNNING
    task.start_count += 1
    task.started = timezone.now()   # use Django time with support of timezone!
    task.save()

    args = json.loads(task.arguments)

    # now go process
    settings.IN_CELERY_PROCESS = True
    results = bulkedit_processor(False, user_id, group_id, switch_id,
                                 interface_change, poe_choice, new_pvid,
                                 new_alias, interfaces, save_config, task)

    task.completed = timezone.now()   # use Django time with support of timezone!
    task.results = json.dumps(results)

    log = Log()
    log.user = user
    log.group = group
    log.switch = switch
    subject = ''
    if results['error_count'] == 0:
        # log the successful end of the job
        task.status = TASK_STATUS_COMPLETED
        task.save()
        log.action = LOG_BULK_EDIT_TASK_END_OK
        log.description = "Bulk-Edit task(id=%d) ended successfully" % task_id
        log.type = LOG_TYPE_CHANGE
        log.save()
        subject = "Task executed successfully!"
    else:
        # log the error
        task.status = TASK_STATUS_ERROR
        task.save()
        log.action = LOG_BULK_EDIT_TASK_END_ERROR
        log.description = "Bulk-Edit task(%d) ended with errors" % task_id
        log.type = LOG_TYPE_ERROR
        log.save()
        subject = "Task had errors!"

    # now email the results to the user:
    if user.email:
        message = "Task Description: %s\nId: %d\nScheduled: %s\nCompleted: %s\n\nResults:\n\n%s\n" % \
            (task.description, task.id, task.eta, task.completed,
             "\n".join(results['outputs']))

        log = Log()
        log.user = user
        log.group = group
        log.switch = switch
        try:
            send_mail("%s%s" % (subject, settings.EMAIL_SUBJECT_PREFIX),
                      message, settings.EMAIL_FROM_ADDRESS,
                      [user.email], fail_silently=False)
            log.type = LOG_TYPE_CHANGE
            log.action = LOG_EMAIL_SENT
            log.description = "Bulk-Edit task(id=%d) results email sent" % task_id
            if settings.TASKS_BCC_ADMINS:
                try:
                    mail_admins(subject, message, fail_silently=False)
                except Exception as e:
                    log = Log()
                    log.user = user
                    log.group = group
                    log.switch = switch
                    log.type = LOG_TYPE_ERROR
                    log.action = LOG_EMAIL_ERROR
                    log.description = "Error emailing admin results for task(id=%d) (%s)" % (task_id, repr(e))
                    log.save()
        except Exception as e:
            log.type = LOG_TYPE_ERROR
            log.action = LOG_EMAIL_ERROR
            log.description = "Error emailing Bulk-Edit task(id=%d) results (%s)" % (task_id, repr(e))
        log.save()

    return 0


def bulkedit_processor(request, user_id, group_id, switch_id,
                       interface_change, poe_choice, new_pvid,
                       new_alias, interfaces, save_config, task=False):
    """
    Function to handle the bulk edit processing, from form-submission or scheduled job.
    This will Log() each individual action per interface.
    Returns the number of successful action, number of error actions, and
    a list of outputs with text information about each action.
    """
    try:
        user = User.objects.get(pk=user_id)
        group = SwitchGroup.objects.get(pk=group_id)
        switch = Switch.objects.get(pk=switch_id)
    except Exception as e:
        log = Log()
        log.ip_address = "0.0.0.0"
        log.action = LOG_BULK_EDIT_TASK_END_ERROR
        log.description = "bulkedit_processor() started with invalid user(%d), \
                           group(%d) or switch(%d)" \
                           % (int(user_id), int(group_id), int(switch_id))
        log.type = LOG_TYPE_ERROR
        log.save()

        results = {}
        results['success_count'] = 0
        results['error_count'] = 1
        outputs = []
        outputs.append("FATAL Error getting object for User, Group, or Switch!")
        results['outputs'] = outputs
        return results

    if request:
        remote_ip = get_remote_ip(request)
    else:
        remote_ip = "0.0.0.0"

    # this needs work:
    conn = get_connection_object(request, group, switch)
    if not request:
        # running asynchronously (as task), we need to read the device
        # to get access to interfaces.
        conn.get_switch_basic_info()

    # now do the work, and log each change
    runtime_undo_info = {}
    iface_count = 0
    success_count = 0
    error_count = 0
    outputs = []    # description of any errors found
    for (if_index, name) in interfaces.items():
        if_index = int(if_index)
        # OPTIMIZE: options.append("Interface index %s</br>" % if_index)
        iface = conn.get_interface_by_index(if_index)
        if not iface:
            error_count += 1
            outputs.append("ERROR: interface for index %s not found!" % if_index)
            continue
        iface_count += 1
        current_state = {}  # save the current state, right before we make a change!
        current_state['if_index'] = if_index
        current_state['name'] = iface.name    # for readability
        if interface_change:
            log = Log()
            log.user = user
            log.ip_address = remote_ip
            log.if_index = if_index
            log.switch = switch
            log.group = group
            current_state['admin_state'] = iface.admin_status
            if iface.admin_status == IF_ADMIN_STATUS_UP:
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
                log.description = "Interface %s: Bulk-Edit Admin %s ERROR: %s" % \
                    (iface.name, new_state_name, conn.error.description)
            else:
                success_count += 1
                log.type = LOG_TYPE_CHANGE
                log.description = "Interface %s: Bulk-Edit Admin set to %s" % \
                    (iface.name, new_state_name)
            outputs.append(log.description)
            log.save()

        if poe_choice != BULKEDIT_POE_NONE:
            if iface.poe_entry:
                log = Log()
                log.user = user
                log.ip_address = remote_ip
                log.if_index = if_index
                log.switch = switch
                log.group = group
                current_state['poe_state'] = iface.poe_entry.admin_status
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
                        log.description = "Interface %s: Bulk-Edit PoE %s ERROR: %s" % \
                            (iface.name, new_state_name, conn.error.description)
                    else:
                        success_count += 1
                        log.type = LOG_TYPE_CHANGE
                        log.description = "Interface %s: Bulk-Edit PoE set to %s" % \
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
                            log.description = "ERROR: Bulk-Edit Toggle-Disable PoE on interface %s - %s " % (iface.name, conn.error.description)
                            log.type = LOG_TYPE_ERROR
                            log.save()
                            outputs.append(log.description)
                        else:
                            # successful power down, now delay
                            time.sleep(settings.POE_TOGGLE_DELAY)
                            # Now enable PoE again...
                            retval = conn._set("%s.%s" % (POE_PORT_ADMINSTATUS, iface.poe_entry.index), POE_PORT_ADMIN_ENABLED, 'i')
                            if retval < 0:
                                log.description = "ERROR: Bulk-Edit Toggle-Enable PoE on interface %s - %s " % (iface.name, conn.error.description)
                                log.type = LOG_TYPE_ERROR
                                outputs.append(log.description)
                                log.save()
                            else:
                                # all went well!
                                success_count += 1
                                log.type = LOG_TYPE_CHANGE
                                log.description = "Interface %s: Bulk-Edit PoE Toggle Down/Up OK" % iface.name
                                outputs.append(log.description)
                                log.save()
                    else:
                        outputs.append("Interface %s: Bulk-Edit PoE IGNORED, Poe NOT enabled" % iface.name)

            else:
                outputs.append("Interface %s: not PoE capable - ignored!" % iface.name)

        if new_pvid > 0:
            if iface.lacp_master_index > 0:
                # LACP member interface, we cannot edit the vlan!
                log = Log()
                log.user = user
                log.ip_address = remote_ip
                log.if_index = if_index
                log.switch = switch
                log.group = group
                log.type = LOG_TYPE_WARNING
                log.action = LOG_CHANGE_INTERFACE_PVID
                log.description = "Interface %s: LACP Member, Bulk-Edit Vlan set to %s IGNORED!" % (iface.name, new_pvid)
                outputs.append(log.description)
                log.save()
            else:
                # make sure we cast the proper type here! Ie this needs an Integer()
                current_state['pvid'] = iface.untagged_vlan
                retval = conn.set_interface_untagged_vlan(if_index, iface.untagged_vlan, new_pvid)
                log = Log()
                log.user = user
                log.ip_address = remote_ip
                log.if_index = if_index
                log.switch = switch
                log.group = group
                log.action = LOG_CHANGE_INTERFACE_PVID
                if retval < 0:
                    error_count += 1
                    log.type = LOG_TYPE_ERROR
                    log.description = "Interface %s: Bulk-Edit Vlan change ERROR: %s" % \
                        (iface.name, conn.error.description)
                else:
                    success_count += 1
                    log.type = LOG_TYPE_CHANGE
                    log.description = "Interface %s: Bulk-Edit Vlan set to %s" % (iface.name, new_pvid)
                outputs.append(log.description)
                log.save()

        if new_alias:
            iface_new_alias = new_alias
            # check if the original alias starts with a string we have to keep
            if settings.IFACE_ALIAS_KEEP_BEGINNING_REGEX:
                keep_format = "(^%s)" % settings.IFACE_ALIAS_KEEP_BEGINNING_REGEX
                match = re.match(keep_format, iface.alias)
                if match:
                    # check of new submitted alias begins with this string:
                    match_new = re.match(keep_format, iface_new_alias)
                    if not match_new:
                        # required start string NOT found on new alias, so prepend it!
                        iface_new_alias = "%s %s" % (match[1], iface_new_alias)
                        outputs.append("Interface %s: Bulk-Edit Description override: %s" % (iface.name, iface_new_alias))

            log = Log()
            log.user = user
            log.ip_address = remote_ip
            log.if_index = if_index
            log.switch = switch
            log.group = group
            log.action = LOG_CHANGE_INTERFACE_ALIAS
            current_state['description'] = iface.alias
            # make sure we cast the proper type here! Ie this needs an string
            retval = conn._set(IFMIB_ALIAS + "." + str(if_index), iface_new_alias, 'OCTETSTRING')
            if retval < 0:
                error_count += 1
                log.type = LOG_TYPE_ERROR
                log.description = "Interface %s: Bulk-Edit Descr ERROR: %s" % \
                    (iface.name, conn.error.description)
                log.save()
                return error_page(request, group, switch, conn.error)
            else:
                success_count += 1
                log.type = LOG_TYPE_CHANGE
                log.description = "Interface %s: Bulk-Edit Descr set OK" % iface.name
            outputs.append(log.description)
            log.save()

        # done with this interface, add pre-change state!
        runtime_undo_info[if_index] = current_state

    # update the task with the pre-change state:
    if task:
        task.runtime_reverse_arguments = json.dumps(runtime_undo_info)
        task.save()

    # do we need to save the config?
    if save_config and error_count == 0 and conn.can_save_config():
        log = Log()
        log.user = user
        log.ip_address = remote_ip
        log.switch = switch
        log.group = group
        log.action = LOG_SAVE_SWITCH
        retval = conn.save_running_config()  # we are not checking errors here!
        if retval < 0:
            # an error happened!
            log.type = LOG_TYPE_ERROR
            log.description = "Bulk-Edit Error Saving Config"
        else:
            # save OK!
            log.type = LOG_TYPE_CHANGE
            log.description = "Bulk-Edit Config Saved"
        log.save()

    # log final results
    log = Log()
    log.user = user
    log.ip_address = remote_ip
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

    results = {}
    results['success_count'] = success_count
    results['error_count'] = error_count
    results['outputs'] = outputs
    return results
