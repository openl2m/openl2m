# Create your Celery scheduled tasks here
from __future__ import absolute_import, unicode_literals
from celery import shared_task

from .utils import dprint

@shared_task
def bulkedit_job(user_id, http_post):
    dprint("BulkEdit JOB!")
    return 0
