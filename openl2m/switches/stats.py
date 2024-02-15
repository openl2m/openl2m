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

#
# Functions that perform statistics calculations used in Web UI and REST API
#
import datetime
import distro
import git
import os
import sys
import time

import django
from django.conf import settings
from django.utils import timezone

from counters.models import Counter

from switches.constants import (
    LOG_TYPE_CHANGE,
    LOG_TYPE_COMMAND,
    LOG_TYPE_LOGIN_OUT,
    LOG_LOGIN_REST_API,
)

from switches.models import (
    SnmpProfile,
    NetmikoProfile,
    Command,
    CommandList,
    VLAN,
    VlanGroup,
    Switch,
    SwitchGroup,
    Log,
)

from users.models import Token


def get_environment_info():
    '''Get information about the runtime environment, and return in a dict().'''
    environment = {"Python": f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}"}
    # OS environment information
    uname = os.uname()
    environment["OS"] = f"{uname.sysname} ({uname.release})"
    # environment['Version'] = uname.version
    environment["Distro"] = f"{distro.name()} {distro.version(best=True)}"
    environment["Hostname"] = uname.nodename
    environment["Django"] = django.get_version()
    environment["OpenL2M version"] = f"{settings.VERSION} ({settings.VERSION_DATE})"

    try:
        repo = git.Repo(search_parent_directories=True)
        sha = repo.head.object.hexsha
        short_sha = repo.git.rev_parse(sha, short=8)
        branch = repo.active_branch
        commit_date = time.strftime("%a, %d %b %Y %H:%M UTC", time.gmtime(repo.head.object.committed_date))
        environment["Git version"] = f"{branch} ({short_sha})"
        environment["Git commit"] = commit_date
    except Exception:
        environment["Git version"] = "Not found!"
    return environment


def get_database_info():
    '''Get information about various database items, and return as a dict().'''
    db_items = {"Switches": Switch.objects.count()}  # database object item counts
    # need to calculate switchgroup count, as we count only groups with switches!
    group_count = 0
    for group in SwitchGroup.objects.all():
        if group.switches.count():
            group_count += 1
    db_items["Switch Groups"] = group_count
    db_items["Vlans"] = VLAN.objects.count()
    db_items["Vlan Groups"] = VlanGroup.objects.count()
    db_items["SNMP Profiles"] = SnmpProfile.objects.count()
    db_items["Credentials Profiles"] = NetmikoProfile.objects.count()
    db_items["Commands"] = Command.objects.count()
    db_items["Command Lists"] = CommandList.objects.count()
    db_items["API Tokens"] = Token.objects.count()
    db_items["Log Entries"] = Log.objects.count()
    return db_items


def get_usage_info():
    '''Get OpenL2M application usage, and return as a dict().'''
    usage = {}  # usage statistics

    # Devices accessed:
    filter = {}
    filter['timestamp__date'] = datetime.date.today()
    usage['Devices today'] = Log.objects.filter(**filter).values_list('switch_id', flat=True).distinct().count()

    filter = {}
    filter['timestamp__gte'] = timezone.now().date() - datetime.timedelta(days=7)
    usage['Devices last 7 days'] = Log.objects.filter(**filter).values_list('switch_id', flat=True).distinct().count()

    filter = {}
    filter['timestamp__gte'] = timezone.now().date() - datetime.timedelta(days=31)
    usage['Devices last 31 days'] = Log.objects.filter(**filter).values_list('switch_id', flat=True).distinct().count()

    # Changes made
    filter = {}
    filter['type'] = int(LOG_TYPE_CHANGE)
    filter['timestamp__date'] = datetime.date.today()
    usage['Changes today'] = Log.objects.filter(**filter).count()

    filter = {
        "type": int(LOG_TYPE_CHANGE),
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=7),
    }
    usage["Changes last 7 days"] = Log.objects.filter(**filter).count()

    filter = {
        "type": int(LOG_TYPE_CHANGE),
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=31),
    }
    usage["Changes last 31 days"] = Log.objects.filter(**filter).count()

    # the total change count since install from Counter()'changes') object:
    usage["Total Changes"] = Counter.objects.get(name="changes").value

    # API requests:
    filter = {}
    filter['type'] = int(LOG_TYPE_LOGIN_OUT)
    filter['action'] = int(LOG_LOGIN_REST_API)
    filter['timestamp__date'] = datetime.date.today()
    usage['API calls today'] = Log.objects.filter(**filter).count()

    filter = {
        "type": int(LOG_TYPE_LOGIN_OUT),
        "action": int(LOG_LOGIN_REST_API),
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=7),
    }
    usage["API calls last 7 days"] = Log.objects.filter(**filter).count()

    filter = {
        "type": int(LOG_TYPE_LOGIN_OUT),
        "action": int(LOG_LOGIN_REST_API),
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=31),
    }
    usage["API calls last 31 days"] = Log.objects.filter(**filter).count()

    # Commands run:
    filter = {"type": int(LOG_TYPE_COMMAND), "timestamp__date": datetime.date.today()}
    usage["Commands today"] = Log.objects.filter(**filter).count()

    filter = {
        "type": int(LOG_TYPE_COMMAND),
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=7),
    }
    usage["Commands last 7 days"] = Log.objects.filter(**filter).count()

    filter = {
        "type": int(LOG_TYPE_COMMAND),
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=31),
    }
    usage["Commands last 31 days"] = Log.objects.filter(**filter).count()

    # total number of commands run:
    usage["Total Commands"] = Counter.objects.get(name="commands").value

    return usage
