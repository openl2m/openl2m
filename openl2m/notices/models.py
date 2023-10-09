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

# this idea originates from https://djangosnippets.org/snippets/1310/
# and implements using https://docs.djangoproject.com/en/4.1/ref/contrib/messages/

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now

from django.contrib.messages import constants as notice_levels

NOTICE_PRIORITY_CHOICES = [
    # [notice_levels.DEBUG, 'DEBUG'],
    [notice_levels.INFO, 'Information'],
    [notice_levels.SUCCESS, 'Success'],
    [notice_levels.WARNING, 'Warning'],
    # [notice_levels.ERROR, 'Error'],
]


class NoticeManager(models.Manager):
    def active_notices(self):
        dtnow = now()
        return (
            super(NoticeManager, self).get_queryset().filter(enabled=True, start_time__lte=dtnow, end_time__gte=dtnow)
        )


class Notice(models.Model):
    enabled = models.BooleanField(default=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    title = models.CharField(_('name'), unique=True, max_length=100)
    priority = models.PositiveSmallIntegerField(
        choices=NOTICE_PRIORITY_CHOICES,
        default=notice_levels.WARNING,
        verbose_name='Notice priority',
        help_text='Priority of this notice, as defined by Message Levels',
    )
    content = models.TextField(_('content'), blank=False)

    objects = NoticeManager()

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return self.title
