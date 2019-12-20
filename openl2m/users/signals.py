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
import re

from django.conf import settings
from django.dispatch import receiver
from django_auth_ldap.backend import populate_user, LDAPBackend

from switches.models import SwitchGroup, Log
from switches.constants import *


@receiver(populate_user, sender=LDAPBackend)
def ldap_auth_handler(user, ldap_user, **kwargs):
    """
    Django Signal handler that assigns user to SwitchGroup(s)

    This signal gets called after Django Auth LDAP Package has populated
    the user with its data, but before the user is saved to the database.
    """
    # Check all of the user's group names to see if they belong
    # in a group that match what we're looking for.
    for group_name in ldap_user.group_names:
        if settings.AUTH_LDAP_GROUP_TO_SWITCHGROUP_REGEX:

            match = re.match(settings.AUTH_LDAP_GROUP_TO_SWITCHGROUP_REGEX, group_name)
            if match is None:
                continue
            # get the switchgroup name:
            switchgroup_name = match.group(1).strip()
            # Since this signal is called BEFORE the user object is saved to the database,
            # we have to save it first so that we then can assign groups to it.
            user.save()
            # Add user to the SwitchGroup.
            try:
                group = SwitchGroup.objects.get(name=switchgroup_name)
                # existing SwitchGroup, try adding below
            except Exception:
                # new SwitchGroup() needed
                group = SwitchGroup()
                group.name = switchgroup_name
                try:
                    group.save()
                    log = Log()
                    log.user = user
                    log.action = LOG_LDAP_CREATE_GROUP
                    log.description = "Creating switchgroup '%s' from LDAP" % switchgroup_name
                    log.type = LOG_TYPE_LOGIN_OUT
                    log.save()
                except Exception:
                    # error creating new SwitchGroup()
                    log = Log()
                    log.user = user
                    log.action = LOG_LDAP_ERROR_CREATE_GROUP
                    log.description = "Error creating switchgroup '%s' from LDAP" % switchgroup_name
                    log.type = LOG_TYPE_ERROR
                    log.save()
                    continue
            # add user to this switchgroup
            try:
                group.users.add(user)
            except Exception:
                # how to handle this other then log message?
                log = Log()
                log.user = user
                log.action = LOG_LDAP_ERROR_USER_TO_GROUP
                log.description = "Error adding user to switchgroup '%s' from LDAP" % switchgroup_name
                log.type = LOG_TYPE_ERROR
                log.save()
