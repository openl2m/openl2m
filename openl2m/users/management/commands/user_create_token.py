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
# this allow a REST API token to created from CLI management command.
#
import sys

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from switches.constants import LOG_TYPE_CHANGE, LOG_REST_API_TOKEN_CREATED
from switches.models import Log
from users.models import Token


class Command(BaseCommand):
    help = 'Create REST token for a user.'

    def add_arguments(self, parser):
        # Positional arguments - username
        parser.add_argument('username', type=str, help='the OpenL2M user')

        # optional commands - TBD
        # parser.add_argument('--expires', type=str, help='the expiration date/time of this token')

        # parser.add_argument('--write_enabled', type=str, help='the Switch CSV file to import')

        # parser.add_argument('--allowed_ips', type=str, help='the Netmiko Profile CSV file to import')

        # parser.add_argument('--description', type=str, help='the SNMP Profile CSV file to import')

    def handle(self, *args, **options):
        username = options['username']
        # expires = options['expires']
        # write_enabled = options['write_enabled']
        # allowed_ips = options['allowed_ips']
        # description = options['descriptions']

        # self.stdout.write(self.style.ERROR("'name' field is required!"))
        # self.stdout.write(self.style.WARNING(f"Command '{row['name']}' already exists, but update NOT allowed!")
        try:
            user = User.objects.get(username=username)
        except Exception:
            self.stdout.write(self.style.ERROR(f"Error: user '{username}' not found!"))
            return
        # get a new token:
        t = Token()
        t.user = user
        t.key = Token.generate_key()
        self.stdout.write(self.style.SUCCESS(f"New token for '{username}': {t.key}"))
        t.save()
        # log this!
        log = Log(
            user=user,
            # ip_address=None,
            # switch=None,
            # # group=False,
            action=LOG_REST_API_TOKEN_CREATED,
            type=LOG_TYPE_CHANGE,
            description=f"REST API token created from CLI",
        )
        log.save()
