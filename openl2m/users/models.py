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
import binascii
import netaddr
import os

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.core.validators import MinLengthValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone


from switches.constants import LOG_TYPE_LOGIN_OUT, LOG_LOGIN, LOG_LOGOUT, LOG_LOGIN_FAILED
from switches.models import Log
from switches.utils import dprint, get_remote_ip

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
        help_text="If checked, user will have only Read-Only access to switches",
    )
    bulk_edit = models.BooleanField(
        default=True,
        verbose_name='Bulk-editing of interfaces',
        help_text='If Bulk Edit is set, this user can edit multiple interfaces at once on switches.',
    )
    vlan_edit = models.BooleanField(
        default=False,
        verbose_name='Allow VLAN adding or editing',
        help_text='If VLAN Edit is set, this user can add or edit VLANs on switches.',
    )
    allow_poe_toggle = models.BooleanField(
        default=False,
        verbose_name='Poe Toggle All',
        help_text='If set, allow PoE toggle on all interfaces',
    )
    edit_if_descr = models.BooleanField(
        default=True,
        verbose_name='Edit Port Description',
        help_text='If set, allow interface descriptions to be edited.',
    )
    are_you_sure = models.BooleanField(
        default=True,
        verbose_name='Are You Sure?',
        help_text="If checked, user will get 'Are You Sure?' question on changes",
    )
    last_ldap_dn = models.CharField(
        max_length=1024,
        blank=True,
        verbose_name="Last LDAP DN",
        help_text="The LDAP DN of the last LDAP login (if any)",
    )
    last_ldap_login = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Last LDAP login",
        help_text="The time of the most recent LDAP login (if any)",
    )
    theme = models.CharField(
        max_length=40,
        blank=False,
        null=False,
        default="light",
        verbose_name="The Theme selected",
        help_text="Set to a valid theme name",
    )

    class Meta:
        pass

    def __str__(self):
        # Only display the last 24 bits of the token to avoid accidental exposure.
        return self.user.username + " Profile"


# and the signal handler to auto-create or auto-update
@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        # newly saved user object instance
        Profile.objects.create(user=instance)
    else:
        # pre-existing user object
        instance.profile.save()


def create_logged_in_log_entry(sender, user, request, **kwargs):
    # log the login!
    log = Log(
        user=request.user,
        ip_address=get_remote_ip(request),
        action=LOG_LOGIN,
        description="Logged in",
        type=LOG_TYPE_LOGIN_OUT,
    )
    log.save()


def create_logged_out_log_entry(sender, user, request, **kwargs):
    # log the logout!
    log = Log(ip_address=get_remote_ip(request), action=LOG_LOGOUT, description="Logged out", type=LOG_TYPE_LOGIN_OUT)
    if isinstance(request.user, User):
        log.user = request.user
    log.save()


def create_login_failed_log_entry(sender, credentials, request, **kwargs):
    # log the failed login!
    log = Log(
        user=None,
        ip_address=get_remote_ip(request),
        action=LOG_LOGIN_FAILED,
        description=f"Login failed: user={credentials['username']}",
        type=LOG_TYPE_LOGIN_OUT,
    )
    log.save()


# hook into the user-logged-in/out/failed signal:
user_logged_in.connect(create_logged_in_log_entry)
user_logged_out.connect(create_logged_out_log_entry)
user_login_failed.connect(create_login_failed_log_entry)

#
# this is adopted from Netbox: users.models
#
#
# REST API
#


def generate_key():
    # Generate a random 160-bit key expressed in hexadecimal.
    return binascii.hexlify(os.urandom(20)).decode()


def ip_in_list(client_ip, ip_list):
    """Validate client IP again list IP's.

    Args:
        client_ip (str): the IP address to check.
        ip_list (str): list of comma-separated IP's in CIDR format.

    Returns:
        (boolean): True if found in list, False if not.
    """
    dprint("ip_in_list()")
    for net in ip_list.replace(" ", "").split(","):
        dprint(f"  Checking for net '{net}'")
        try:
            ipnet = netaddr.IPNetwork(net)
        except Exception as err:
            # bad network string, IGNORE!
            dprint(f"  IGNORING BAD network: '{net}' ({err})")
            continue
        else:
            if client_ip in ipnet:
                dprint(f"  IP '{client_ip}' found in '{net}'")
                return True
    return False


class Token(models.Model):
    """
    An API token used for user authentication. This extends the stock model to allow each user to have multiple tokens.
    It also supports setting an expiration time and toggling write ability.
    """

    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='tokens')
    created = models.DateTimeField(verbose_name='created', auto_now_add=True)
    expires = models.DateTimeField(verbose_name='expires', blank=True, null=True)
    last_used = models.DateTimeField(verbose_name='last used', blank=True, null=True)
    key = models.CharField(verbose_name='key', max_length=40, unique=True, validators=[MinLengthValidator(40)])
    write_enabled = models.BooleanField(
        verbose_name='write enabled', default=True, help_text='Permit create/update/delete operations using this key'
    )
    description = models.CharField(verbose_name='description', max_length=200, blank=True)
    allowed_ips = models.CharField(
        verbose_name='allowed IPs',
        max_length=200,
        blank=True,
        help_text='Allowed IPv4/IPv6 networks from where the token can be used. Leave blank for no restrictions. '
        'Ex: "10.1.1.0/24, 192.168.10.16/32, 2001:DB8:1::/64"',
    )

    class Meta:
        verbose_name = 'token'
        verbose_name_plural = 'tokens'

    def __str__(self):
        return self.key if settings.ALLOW_TOKEN_RETRIEVAL else self.partial

    def get_absolute_url(self):
        return reverse('users:token', args=[self.pk])

    @property
    def partial(self):
        return f'******{self.key[-6:]}' if self.key else ''

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)

    @staticmethod
    def generate_key():
        # Generate a random 160-bit key expressed in hexadecimal.
        return binascii.hexlify(os.urandom(20)).decode()

    @property
    def is_expired(self):
        if self.expires is None or timezone.now() < self.expires:
            return False
        return True

    def validate_client_ip(self, client_ip):
        """
        Validate the API client IP address against the source IP restrictions (if any) set on the token.
        """
        dprint(f"Token().validate_client_ip() for {client_ip}")

        # are we globally denying this IP address?
        if settings.API_CLIENT_IP_DENIED and ip_in_list(client_ip=client_ip, ip_list=settings.API_CLIENT_IP_DENIED):
            dprint("  Client denied, in settings.API_CLIENT_IP_DENIED!")
            return False

        # is this IP globally permitted?
        if settings.API_CLIENT_IP_ALLOWED and not ip_in_list(
            client_ip=client_ip, ip_list=settings.API_CLIENT_IP_ALLOWED
        ):
            dprint("  Client denied, not in settings.API_CLIENT_IP_ALLOWED!")
            return False

        # Check the Token allowed IP list:
        if self.allowed_ips and not ip_in_list(client_ip=client_ip, ip_list=self.allowed_ips):
            dprint("  Client denied, not in token.allowed_ips!")
            return False

        dprint("  Client ALLOWED!")
        return True
