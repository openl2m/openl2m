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

from openl2m.celery import is_celery_running


def user_can_run_tasks(user, group, switch):
    """
    Can this use user schedule tasks?
    Return True if so, False if not.
    """
    if not is_celery_running():
        return False
    if user.is_superuser or user.is_staff:
        return True
    if user.profile.tasks and not group.read_only and not switch.read_only \
       and not user.profile.read_only:
        return True
    #dis-allow everything else
    return False


def user_can_bulkedit(user, group, switch):
    """
    Verify if this user can bulk-edit.
    Return True is so, False if not.
    """
    if user.profile.bulk_edit and group.bulk_edit and switch.bulk_edit \
       and not group.read_only and not switch.read_only and \
       not user.profile.read_only:
       return True
    return False
