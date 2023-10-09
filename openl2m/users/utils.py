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
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone

from switches.utils import get_ip_dns_name


def user_can_bulkedit(user, group, switch):
    """
    Verify if this user can bulk-edit.
    Return True is so, False if not.
    """
    if (
        user.profile.bulk_edit
        and group.bulk_edit
        and switch.bulk_edit
        and not group.read_only
        and not switch.read_only
        and not user.profile.read_only
    ):
        return True
    return False


def user_can_edit_vlans(user, group, switch):
    """
    Verify if this user can edit vlans on a device.
    Return True is so, False if not.
    """
    if user.profile.read_only or group.read_only or switch.read_only:
        return False
    if user.is_superuser or user.profile.vlan_edit:
        return True
    return False


def get_current_users():
    """
    Get the list of current users with a session that has not expired.
    This "approximates" the currently active users.
    Note this only works if SESSION_EXPIRE_AT_BROWSER_CLOSE = True !
    """
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    user_list = []
    for session in active_sessions:
        data = session.get_decoded()
        user_id = data.get('_auth_user_id', None)
        remote_ip = data.get('remote_ip', None)
        if user_id and remote_ip:
            user = User.objects.get(pk=int(user_id))
            u = {}
            u['id'] = user.id
            u['remote_ip'] = remote_ip
            u['username'] = user.username
            if settings.LOOKUP_HOSTNAME_ADMIN:
                u['hostname'] = get_ip_dns_name(remote_ip)
            else:
                u['hostname'] = ""
            user_list.append(u)
    return user_list
