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

# Celery scheduler integration according to
# https://docs.celeryproject.org/en/latest/django/first-steps-with-django.html
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openl2m.settings')

app = Celery('openl2m')

if settings.USE_TZ:
    app.conf.timezone = settings.TIME_ZONE

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


def get_celery_info():
    """
    Return a dict with all Celery related information, see
    http://docs.celeryproject.org/en/latest/userguide/workers.html#inspecting-workers
    """
    try:
        i = app.control.inspect()
        stats = i.stats()
        registered_tasks = i.registered()
        active_tasks = i.active()
        scheduled_tasks = i.scheduled()
        result = {
            'stats': stats,
            'registered_tasks': registered_tasks,
            'active_tasks': active_tasks,
            'scheduled_tasks': scheduled_tasks
        }
        return result
    except Exception:
        # any error means Celery not running!
        return False


def is_celery_running():
    """
    Check if Celery is running. Return True or False
    """
    if not settings.TASKS_ENABLED:
        return False
    # we have seen strange exception here, so catch them:
    try:
        i = app.control.inspect()
        stats = i.stats()
        if stats:
            return True
        return False
    except Exception:
        # anything go wrong just return False
        return False
