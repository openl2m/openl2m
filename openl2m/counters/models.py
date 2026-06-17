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
from django.db import models
from django.contrib.auth.signals import user_logged_in, user_login_failed

# this app creates a simple Counter class, used to track some activity counters
from counters import constants

from switches.utils import dprint

# this class is intended only to be used from the admin site, or from migrations!


class Counter(models.Model):
    """
    A simple class to create a counter to track activity.
    """

    name = models.CharField(
        max_length=64,
        unique=True,
    )
    description = models.CharField(
        max_length=100,
        blank=True,
    )
    value = models.PositiveBigIntegerField(
        default=0,
        verbose_name='Value of this counter',
    )

    class Meta:  # pylint: disable=too-few-public-methods
        ordering = ['name']
        verbose_name = 'Counter'
        verbose_name_plural = 'Counters'

    def display_name(self):
        """
        This is used in templates, so we can 'annotate' as needed
        """
        return str(self.name)

    def __str__(self):
        return self.display_name()


def counter_increment(name, addition=1):
    # function to increment the value of a named counter
    dprint(f"counter_increment({name})")
    try:
        c = Counter.objects.get(name=name)  # pylint: disable=no-member
        c.value += addition
        c.save()

    except Exception:
        # ignore
        dprint("Error finding counter!")


def increment_login_counter(sender, user, request, **kwargs):  # pylint: disable=unused-argument
    # count the login!
    counter_increment(constants.COUNTER_LOGINS)


def increment_login_failed_counter(sender, credentials, request, **kwargs):  # pylint: disable=unused-argument
    # count the failed login!
    counter_increment(constants.COUNTER_LOGINS_FAILED)


# hook into the user-logged-in/failed signal:
user_logged_in.connect(increment_login_counter)
user_login_failed.connect(increment_login_failed_counter)
