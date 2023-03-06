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
#    https://docs.djangoproject.com/en/2.2/howto/custom-management-commands/
#    https://simpleisbetterthancomplex.com/tutorial/2018/08/27/how-to-create-custom-django-management-commands.html

#
# add the command 'removelogs' to remove Log() entries older then settings.LOG_MAX_AGE days.
# this is heavily inspired by the Netbox housekeeping code in
# /netbox/extras/management/commands/housekeeping.py
#

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import DEFAULT_DB_ALIAS

from switches.models import Log


class Command(BaseCommand):
    help = "Remove log entries older then configured number of days."

    def handle(self, *args, **options):

        # Remove log entries older then configured value...
        self.stdout.write("Checking for old log entries to remove:")
        if settings.LOG_MAX_AGE:
            cutoff = timezone.now() - timedelta(days=settings.LOG_MAX_AGE)
            if options['verbosity'] > 1:
                self.stdout.write(f"\tRetention period: {settings.LOG_MAX_AGE} days")
                self.stdout.write(f"\tCut-off time: {cutoff}")
            expired_records = Log.objects.filter(timestamp__lt=cutoff).count()
            if expired_records:
                self.stdout.write(f"\tDeleting {expired_records} expired log records... ", self.style.WARNING, ending="")
                self.stdout.flush()
                try:
                    Log.objects.filter(timestamp__lt=cutoff)._raw_delete(using=DEFAULT_DB_ALIAS)
                except Exception:
                    self.stderr.write("Error deleting log entries!")
                self.stdout.write("Done!", self.style.WARNING)
            else:
                self.stdout.write("\tNo expired log records found.")
        else:
            self.stdout.write(
                f"\tNo-Op: No log maximum age set! (LOG_MAX_AGE = {settings.LOG_MAX_AGE})"
            )

        self.stdout.write("Finished.", self.style.SUCCESS)
