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
from importlib.metadata import version as pkg_version
import os
import sys
import time

import distro
import django
from django.conf import settings
from django.db import connection as db_connection, ProgrammingError
from django.utils import timezone
import git

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

from users.models import Token


def get_environment_info() -> dict:
    '''Get information about the runtime environment, and return in a dict().
    The key is the "attribute name" in api format (lc with _),
    and values are a dict of "label" and "value". eg>
    { "attribute" = {
         "label": "Attribute Label",  # Note: this can be Internationalized if needed!
         "value": attribute-value,
         }
    }
    '''
    environment = {}
    environment["python"] = {
        "label": "Python",
        "value": f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}",
    }
    # OS environment information
    uname = os.uname()
    environment["os"] = {
        "label": "OS",
        "value": f"{uname.sysname} ({uname.release})",
    }
    # environment["Version"] = uname.version
    environment["distro"] = {
        "label": "Distro",
        "value": f"{distro.name()} {distro.version(best=True)}",
    }
    environment["hostname"] = {
        "label": "Hostname",
        "value": uname.nodename,
    }
    environment["django"] = {
        "label": "Django",
        "value": django.get_version(),
    }

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
            environment["database"] = {
                "label": "Database",
                "value": psql_version,
            }
            environment["database_name"] = {
                "label": "Database Name",
                "value": db_name,
            }
            environment["database_size"] = {
                "label": "Database Size",
                "value": db_size,
            }
    except (ProgrammingError, IndexError):
        pass

    # show the "ezsnmp" package version
    environment["ezsnmp"] = {
        "label": "EzSnmp",
        "value": pkg_version('ezsnmp'),
    }

    environment["openl2m"] = {
        "label": "OpenL2M",
        "value": f"{settings.VERSION} ({settings.VERSION_DATE})",
    }

    if os.environ.get('IN_CONTAINER', False):
        environment["dockerized"] = {
            "label": "Dockerized",
            "value": "Yes",
        }

    if settings.DEBUG:
        environment["debug"] = {
            "label": "Debug",
            "value": "Enabled",
        }

        try:
            repo = git.Repo(search_parent_directories=True)
            sha = repo.head.object.hexsha
            short_sha = repo.git.rev_parse(sha, short=8)
            branch = repo.active_branch
            commit_date = time.strftime("%a, %d %b %Y %H:%M UTC", time.gmtime(repo.head.object.committed_date))
            environment["git_version"] = {
                "label": "Git version",
                "value": f"{branch} ({short_sha})",
            }
            environment["git_commit"] = {
                "label": "Git Commit",
                "value": commit_date,
            }
        except Exception:
            environment["git_version"] = {
                "label": "Git version",
                "value": "Not found!",
            }

    return environment


def get_database_info() -> dict:
    '''Get information about various database items, and return as a dict().'''
    db_items = {}
    db_items["switches"] = {
        "label": "Switches",
        "value": Switch.objects.count(),  # database object item counts
    }

    # need to calculate switchgroup count, as we count only groups with switches!
    group_count = 0
    for group in SwitchGroup.objects.all():
        if group.switches.count():
            group_count += 1
            db_items["switchgroups"] = {
                "label": "Switch Groups",
                "value": group_count,
            }

    db_items["vlans"] = {
        "label": "Vlans",
        "value": VLAN.objects.count(),
    }

    db_items["vlan_groups"] = {
        "label": "Vlan Groups",
        "value": VlanGroup.objects.count(),
    }

    db_items["snmp_profiles"] = {
        "label": "SNMP Profiles",
        "value": SnmpProfile.objects.count(),
    }

    db_items["credentials_profiles"] = {
        "label": "Credentials Profiles",
        "value": NetmikoProfile.objects.count(),
    }

    db_items["commands"] = {
        "label": "Commands",
        "value": Command.objects.count(),
    }

    db_items["command_lists"] = {
        "label": "Command Lists",
        "value": CommandList.objects.count(),
    }

    db_items["api_tokens"] = {
        "label": "API Tokens",
        "value": Token.objects.count(),
    }

    db_items["log_entries"] = {
        "label": "Log Entries",
        "value": Log.objects.count(),
    }

    return db_items


