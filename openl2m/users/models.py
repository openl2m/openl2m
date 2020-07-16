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
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_save
from django.dispatch import receiver

from switches.constants import LOG_TYPE_LOGIN_OUT, LOG_LOGIN, LOG_LOGOUT, LOG_LOGIN_FAILED
from switches.models import Log
from switches.utils import get_remote_ip

#
# add additional fields to the User models
# see
# https://docs.djangoproject.com/en/2.2/topics/auth/customizing/#extending-the-existing-user-model
# https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html
# https://docs.djangoproject.com/en/2.2/topics/signals/
# https://docs.djangoproject.com/en/2.2/ref/signals/#django.db.models.signals.pre_save
#


class Profile(models.Model):
    # this adds some additional "Profile" fields to the user object
    # start with the relationship to the User object
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # now add additional fields
    read_only = models.BooleanField(
        default=False,
        verbose_name='Read-Only access',
        help_text="If checked, user will have only Read-Only access to switches"
    )
    bulk_edit = models.BooleanField(
        default=True,
        verbose_name='Bulk-editing of interfaces',
        help_text='If Bulk Edit is set, this user can edit multiple interfaces at once on switches.',
    )
    tasks = models.BooleanField(
        default=False,
        verbose_name='Allow scheduled tasks',
        help_text='If Tasks is set, this user can schedule changes on switches at some future date.',
    )
    allow_poe_toggle = models.BooleanField(
        default=False,
        verbose_name='Poe Toggle All',
        help_text='If set, allow PoE toggle on all interfaces',
    )
    edit_if_descr = models.BooleanField(
        default=True,
        verbose_name='Edit Port Description',
        help_text='If set, allow interface descriptions to be edited.'
    )
    are_you_sure = models.BooleanField(
        default=True,
        verbose_name='Are You Sure?',
        help_text="If checked, user will get 'Are You Sure?' question on changes"
    )

    class Meta:
        pass

    def __str__(self):
        # Only display the last 24 bits of the token to avoid accidental exposure.
        return self.user.username + " Profile"


# and the signal handlers to auto-create and auto-update
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


def create_logged_in_log_entry(sender, user, request, **kwargs):
    # log the login!
    log = Log(user=request.user,
              ip_address=get_remote_ip(request),
              action=LOG_LOGIN,
              description="Logged in",
              type=LOG_TYPE_LOGIN_OUT)
    log.save()


def create_logged_out_log_entry(sender, user, request, **kwargs):
    # log the logout!
    log = Log(ip_address=get_remote_ip(request),
              action=LOG_LOGOUT,
              description="Logged out",
              type=LOG_TYPE_LOGIN_OUT)
    if isinstance(request.user, User):
        log.user = request.user
    log.save()


def create_login_failed_log_entry(sender, credentials, request, **kwargs):
    # log the failed login!
    log = Log(user=None,
              ip_address=get_remote_ip(request),
              action=LOG_LOGIN_FAILED,
              description=f"Login failed: user={credentials['username']}",
              type=LOG_TYPE_LOGIN_OUT)
    log.save()


# hook into the user-logged-in/out/failed signal:
user_logged_in.connect(create_logged_in_log_entry)
user_logged_out.connect(create_logged_out_log_entry)
user_login_failed.connect(create_login_failed_log_entry)
