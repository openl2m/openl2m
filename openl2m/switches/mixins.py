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

from switches.connect.classes import Error
from switches.constants import LOG_TYPE_ERROR
from switches.device_actions import DeviceActions
from switches.models import Log
from switches.permissions import get_group_and_switch
from switches.utils import error_page, error_page_by_id, success_page_by_id, get_remote_ip

from counters.models import counter_increment
from counters.constants import COUNTER_ACCESS_DENIED


class SwitchPermissionMixin:
    """
    Helper for views that need to resolve group+switch from URL kwargs and
    deny access when the user has no permission.

    Usage::

        group, switch, denied = self._get_switch_or_deny(request, group_id, switch_id)
        if denied:
            return denied
    """

    def _get_switch_or_deny(self, request, group_id, switch_id):
        group, switch = get_group_and_switch(request=request, group_id=group_id, switch_id=switch_id)
        if group is None or switch is None:
            log = Log(
                user=request.user,
                ip_address=get_remote_ip(request),
                switch=switch,
                group=group,
                type=LOG_TYPE_ERROR,
                description="Permission denied!",
            )
            log.save()
            error = Error()
            error.status = True
            error.description = "Access denied!"
            counter_increment(COUNTER_ACCESS_DENIED)
            return None, None, error_page(request=request, group=False, switch=False, error=error)
        return group, switch, None


class SwitchActionMixin:
    """
    Helper for single-action POST views that call a DeviceActions method and
    return either an error page or a success page.

    Usage::

        return self._dispatch_action(
            request, group_id, switch_id,
            "interface_admin_change",
            message="Optional override message",  # omit to use info.description
            interface_key=name, new_state=True,   # forwarded to action method
        )
    """

    def _dispatch_action(self, request, group_id, switch_id, action_name, message=None, **kwargs):
        actions = DeviceActions(request, group_id, switch_id)
        retval, info = getattr(actions, action_name)(**kwargs)
        if not retval:
            return error_page_by_id(request=request, group_id=group_id, switch_id=switch_id, error=info)
        return success_page_by_id(
            request=request,
            group_id=group_id,
            switch_id=switch_id,
            message=message if message is not None else info.description,
        )