def get_usage_info() -> dict:
    '''Get OpenL2M application usage, and return as a dict().'''
    usage = {}  # usage statistics

    one_hour_ago = timezone.now() - datetime.timedelta(hours=1)

    # Devices accessed:
    filter_values = {
        "type__in": [LOG_TYPE_VIEW, LOG_TYPE_CHANGE],
        "switch_id__isnull": False,
        "timestamp__gte": one_hour_ago,
    }
    usage["devices_last_hour"] = {
        "label": "Devices in last hour",
        "value": Log.objects.filter(**filter_values).values_list('switch_id', flat=True).distinct().count(),
    }

    filter_values = {
        "type__in": [LOG_TYPE_VIEW, LOG_TYPE_CHANGE],
        "switch_id__isnull": False,
        "timestamp__date": datetime.date.today(),
    }
    usage["devices_today"] = {
        "label": "Devices today",
        "value": Log.objects.filter(**filter_values).values_list('switch_id', flat=True).distinct().count(),
    }

    filter_values = {
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=7),
        "switch_id__isnull": False,
    }
    usage["devices_last_7_days"] = {
        "label": "Devices last 7 days",
        "value": Log.objects.filter(**filter_values).values_list('switch_id', flat=True).distinct().count(),
    }

    filter_values = {
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=31),
        "switch_id__isnull": False,
    }
    usage["devices_last_31_days"] = {
        "label": "Devices Last 31 Days",
        "value": Log.objects.filter(**filter_values).values_list('switch_id', flat=True).distinct().count(),
    }

    # Changes made
    filter_values = {
        'type': int(LOG_TYPE_CHANGE),
        'timestamp__gte': one_hour_ago,
    }
    usage["changes_last_hour"] = {
        "label": "Changes in last hour",
        "value": Log.objects.filter(**filter_values).count(),
    }

    filter_values = {
        'type': int(LOG_TYPE_CHANGE),
        'timestamp__date': datetime.date.today(),
    }
    usage["changes_today"] = {
        "label": "Changes today",
        "value": Log.objects.filter(**filter_values).count(),
    }

    filter_values = {
        "type": int(LOG_TYPE_CHANGE),
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=7),
    }
    usage["changes_last_7_days"] = {
        "label": "Changes last 7 days",
        "value": Log.objects.filter(**filter_values).count(),
    }

    filter_values = {
        "type": int(LOG_TYPE_CHANGE),
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=31),
    }
    usage["changes_last_31_days"] = {
        "label": "Changes last 31 days",
        "value": Log.objects.filter(**filter_values).count(),
    }

    # the total change count since install from Counter()'changes') object:
    usage["changes_total"] = {
        "label": "Total Changes",
        "value": Counter.objects.get(name="changes").value,
    }

    # Unique Logins
    filter_values = {
        'type': int(LOG_TYPE_LOGIN_OUT),
        'timestamp__gte': one_hour_ago,
    }
    usage["users_last_hour"] = {
        "label": "Users in last hour",
        "value": Log.objects.filter(**filter_values).values_list('user_id', flat=True).distinct().count(),
    }

    filter_values = {
        'type': int(LOG_TYPE_LOGIN_OUT),
        'timestamp__date': datetime.date.today(),
    }
    usage["users_today"] = {
        "label": "Users today",
        "value": Log.objects.filter(**filter_values).values_list('user_id', flat=True).distinct().count(),
    }

    filter_values = {
        'type': int(LOG_TYPE_LOGIN_OUT),
        'timestamp__gte': timezone.now().date() - datetime.timedelta(days=7),
    }
    usage["users_last_7_days"] = {
        "label": "Users last 7 days",
        "value": Log.objects.filter(**filter_values).values_list('user_id', flat=True).distinct().count(),
    }

    filter_values = {
        'type': int(LOG_TYPE_LOGIN_OUT),
        'timestamp__gte': timezone.now().date() - datetime.timedelta(days=31),
    }
    usage["users_last_31_days"] = {
        "label": "Users last 31 days",
        "value": Log.objects.filter(**filter_values).values_list('user_id', flat=True).distinct().count(),
    }

    # API requests:
    filter_values = {
        'type': int(LOG_TYPE_LOGIN_OUT),
        'action': int(LOG_LOGIN_REST_API),
        'timestamp__date': datetime.date.today(),
    }
    usage["api_calls_today"] = {
        "label": "API calls today",
        "value": Log.objects.filter(**filter_values).count(),
    }

    filter_values = {
        "type": int(LOG_TYPE_LOGIN_OUT),
        "action": int(LOG_LOGIN_REST_API),
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=7),
    }
    usage["api_calls_last_7_days"] = {
        "label": "API calls last 7 days",
        "value": Log.objects.filter(**filter_values).count(),
    }

    filter_values = {
        "type": int(LOG_TYPE_LOGIN_OUT),
        "action": int(LOG_LOGIN_REST_API),
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=31),
    }
    usage["api_calls_last_31_days"] = {
        "label": "API calls last 31 days",
        "value": Log.objects.filter(**filter_values).count(),
    }

    # Commands run:
    filter_values = {"type": int(LOG_TYPE_COMMAND), "timestamp__date": datetime.date.today()}
    usage["commands_today"] = {
        "label": "Commands today",
        "value": Log.objects.filter(**filter_values).count(),
    }

    filter_values = {
        "type": int(LOG_TYPE_COMMAND),
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=7),
    }
    usage["commands_last_7_days"] = {
        "label": "Commands last 7 days",
        "value": Log.objects.filter(**filter_values).count(),
    }

    filter_values = {
        "type": int(LOG_TYPE_COMMAND),
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=31),
    }
    usage["commands_last_31_days"] = {
        "label": "Commands last 31 days",
        "value": Log.objects.filter(**filter_values).count(),
    }

    # total number of commands run:
    usage["commands_total"] = {
        "label": "Total Commands",
        "value": Counter.objects.get(name="commands").value,
    }

    return usage


