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
from django.utils.timezone import now
import re

from django.conf import settings

from switches.utils import dprint

# are we actually using LDAP
if settings.LDAP_CONFIG is not None:
    from django.dispatch import receiver
    from django_auth_ldap.backend import populate_user, LDAPBackend

    from switches.models import SwitchGroup, Log
    import switches.constants as constants

    @receiver(populate_user, sender=LDAPBackend)
    def ldap_auth_handler(user, ldap_user, **kwargs):
        """
        Django Signal handler that assigns user to SwitchGroup(s)

        This signal gets called after Django Auth LDAP Package has populated
        the user with its data, but before the user is saved to the database.
        """
        # Since this signal is called BEFORE the user object is saved to the database,
        # we have to save it first so that we then can assign groups to it.
        user.save()
        # Log the ldap path used to authenticate this user
        log = Log(
            user=user,
            action=constants.LOG_LOGIN_LDAP,
            description=f"LDAP authenticated from '{ldap_user.dn}'",
            type=constants.LOG_TYPE_LOGIN_OUT,
        )
        log.save()

        # update the user profile with the timestamp and ldap dn of the login.
        user.profile.last_ldap_login = now()
        # this field is set to max_length=1024 in models.py
        user.profile.last_ldap_dn = ldap_user.dn[:1024]
        user.profile.save()

        # Check all of the user's group names to see if they belong
        # in a group that match what we're looking for.
        for group_name in ldap_user.group_names:
            if settings.AUTH_LDAP_GROUP_TO_SWITCHGROUP_REGEX:
                match = re.match(settings.AUTH_LDAP_GROUP_TO_SWITCHGROUP_REGEX, group_name)
                if match is None:
                    continue
                # get the switchgroup name:
                switchgroup_name = match.group(1).strip()
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
                        log = Log(
                            user=user,
                            action=constants.LOG_LDAP_CREATE_GROUP,
                            description=f"Creating switchgroup '{switchgroup_name}' from LDAP",
                            type=constants.LOG_TYPE_LOGIN_OUT,
                        )
                        log.save()
                    except Exception:
                        # error creating new SwitchGroup()
                        log = Log(
                            user=user,
                            action=constants.LOG_LDAP_ERROR_CREATE_GROUP,
                            description=f"Error creating switchgroup '{switchgroup_name}' from LDAP",
                            type=constants.LOG_TYPE_ERROR,
                        )
                        log.save()
                        continue
                # see if user is already in this group
                # Note: this returns a QuerySet(), which will be empty if not a member!
                member = group.users.filter(id=user.id)
                if len(member) > 0:
                    dprint(f"LDAP: Already member of '{switchgroup_name}'")
                else:
                    dprint(f"LDAP: Not yet member of '{switchgroup_name}'")
                    # try to add:
                    try:
                        group.users.add(user)
                        # log this group add
                        log = Log(
                            user=user,
                            action=constants.LOG_LDAP_ADD_USER_TO_GROUP,
                            description=f"Adding user {user.username} to switchgroup '{switchgroup_name}' from LDAP",
                            type=constants.LOG_TYPE_CHANGE,
                        )
                        log.save()
                        dprint(f"LDAP: User {user.username} added to switchgroup '{switchgroup_name}'")
                    except Exception:
                        # how to handle this other then log message?
                        log = Log(
                            user=user,
                            action=constants.LOG_LDAP_ERROR_USER_TO_GROUP,
                            description=f"Error adding user to switchgroup '{switchgroup_name}' from LDAP",
                            type=constants.LOG_TYPE_ERROR,
                        )
                        log.save()
                        dprint(f"LDAP: ERROR adding user to switchgroup '{switchgroup_name}'")
