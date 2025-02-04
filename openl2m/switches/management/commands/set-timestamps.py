'''Script to update Switch().created, last_changed and last_access time stamps,
and access_count and change_count counters.
This should only be run ONCE, and only if you have a version of OpenL2M that
preceedes v3.2
'''

# admin LogEntry() model is here:
# https://github.com/django/django/blob/main/django/contrib/admin/models.py

from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone

from switches.constants import (
    LOG_TYPE_VIEW,
    LOG_TYPE_CHANGE,
    LOG_TYPE_COMMAND,
    LOG_VIEW_SWITCH,
    LOG_SAVE_SWITCH,
    LOG_CHANGE_BULK_EDIT,
    LOG_BULK_EDIT_TASK_SUBMIT,
    LOG_BULK_EDIT_TASK_START,
    LOG_EXECUTE_COMMAND,
)
from switches.models import Log, Switch


class Command(BaseCommand):
    help = """One-time update of switch timestamps and use counts from logs. ONLY RUN THIS ONCE!
    To be used if migrating from pre-v3.2 to v3.2 or newer. Assumes you have log entries available.
    """

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--YES",
            action="store_true",
            help="REQUIRED option to make sure you want to do this!",
        )

    def handle(self, *args, **options):
        # Remove log entries older then configured value...
        if not options["YES"]:
            self.stdout.write("REQUIRED argument YES not found, aborting...")
            return

        self.stdout.write("One-time update switch timestamps and use counts:")

        #
        # run admin logs for switch() object create time.
        #
        starttime = timezone.now()
        self.stdout.write("Checking Admin Logs Switch() creation:")
        admin_logs = LogEntry.objects.all()  # or you can filter, etc.
        # looking for Switch() in "switches" app
        switch_content_type = ContentType.objects.get(app_label="switches", model="switch")
        create_found = 0
        create_added = 0
        log_count_used = 0
        for log in admin_logs:
            if log.is_addition():
                # self.stdout.write(f"{log.action_flag} - {log.action_time} - {log.content_type} - {log.object_id} - {log.object_repr}")
                if log.content_type == switch_content_type:
                    log_count_used += 1
                    self.stdout.write(f"Found: switch id {log.object_id} = {log.object_repr}")
                    create_found += 1
                    # get the switch:
                    try:
                        switch = Switch.objects.get(pk=log.object_id)
                        switch.created = log.action_time
                        switch.save()
                        self.stdout.write("  Creation timestamp set!")
                        create_added += 1
                    except Exception as err:
                        self.stdout.write(f"ERROR getting switch: {err}")

        #
        # now find access and change OpenL2M log entries:
        #
        self.stdout.write("==============================")
        self.stdout.write("Checking OpenL2M Logs entries:")

        # look at all log, from recent to oldest
        # to minimize database writes.
        logs = Log.objects.all().order_by("-timestamp")
        access_found = 0
        access_added = 0
        change_found = 0
        change_added = 0
        command_found = 0
        command_added = 0
        # the type of logs we need to look at:
        wanted_types = (LOG_TYPE_VIEW, LOG_TYPE_CHANGE, LOG_TYPE_COMMAND)
        change_action_ignore = (
            LOG_SAVE_SWITCH,
            LOG_CHANGE_BULK_EDIT,
            LOG_BULK_EDIT_TASK_SUBMIT,
            LOG_BULK_EDIT_TASK_START,
        )
        for log in logs:
            if log.type not in wanted_types:
                continue

            if log.type == LOG_TYPE_VIEW and log.action == LOG_VIEW_SWITCH:
                # this is accessing a device:
                access_found += 1
                try:
                    # this should set the most recent access time just once
                    if log.timestamp > log.switch.last_accessed:
                        log.switch.last_accessed = log.timestamp
                        self.stdout.write(f"  Access timestamp set on '{log.switch.name}': {log.timestamp}")
                    log.switch.access_count += 1
                    log.switch.save()
                    access_added += 1
                except Exception as err:
                    self.stdout.write(f"ERROR setting switch access: {err}")
                    self.stdout.write(f"  Log entry: {log.as_string()}")

            if log.type == LOG_TYPE_CHANGE and log.switch:
                # changing a device, ignore config save, and bulkedit entries
                # we count the individual changes
                if log.action in change_action_ignore:
                    continue
                change_found += 1
                try:
                    # this should set the most recent changed time just once
                    if log.timestamp > log.switch.last_changed:
                        # update stats
                        log.switch.last_changed = log.timestamp
                        self.stdout.write(f"  Change timestamp set on '{log.switch.name}': {log.timestamp}")
                    log.switch.change_count += 1
                    log.switch.save()
                    change_added += 1
                except Exception as err:
                    self.stdout.write(f"ERROR setting switch change: {err}")
                    self.stdout.write(f"  Log entry: {log.as_string()}")

            if log.type == LOG_TYPE_COMMAND and log.action == LOG_EXECUTE_COMMAND:
                command_found += 1
                try:
                    # this should set the most recent access time just once
                    if log.timestamp > log.switch.last_command_time:
                        # update stats
                        log.switch.last_command_time = log.timestamp
                        self.stdout.write(f"  Command timestamp set on '{log.switch.name}': {log.timestamp}")
                    log.switch.command_count += 1
                    log.switch.save()
                    command_added += 1
                except Exception as err:
                    self.stdout.write(f"ERROR setting switch command: {err}")
                    self.stdout.write(f"  Log entry: {log.as_string()}")

        # print some stats about what we imported...
        self.stdout.write(
            f"Found {create_found} creation entries, added to {create_added} switches.", self.style.SUCCESS
        )
        self.stdout.write(f"Found {access_found} access entries, {access_added} added to switches.", self.style.SUCCESS)
        self.stdout.write(f"Found {change_found} change entries, {change_added} added to switches.", self.style.SUCCESS)
        self.stdout.write(
            f"Found {command_found} command entries, {command_added} added to switches.", self.style.SUCCESS
        )
        duration = timezone.now() - starttime
        self.stdout.write(f"This took {duration}")
        self.stdout.write("Finished.", self.style.SUCCESS)
