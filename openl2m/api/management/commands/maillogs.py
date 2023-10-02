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

# Custom command line commands, see also:
#    https://docs.djangoproject.com/en/4.2/howto/custom-management-commands/
#    https://simpleisbetterthancomplex.com/tutorial/2018/08/27/how-to-create-custom-django-management-commands.html
from datetime import timedelta
import tempfile
import xlsxwriter

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.utils import timezone

from switches.models import Log
from switches.constants import (
    LOG_TYPE_CHOICES,
    LOG_ACTION_CHOICES,
)

MY_TIMEFORMAT = "%x %X"

# the columns in the output spreadsheet, if requested:
COLUMN_TIME = 0
COLUMN_TYPE = 1
COLUMN_ACTION = 2
COLUMN_DEVICE = 3
COLUMN_USER = 4
COLUMN_IP = 5
COLUMN_DESCRIPTION = 6


class Command(BaseCommand):
    help = "E-mail OpenL2M logs"

    def add_arguments(self, parser):
        # Positional arguments - NONE

        # optional commands
        parser.add_argument(
            "--type",
            type=str,
            default="error",
            help='the type of log entries. Default is "error".',
        )

        parser.add_argument(
            "--hours",
            type=int,
            default=1,
            help="send the most recent number of hours of log entries. Default is 1 hour.",
        )

        parser.add_argument(
            "--to",
            type=str,
            default="",
            help="the email address to send the report to. (no default)",
        )

        parser.add_argument(
            "--ignore",
            type=str,
            default="",
            help="comma-separated list of integers representing log actions to ignore in the output. See switches/constants.py for the numerical LOG_ action numbers.",
        )

        parser.add_argument(
            "--subject",
            type=str,
            default="OpenL2M log report",
            help='the subject of the email. Default is "OpenL2M log report"',
        )

        parser.add_argument(
            "--attach",
            action="store_true",
            help="Create Excel spreadsheet as attachment.",
        )

        parser.add_argument(
            "--filename",
            type=str,
            default="openl2m_logs.xlsx",
            help='Log entries attachment filename. Default is "openl2m_logs.xlsx."',
        )

    def handle(self, *args, **options):
        # validate a few things...
        if not settings.EMAIL_HOST:
            self.stdout.write(
                "Error: settings.EMAIL_HOST is NOT set!", self.style.ERROR
            )
            return

        if not options["to"]:
            self.stdout.write("Error: 'to' argument needed!", self.style.ERROR)
            return

        # for email, "to" needs to be a list or tuple:
        to = options["to"].split(",")

        # prepare some convenience dictionaries:
        log_types = {}
        log_types_by_name = {}
        log_types_by_name["all"] = -1
        # add log types by name and key (number)
        for item in LOG_TYPE_CHOICES:
            # name => number
            log_types_by_name[item[1].lower()] = item[0]
            # number => name
            log_types[item[0]] = item[1]

        # index actions by key (number)
        log_actions = {}
        for item in LOG_ACTION_CHOICES:
            # number => description
            log_actions[item[0]] = item[1]

        # validate type choices
        type = options["type"].lower()
        if type not in log_types_by_name:
            self.stdout.write(
                f"Error: invalid log type '{type}', select from {log_types.keys()}"
            )
            return
        log_type = log_types_by_name[type]

        # create filter for Log() query:
        filter = {}
        if log_type != -1:  # -1 = 'all', the default of the objects.all() below!
            filter["type"] = log_type

        # do we ignore some log entry types?
        excludes = []
        if options["ignore"]:
            try:
                numbers = options["ignore"].split(",")
            except Exception:
                # ignore!
                self.stdout.write(
                    f"Error: invalid 'ignore' format: {options['ignore']}",
                    self.style.ERROR,
                )
                return
            # make sure they are all integers:
            for num in numbers:
                try:
                    n = int(num)
                except Exception:
                    self.stdout.write(
                        f"Error: ignore option '{num}' is NOT an integer!",
                        self.style.ERROR,
                    )
                    return
                if n in log_actions:
                    # all seems OK, add to filter!
                    excludes.append(n)
                    self.stdout.write(f"Ignoring action {n}: {log_actions[n]}")
                else:
                    self.stdout.write(f"ERROR: Invalid action number {n}")
                    return

        # calculate what the cut-off time is. Use local timezone.
        now = timezone.now().astimezone(tz=None)
        cutoff = now - timedelta(hours=options["hours"])
        cutoff_local = cutoff.astimezone(tz=None)

        if options["verbosity"] > 1:    # default = 1
            now_string = now.strftime(MY_TIMEFORMAT)
            cutoff_string = cutoff.strftime(MY_TIMEFORMAT)
            self.stdout.write(
                f"Now: {now_string}, Logs since: {cutoff_string}", self.style.SUCCESS
            )

        # looks like we are good to go!
        self.stdout.write(
            f"Sending most recent {options['hours']} hours of log entries for '{type}' to '{options['to']}'"
        )

        # get log since cut-off time
        filter["timestamp__gt"] = cutoff
        logs = (
            Log.objects.all()
            .exclude(action__in=excludes)
            .filter(**filter)
            .order_by("timestamp")
        )

        # go outout them!
        if logs:
            self.stdout.write(
                f"Emailing {logs.count()} log records... ", self.style.WARNING
            )
            self.stdout.flush()
            # need for-loop here!
            lines = []
            row = 0
            if options["attach"]:
                # open the Excel file:
                try:
                    tmp_file = f"{tempfile.gettempdir()}/{options['filename']}"
                    if options["verbosity"] > 1:
                        self.stdout.write(f"Attachment filename: {tmp_file}")
                    workbook = xlsxwriter.Workbook(tmp_file)
                    format_bold = workbook.add_format({'bold': True, 'font_name': 'Calibri', 'font_size': 14})
                    format_regular = workbook.add_format({'font_name': 'Calibri', 'font_size': 12})

                    worksheet = workbook.add_worksheet()

                    worksheet.write(row, COLUMN_TIME, "Time", format_bold)
                    worksheet.set_column(COLUMN_TIME, COLUMN_TIME, 25)      # Adjust the column width.

                    worksheet.write(row, COLUMN_TYPE, "Type", format_bold)
                    worksheet.set_column(COLUMN_TYPE, COLUMN_TYPE, 10)      # Adjust the column width.

                    worksheet.write(row, COLUMN_ACTION, "Action", format_bold)
                    worksheet.set_column(COLUMN_ACTION, COLUMN_ACTION, 15)      # Adjust the column width.

                    worksheet.write(row, COLUMN_DEVICE, "Device", format_bold)
                    worksheet.set_column(COLUMN_DEVICE, COLUMN_DEVICE, 25)      # Adjust the column width.

                    worksheet.write(row, COLUMN_USER, "User", format_bold)
                    worksheet.set_column(COLUMN_USER, COLUMN_USER, 15)      # Adjust the column width.

                    worksheet.write(row, COLUMN_IP, "IP", format_bold)
                    worksheet.set_column(COLUMN_IP, COLUMN_IP, 20)      # Adjust the column width.

                    worksheet.write(row, COLUMN_DESCRIPTION, "Description", format_bold)
                    worksheet.set_column(COLUMN_DESCRIPTION, COLUMN_DESCRIPTION, 150)      # Adjust the column width.

                    lines.append("Log entries are in the attached file!")
                except Exception as err:
                    self.stdout.write(
                        f"ERROR creating attachment at '{tmp_file}': {err}",
                        self.style.ERROR,
                    )
                    return

            for log in logs:
                row += 1
                entry = f"#{row}, {log.timestamp.strftime(MY_TIMEFORMAT)}, type '{log_types[log.type]}', action '{log_actions[log.action]}', client ip '{log.ip_address}', device '{log.switch}', description '{log.description}'"
                timestamp = log.timestamp.astimezone(tz=None)
                if options["attach"]:
                    worksheet.write(row, COLUMN_TIME, timestamp.strftime(MY_TIMEFORMAT), format_regular)
                    worksheet.write(row, COLUMN_TYPE, log_types[log.type], format_regular)
                    worksheet.write(row, COLUMN_ACTION, log_actions[log.action], format_regular)
                    worksheet.write(row, COLUMN_DEVICE, f"{log.switch}", format_regular)
                    worksheet.write(row, COLUMN_USER, f"{log.user}", format_regular)
                    worksheet.write(row, COLUMN_IP, log.ip_address, format_regular)
                    worksheet.write(row, COLUMN_DESCRIPTION, log.description, format_regular)
                else:
                    lines.append(entry)
                if options["verbosity"] > 1:
                    self.stdout.write(entry)

            if options["attach"]:
                try:
                    workbook.close()
                except Exception as err:
                    self.stdout.write(f"ERROR saving attachment file '{tmp_file}': {err}")
                    return

            # email it:
            try:
                message = EmailMessage(
                    subject=options["subject"],
                    body="\n".join(lines),
                    from_email=f"OpenL2M Log Mailer {settings.EMAIL_FROM_ADDRESS}",
                    to=to,
                )
                if options["attach"]:
                    message.attach_file(tmp_file)
                message.send()
            except Exception as err:
                self.stdout.write(f"ERROR emailing: {err}", self.style.ERROR)
        else:
            self.stdout.write("No log records found.")

        self.stdout.write("Finished.", self.style.SUCCESS)
