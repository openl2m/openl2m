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
import json

from users.models import Profile
from switches.models import SwitchGroup
from switches.utils import dprint


def add_user_to_switchgroups(request, user):
    '''
    Add a given user to a list of switchgroups in the request data.
    The switchgroups parameter should contain *all* group memberships!!!
    Any other existing group membership will be removed.

    Parameters:
        request: the HttpRequest object, that may contain the 'switchgroups' field in the data element.
                 switchgroups is a comma-separated list of SwitchGroup() id's
        user: the User() object to add to the groups

    Returns:
        (bool) True if set, False if no-op.
    '''
    dprint(f"add_user_to_switchgroup() user={user.username}")
    if 'switchgroups' not in request.data:
        dprint("  No switchgroups found!")
        return False

    dprint(f"  Groups: {request.data['switchgroups']}")
    group_list = []  # the requested group memberships
    # get group ID's out of CSV string.
    for pk in request.data['switchgroups'].split(","):
        try:
            pk = int(pk)
            group_list.append(pk)
            group = SwitchGroup.objects.get(pk=pk)
            dprint(f"    ADD to group: {pk} = {group.name}")
            group.users.add(user)
        except Exception as err:
            # we ignore bad group numbers, and unknown groups
            dprint(f"SwitchGroup.get({pk}) error: {err}")

    # now go through and remove from all other groups:
    for group in SwitchGroup.objects.all():
        if group.pk not in group_list:
            dprint(f"    DELETE from group: {group.pk} = {group.name}")
            group.users.remove(user)  # remove is No-Op if not member.

    return True


def update_user_profile(request, user):
    '''
    Update profile fields for a given user.
    The profile parameter should exist in the request.data

    Parameters:
        request: the HttpRequest object, that may contain the 'profile' field in the data element.
                 profile is a dictionary of attribute = value.
        user: the User() object to add to the groups

    Returns:
        (object) Either the Profile() object, or None
    '''
    dprint(f"update_user_profile() user={user.username}")
    if 'profile' not in request.data:
        dprint("  No profile found!")
        return None

    dprint(f"Updating profile with: {request.data['profile']}")
    try:
        d = json.loads(request.data['profile'])
        if type(d) is dict:
            # all looks good, get user's Profile()
            profile = Profile.objects.get(user=user)
            dprint(f"Found Profile: {repr(profile)}")
            # and go update the fields:
            for name, value in d.items():
                dprint(f"  SET {name} = {value}")
                if hasattr(profile, name):
                    setattr(profile, name, value)
                else:
                    dprint("  INVALID Profile attribute!")
            profile.save()
            return profile
        else:
            dprint(f"  INVALID data type: {type(d)}")
            return None
    except Exception as err:
        dprint(f"  ERROR: {err}")
        return None