def get_top_n_from_dict_on_count(data: dict) -> dict:
    """Return the TOP_N from the dcitionary with value, based on the 'count' attribute.

    Args:
    data (dict): a dictionary of dictionaries containing at least the 'count' attrbute.

    Returns:
        (dict): the TOP-N (ie sorted) entries of the data (input) argument.

    """
    # sort by descending order:
    data_sorted = dict(sorted(data.items(), key=lambda x: x[1]["count"], reverse=True))
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
    filter_values = {
        "type": int(LOG_TYPE_CHANGE),
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=settings.TOP_ACTIVITY_DAYS),
    }
    # records = Log.objects.filter(**filter_values).values_list('switch_id', flat=True)
    logs = Log.objects.filter(**filter_values)
    # there is probably a better way to do this with a filter above, but this works also:
    for log in logs:
        if log.switch is not None:
            if log.switch.id not in devices:
                devices[log.switch.id] = {
                    'name': log.switch.name,
                    'count': 1,
                }
            else:
                devices[log.switch.id]["count"] += 1

    return get_top_n_from_dict_on_count(devices)


def get_top_viewed_devices() -> dict:
    """Return a dict with the most viewed devices over the last TOP_ACTIVITY_DAYS"""
    devices = {}
    filter_values = {
        "type": int(LOG_TYPE_VIEW),
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=settings.TOP_ACTIVITY_DAYS),
    }
    # records = Log.objects.filter(**filter_values).values_list('switch_id', flat=True)
    logs = Log.objects.filter(**filter_values)
    # there is probably a better way to do this with a filter above, but this works also:
    for log in logs:
        if log.switch is not None:
            if log.switch.id not in devices:
                devices[log.switch.id] = {
                    'name': log.switch.name,
                    'count': 1,
                }
            else:
                devices[log.switch.id]["count"] += 1

    return get_top_n_from_dict_on_count(devices)


def get_top_active_users() -> dict:
    """Return a dict with the most active users, based on views or changes, over the last TOP_ACTIVITY_DAYS"""
    users = {}
    filter_values = {
        "type__in": [LOG_TYPE_VIEW, LOG_TYPE_CHANGE],
        "timestamp__gte": timezone.now().date() - datetime.timedelta(days=settings.TOP_ACTIVITY_DAYS),
    }
    logs = Log.objects.filter(**filter_values)
    # there is probably a better way to do this with a filter above, but this works also:
    for log in logs:
        if log.user is not None:
            if log.user.id not in users:
                users[log.user.id] = {
                    'name': log.user.username,
                    'count': 1,
                }
            else:
                users[log.user.id]["count"] += 1

    return get_top_n_from_dict_on_count(users)
