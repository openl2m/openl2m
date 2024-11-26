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
from importlib.metadata import version as pkg_version
import os
import sys
import time

import django
from django.conf import settings
from django.db import connection as db_connection, ProgrammingError
from django.utils import timezone

from counters.models import Counter

from switches.constants import (
    LOG_TYPE_CHANGE,
    LOG_TYPE_COMMAND,
    LOG_TYPE_LOGIN_OUT,
    LOG_TYPE_VIEW,
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

from switches.utils import dprint

from users.models import Token


def get_environment_info() -> dict:
    '''Get information about the runtime environment, and return in a dict().'''
    environment = {"Python": f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}"}
    # OS environment information
    uname = os.uname()
    environment["OS"] = f"{uname.sysname} ({uname.release})"
    # environment['Version'] = uname.version
    environment["Distro"] = f"{distro.name()} {distro.version(best=True)}"
    environment["Hostname"] = uname.nodename
    environment["Django"] = django.get_version()
    # parse the PostgreSQL version (the only db we support)
    # version_main = int(db_connection.pg_version / 10000)
    # version_minor = int(db_connection.pg_version - (version_main * 10000))
    # environment["PostgreSQL"] = f"{version_main}.{version_minor}"
    try:
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            psql_version = cursor.fetchone()[0]
            psql_version = psql_version.split('(')[0].strip()
            cursor.execute("SELECT current_database()")
            db_name = cursor.fetchone()[0]
            cursor.execute(f"SELECT pg_size_pretty(pg_database_size('{db_name}'))")
            db_size = cursor.fetchone()[0]
            environment["Database"] = psql_version
            environment["Database Name"] = db_name
            environment["Database Size"] = db_size
    except (ProgrammingError, IndexError):
        pass

    # show the "ezsnmp" package version
    environment["EzSnmp"] = pkg_version('ezsnmp')

    environment["OpenL2M"] = f"{settings.VERSION} ({settings.VERSION_DATE})"
    if os.environ.get('IN_CONTAINER', False):
        environment["Dockerized"] = "Yes"

    if settings.DEBUG:
        environment['Debug'] = "Enabled"
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


def get_database_info() -> dict:
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


def get_usage_info() -> dict:
    '''Get OpenL2M application usage, and return as a dict().'''
    usage = {}  # usage statistics

    # Devices accessed:
    filter = {
        "type__in": [LOG_TYPE_VIEW, LOG_TYPE_CHANGE],
        "switch_id__isnull": False,
        "timestamp__date": datetime.date.today(),
    }
    usage['Devices today'] = Log.objects.filter(**filter).values_list('switch_id', flat=True).distinct().count()

    filter = {
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=7),
        "switch_id__isnull": False,
    }
    usage['Devices last 7 days'] = Log.objects.filter(**filter).values_list('switch_id', flat=True).distinct().count()

    filter = {
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=31),
        "switch_id__isnull": False,
    }
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

    # Unique Logins
    filter = {}
    filter['type'] = int(LOG_TYPE_LOGIN_OUT)
    filter['timestamp__date'] = datetime.date.today()
    usage['Users today'] = Log.objects.filter(**filter).values_list('user_id', flat=True).distinct().count()

    filter = {}
    filter['type'] = int(LOG_TYPE_LOGIN_OUT)
    filter['timestamp__gte'] = timezone.now().date() - datetime.timedelta(days=7)
    usage['Users last 7 days'] = Log.objects.filter(**filter).values_list('user_id', flat=True).distinct().count()

    filter = {}
    filter['type'] = int(LOG_TYPE_LOGIN_OUT)
    filter['timestamp__gte'] = timezone.now().date() - datetime.timedelta(days=31)
    usage['Users last 31 days'] = Log.objects.filter(**filter).values_list('user_id', flat=True).distinct().count()

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


def get_top_n_from_dict_on_count(data: dict) -> dict:
    """Return the TOP_N from the dcitionary with value, based on the 'count' attribute.

    Args:
    data (dict): a dictionary of dictionaries containing at least the 'count' attrbute.

    Returns:
        (dict): the TOP-N (ie sorted) entries of the data (input) argument.

    """
    # sort by descending order:
    data_sorted = dict(sorted(data.items(), key=lambda x: x[1]['count'], reverse=True))
    # # and limit to TOP-N:
    top_data = {}
    num = 0
    for key, val in data_sorted.items():
        top_data[key] = val
        num += 1
        if num == settings.TOP_ACTIVITY:
            break
    return top_data


def get_top_changed_devices() -> dict:
    """Return a dict with the most active (changed) devices over the last TOP_ACTIVITY_DAYS"""
    devices = {}
    filter = {
        "type": int(LOG_TYPE_CHANGE),
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=settings.TOP_ACTIVITY_DAYS),
    }
    # records = Log.objects.filter(**filter).values_list('switch_id', flat=True)
    logs = Log.objects.filter(**filter)
    # there is probably a better way to do this with a filter above, but this works also:
    for log in logs:
        if log.switch is not None:
            if log.switch.id not in devices:
                devices[log.switch.id] = {
                    'name': log.switch.name,
                    'count': 1,
                }
            else:
                devices[log.switch.id]['count'] += 1

    return get_top_n_from_dict_on_count(devices)


def get_top_viewed_devices() -> dict:
    """Return a dict with the most viewed devices over the last TOP_ACTIVITY_DAYS"""
    devices = {}
    filter = {
        "type": int(LOG_TYPE_VIEW),
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=settings.TOP_ACTIVITY_DAYS),
    }
    # records = Log.objects.filter(**filter).values_list('switch_id', flat=True)
    logs = Log.objects.filter(**filter)
    # there is probably a better way to do this with a filter above, but this works also:
    for log in logs:
        if log.switch is not None:
            if log.switch.id not in devices:
                devices[log.switch.id] = {
                    'name': log.switch.name,
                    'count': 1,
                }
            else:
                devices[log.switch.id]['count'] += 1

    return get_top_n_from_dict_on_count(devices)


def get_top_active_users() -> dict:
    """Return a dict with the most active users, based on views or changes, over the last TOP_ACTIVITY_DAYS"""
    users = {}
    filter = {
        "type__in": [LOG_TYPE_VIEW, LOG_TYPE_CHANGE],
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=settings.TOP_ACTIVITY_DAYS),
    }
    logs = Log.objects.filter(**filter)
    # there is probably a better way to do this with a filter above, but this works also:
    for log in logs:
        if log.user is not None:
            if log.user.id not in users:
                users[log.user.id] = {
                    'name': log.user.username,
                    'count': 1,
                }
            else:
                users[log.user.id]['count'] += 1

    return get_top_n_from_dict_on_count(users)
