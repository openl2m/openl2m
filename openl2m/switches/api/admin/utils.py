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
from switches.models import SwitchGroup
from switches.utils import dprint


def add_to_switchgroup(request, switch):
    '''
    Add a given switch to a list of switchgroups in the request data.
    The switchgroups parameter should contain *all* group memberships!!!
    Any other existing group membership will be removed.

    Parameters:
        request: the HttpRequest object, that may contain the 'switchgroups' field in the data element.
                 switchgroups is a comma-separated list of SwitchGroup() id's
        switch: the Switch() object to add to the groups

    Returns:
        True
    '''
    dprint(f"add_to_switchgroup() switch={switch.name}")
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
            dprint(f"ADD to group: {pk} = {group.name}")
            group.switches.add(switch)
        except Exception as err:
            # we ignore bad group numbers, and unknown groups
            dprint(f"SwitchGroup.get({pk}) error: {err}")

    # now go through and remove from all other groups:
    for group in SwitchGroup.objects.all():
        if group.pk not in group_list:
            dprint(f"DELETE from group: {group.pk} = {group.name}")
            group.switches.remove(switch)  # remove is No-Op if not member.

    return True
