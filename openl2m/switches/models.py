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
import logging.handlers
import json

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

# local copy of django-ordered-model, with some fixes:
# from libraries.django_ordered_model.ordered_model.models import OrderedModelManager, OrderedModel
from ordered_model.models import OrderedModelManager, OrderedModel

from switches.constants import *
from switches.connect.netmiko.constants import *
from switches.utils import is_valid_hostname_or_ip


#
# SNMP Profile is a complete description of an SNMP auth method, v1,2 or 3
#
class SnmpProfile(models.Model):
    """
    An SNMP profile defines a series of settings for SNMP-based management access.
    A switch can have exactly one snmp profile assigned to it.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    name = models.CharField(
        max_length=64,
        unique=True,
    )
    description = models.CharField(
        max_length=100,
        blank=True,
    )
    version = models.PositiveSmallIntegerField(
        choices=SNMP_VERSION_CHOICES,
        default=SNMP_VERSION_3,
    )
    # v2c settings:
    community = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name='v2c Community name',
    )
    # v3 settings:
    username = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        verbose_name='v3 Username',
    )
    passphrase = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name='v3 Authentication passphrase',
    )
    priv_passphrase = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name='v3 Privacy passphrase',
    )
    auth_protocol = models.PositiveSmallIntegerField(
        choices=SNMP_V3_AUTH_CHOICES,
        default=SNMP_V3_AUTH_SHA,
    )
    priv_protocol = models.PositiveSmallIntegerField(
        choices=SNMP_V3_PRIV_CHOICES,
        default=SNMP_V3_PRIV_AES,
    )
    sec_level = models.PositiveSmallIntegerField(
        choices=SNMP_V3_SECURITY_CHOICES,
        default=SNMP_V3_SECURITY_AUTH_PRIV,
        verbose_name='Security level',
    )
    context_name = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        verbose_name='v3 Context Name',
        help_text="SNMP v3 contextName field. Mostly left blank. Only set if you know what this is! (not used yet)",
    )
    context_engine_id = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        verbose_name='v3 Context EngineID',
        help_text="SNMP v3 contextEngineID field. Mostly left blank. Only set if you know what this is! (not used yet)",
    )
    udp_port = models.PositiveIntegerField(
        default=161,
        verbose_name='SNMP Udp port',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'SNMP Profile'
        verbose_name_plural = 'SNMP Profiles'

    def display_name(self):
        """
        This is used in templates, so we can 'annotate' as needed
        """
        return self.name + " (v" + str(self.version) + ")"

    def __str__(self):
        return self.display_name()

    def __unicode__(self):
        return unicode(self.name)


#
# Netmiko Profile is a complete description of a Netmiko/SSH configuration
# see more at https://github.com/ktbyers/netmiko
#
class NetmikoProfile(models.Model):
    """
    An Netmiko(SSH) profile defines a series of settings for management access over SSH.
    A switch can have exactly one netmiko/ssh profile assigned to it.
    Note this is ALSO used for the Napalm library!
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    name = models.CharField(
        max_length=64,
        unique=True,
    )
    description = models.CharField(
        max_length=100,
        blank=True,
    )
    username = models.CharField(
        max_length=32,
        default='username',
        # blank=True,
        # null=True,
        verbose_name='Username',
    )
    password = models.CharField(
        max_length=64,
        default='password',
        # blank=True,
        # null=True,
        verbose_name='Password',
    )
    device_type = models.CharField(
        max_length=64,
        choices=NETMIKO_DEVICE_TYPES,
        default='hp_comware',
        verbose_name='Netmiko device_type field',
    )
    enable_password = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name='Netmiko/SSH enable password, e.g. for Cisco devices (optional)',
    )
    tcp_port = models.PositiveIntegerField(
        default=22,
        verbose_name='Tcp port',
    )
    verify_hostkey = models.BooleanField(
        default=False,
        verbose_name='Verify the ssl host key',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Netmiko/SSH Profile'
        verbose_name_plural = 'Netmiko/SSH Profiles'

    def display_name(self):
        """
        This is used in templates, so we can 'annotate' as needed
        """
        return self.name

    def __str__(self):
        return self.display_name()

    def __unicode__(self):
        return unicode(self.display_name)


class Command(models.Model):
    """
    A command that can be send to a switch.
    %s will signify the switch interface name.
    """
    name = models.CharField(
        max_length=32,
        help_text="The name as shown to the user",
    )
    os = models.CharField(
        max_length=32,
        help_text="The switch OS name, for easier displaying & sorting",
    )
    description = models.CharField(
        max_length=100,
        blank=True,
        help_text="Explanation of command, shown as hover-over to user",
    )
    type = models.PositiveSmallIntegerField(
        choices=CMD_TYPE_CHOICES,
        default=CMD_TYPE_INTERFACE,
        verbose_name='Command type',
        help_text='Type of command, i.e. for the switch (global), or on chosen interface',
    )
    command = models.CharField(
        max_length=64,
        verbose_name='Command',
        help_text='The command. Use %s for interface name',
    )

    class Meta:
        ordering = ['type', 'name', 'os']
        unique_together = ['name', 'type', 'os']
        verbose_name = 'Command'
        verbose_name_plural = 'Commands'

    def display_name(self):
        """
        This is used in templates, so we can 'annotate' as needed
        """
        if self.os:
            return f"{self.name} ({self.os} - {self.get_type_display()})"
        return f"{self.name} ({self.get_type_display()})"

    def __str__(self):
        return self.display_name()

    def __unicode__(self):
        return unicode(self.display_name)


#
# List of show/display commands that can be sent to switches
#
class CommandList(models.Model):
    """
    An SNMP profile defines a series of settings for management access.
    A switch can have exactly one snmp profile assigned to it.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    name = models.CharField(
        max_length=64,
        unique=True,
    )
    description = models.CharField(
        max_length=100,
        blank=True,
    )
    global_commands = models.ManyToManyField(
        to='Command',
        limit_choices_to={'type': CMD_TYPE_GLOBAL},
        blank=True,      # we don't require to have a command
        # see https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.ForeignKey.related_name
        related_name='global_commands',      # from Commands object, we can now reference "Command.global_commands"
        verbose_name='Global commands to send to switch.',
        help_text='List of global "show" commands user can send to switch.',
    )
    interface_commands = models.ManyToManyField(
        to='Command',
        limit_choices_to={'type': CMD_TYPE_INTERFACE},
        blank=True,
        # see https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.ForeignKey.related_name
        related_name='interface_commands',      # from Commands object, we can now reference "Command.interface_commands"
        verbose_name='Interface commands to send to switch.',
        help_text='List of contextual "show interface" commands user can send to switch. %s will be replaced with interface name.',
    )
    global_commands_staff = models.ManyToManyField(
        to='Command',
        limit_choices_to={'type': CMD_TYPE_GLOBAL},
        blank=True,      # we don't require to have a vlan
        # see https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.ForeignKey.related_name
        related_name='global_commands_staff',      # from Commands object, we can now reference "Command.global_commands_staff"
        verbose_name='Global commands for Staff.',
        help_text='List of global "show" commands Staff users can send to switch.',
    )
    interface_commands_staff = models.ManyToManyField(
        to='Command',
        limit_choices_to={'type': CMD_TYPE_INTERFACE},
        blank=True,
        # see https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.ForeignKey.related_name
        related_name='interface_commands_staff',      # from Commands object, we can now reference "Command.interface_commands_staff"
        verbose_name='Interface commands for Staff.',
        help_text='List of contextual "show interface" commands Staff users can send to switch. %s will be replaced with interface name.',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Commands List'
        verbose_name_plural = 'Commands Lists'

    def display_name(self):
        """
        This is used in templates, so we can 'annotate' as needed
        """
        return self.name

    def __str__(self):
        return self.display_name()

    def __unicode__(self):
        return unicode(self.display_name)


class CommandTemplate(models.Model):
    """
    A "long" command template that can be send to a switch.
    Up to 8 fields and 3 pick-lists can be defined for the user to fill in values.
    """
    name = models.CharField(
        max_length=32,
        help_text="The name as shown to the user",
    )
    os = models.CharField(
        max_length=32,
        blank=True,
        help_text="The switch OS name, for easier displaying & sorting",
    )
    description = models.CharField(
        max_length=250,
        blank=True,
        help_text="Explanation of command template, shown as hover-over to user",
    )
    template = models.CharField(
        max_length=512,
        verbose_name='Command Template',
        help_text='The command template. Use {{field[1-8]}} or {{list[1-5]}} as needed.',
    )
    field1_name = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Name',
        help_text='Command template field 1 name.',
    )
    field1_description = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Description',
        help_text='Command template field 1 description.',
    )
    field1_regex = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Regex',
        help_text='Command template field 1 validation regular expression.',
    )
    field2_name = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Name',
        help_text='Command template field 2 name.',
    )
    field2_description = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Description',
        help_text='Command template field 2 description.',
    )
    field2_regex = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Regex',
        help_text='Command template field 2 validation regular expression.',
    )
    field3_name = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Name',
        help_text='Command template field 3 name.',
    )
    field3_description = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Description',
        help_text='Command template field 3 description.',
    )
    field3_regex = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Regex',
        help_text='Command template field 3 validation regular expression.',
    )
    field4_name = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Name',
        help_text='Command template field 4 name.',
    )
    field4_description = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Description',
        help_text='Command template field41 description.',
    )
    field4_regex = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Regex',
        help_text='Command template field 4 validation regular expression.',
    )
    field5_name = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Name',
        help_text='Command template field 5 name.',
    )
    field5_description = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Description',
        help_text='Command template field 5 description.',
    )
    field5_regex = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Regex',
        help_text='Command template field 5 validation regular expression.',
    )
    field6_name = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Name',
        help_text='Command template field 6 name.',
    )
    field6_description = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Description',
        help_text='Command template field 6 description.',
    )
    field6_regex = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Regex',
        help_text='Command template field 6 validation regular expression.',
    )
    field7_name = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Name',
        help_text='Command template field 7 name.',
    )
    field7_description = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Description',
        help_text='Command template field 7 description.',
    )
    field7_regex = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Regex',
        help_text='Command template field 7 validation regular expression.',
    )
    field8_name = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Name',
        help_text='Command template field 8 name.',
    )
    field8_description = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Description',
        help_text='Command template field 8 description.',
    )
    field8_regex = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Regex',
        help_text='Command template field 8 validation regular expression.',
    )
    list1_name = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Name',
        help_text='Command template pick list 1 name.',
    )
    list1_description = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Description',
        help_text='Command template pick list 1 description.',
    )
    list1_values = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Values',
        help_text='Command template pick list 1 comma-separated values.',
    )
    list2_name = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Name',
        help_text='Command template pick list 2 name.',
    )
    list2_description = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Description',
        help_text='Command template pick list 2 description.',
    )
    list2_values = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Values',
        help_text='Command template pick list 2 comma-separated values.',
    )
    list3_name = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Name',
        help_text='Command template pick list 3 name.',
    )
    list3_description = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Description',
        help_text='Command template pick list 3 description.',
    )
    list3_values = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Values',
        help_text='Command template pick list 3 comma-separated values.',
    )
    list4_name = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Name',
        help_text='Command template pick list 4 name.',
    )
    list4_description = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Description',
        help_text='Command template pick list 4 description.',
    )
    list4_values = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Values',
        help_text='Command template pick list 4 comma-separated values.',
    )
    list5_name = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Name',
        help_text='Command template pick list 5 name.',
    )
    list5_description = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Description',
        help_text='Command template pick list 5 description.',
    )
    list5_values = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Values',
        help_text='Command template pick list 5 comma-separated values.',
    )
    output_match_regex = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Match Regex',
        help_text='If command template output matches this regular expression, the \'match text\' will be shown, instead of output.',
    )
    output_match_text = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Match Text',
        help_text='Text to show (instead of output) if output matches the regular expression.',
    )
    output_fail_text = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Fail Text',
        help_text='Text to show (instead of output) if output does not match the regular expression.',
    )
    output_lines_keep_regex = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Output Lines Filter',
        help_text='If an output line matches this regular expression, the line will be shown. Otherwize, it will be removed from the output. If blank, all output is shown.',
    )

    class Meta:
        ordering = ['name', 'os']
        unique_together = ['name', 'os']
        verbose_name = 'Command Template'
        verbose_name_plural = 'Command Templates'

    def display_name(self):
        """
        This is used in templates, so we can 'annotate' as needed
        """
        if self.os:
            return f"{self.name} ({self.os})"
        return self.name

    def __str__(self):
        return self.display_name()

    def __unicode__(self):
        return unicode(self.display_name)


class VLAN(models.Model):
    """
    A VLAN is a distinct layer two forwarding domain identified by a 12-bit integer (1-4094). Each VLAN must have a name,
    however VLAN IDs need not be unique. A VLAN may optionally be assigned to a VLANGroup,
    within which all VLAN IDs and names but be unique.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    name = models.CharField(
        max_length=64,
    )
    vid = models.SmallIntegerField(
        verbose_name='ID',
        validators=[MinValueValidator(1), MaxValueValidator(4094)],
    )
    description = models.CharField(
        max_length=100,
        blank=True,
    )
    contact = models.CharField(
        max_length=100,
        blank=True,
    )

    class Meta:
        ordering = ['vid', 'name']
        unique_together = [
            ['vid', 'name'],
        ]
        verbose_name = 'VLAN'
        verbose_name_plural = 'VLANs'

    def display_name(self):
        """
        This is used in templates, so we can 'annotate' as needed
        """
        if self.vid == -1:
            return "(all) - ", self.name
        return "{} - {}".format(self.vid, self.name)

    def __str__(self):
        return self.display_name()


#
# Several VLANs in a group
#
class VlanGroup(models.Model):
    """
    Class that maintains a grouping of one or more vlans, to simplify management in SwitchGroup() objects
    """
    name = models.CharField(
        max_length=64,
    )
    description = models.CharField(
        max_length=100,
        blank=True,
    )
    vlans = models.ManyToManyField(
        to='VLAN',
        blank=True,      # we don't require to have a vlan
        # see https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.ForeignKey.related_name
        related_name='vlangroups',      # from VLAN object, we can now reference "VLAN.vlangroups"
        verbose_name='VLANs in group',
        help_text="A grouping of VLANs, e.g. by department"
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'VLAN Group'
        verbose_name_plural = 'VLAN Groups'

    def display_name(self):
        """
        This is used in templates, so we can 'annotate' as needed
        """
        return self.name

    def __str__(self):
        return self.display_name()


#
# Switches
#

class Switch(models.Model):
    """
    A Switch represents a piece of physical hardware. Each Switch is assigned a SwitchType.
    Switch names are required, and must be unique.

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    name = models.CharField(
        max_length=64,
        unique=True,
    )
    description = models.CharField(
        max_length=100,
        blank=True,
    )
    connector_type = models.PositiveSmallIntegerField(
        choices=CONNECTOR_TYPE_CHOICES,
        default=CONNECTOR_TYPE_SNMP,
        verbose_name='Connector Type',
        help_text='How we connect to this device.',
    )
    napalm_device_type = models.CharField(
        max_length=64,
        choices=NAPALM_DEVICE_TYPES,
        default='',
        blank=True,
        null=True,
        verbose_name='Napalm Device Type',
        help_text='The device type to use if Napalm connector is used.',
    )
    snmp_profile = models.ForeignKey(
        to='SnmpProfile',
        on_delete=models.SET_NULL,
        related_name='snmp_profile',
        blank=True,
        null=True,
        verbose_name='SNMP Profile',
        help_text='The SNMP Profile has all the settings to read/write data on the switch. Not used for Napalm.',
    )
    netmiko_profile = models.ForeignKey(
        to='NetmikoProfile',
        on_delete=models.SET_NULL,
        related_name='netmiko_profile',
        blank=True,
        null=True,
        verbose_name='Netmiko/SSH Profile',
        help_text='The Netmiko/SSH Profile has all the settings to access the switch via SSH for additional command access. Also used for Napalm connections.',
    )
    command_list = models.ForeignKey(
        to='CommandList',
        on_delete=models.SET_NULL,
        related_name='command_list',
        blank=True,
        null=True,
        help_text='This is the list of commands (if any) that can be executed on the switch. Requires a Netmike/SSH profile.',
    )
    command_templates = models.ManyToManyField(
        to='CommandTemplate',
        # see https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.ForeignKey.related_name
        related_name='command_templates',
        blank=True,     # we don't require to have them
        verbose_name='Assigned Command Templates',
        help_text="These are the command templates assigned. Users in a group this device belongs to "
                  "can run these command templates."
    )
    read_only = models.BooleanField(
        default=False,
        verbose_name='Read-Only access',
        help_text='The checked, this switch will be read-only.',
    )
    bulk_edit = models.BooleanField(
        default=True,
        verbose_name='Bulk-editing of interfaces',
        help_text='If Bulk Edit is set, we allow multiple interfaces on this switch to be edited at once.',
    )
    indent_level = models.SmallIntegerField(
        default=0,
        verbose_name='Indentation level',
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text='Tab indentation level, helps organize the switchgroup view.',
    )
    default_view = models.PositiveSmallIntegerField(
        choices=SWITCH_VIEW_CHOICES,
        default=SWITCH_VIEW_BASIC,
        verbose_name='Default View',
        help_text='Default view. Details shows Ethernet, ARP, LLDP immediately.',
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
    status = models.PositiveSmallIntegerField(
        choices=SWITCH_STATUS_CHOICES,
        default=SWITCH_STATUS_ACTIVE,
        verbose_name='Status',
    )
    primary_ip4 = models.CharField(
        max_length=64,
        # on_delete=models.SET_NULL,
        blank=True,
        null=True,
        unique=False,   # allow duplicates so we can enter same switch with different snmp profile
        verbose_name='Management IPv4',
        help_text='IPv4 address or hostname, can be duplicate as long as name is unique.',
    )
#    primary_ip6 = models.CharField(
#        max_length=64,
#        on_delete=models.SET_NULL,
#        blank=True,
#        null=True,
#        unique=False,   # we allow duplication, but combination of IP and SnmpProfile should be unique!
#        verbose_name='Management IPv6',
#    )
    comments = models.TextField(
        blank=True,
        help_text='Add any additional information about this switch.',
    )
    nms_id = models.CharField(
        max_length=64,
        # on_delete=models.SET_NULL,
        blank=True,
        null=True,
        unique=False,
        verbose_name='External NMS Id',
        help_text='ID or Label in an external Network Management System. To be used in admin-configurable links. See configuration.py',
    )
    # some fields that are set by the proper connector class:
    hostname = models.CharField(
        max_length=64,
        default='',
        blank=True,
        null=True,
        verbose_name='Hostname',
        help_text='The switch hostname as reported via snmp, ssh, etc.',
    )
    # dont_show_interfaces = models.BooleanField(
    #    default=False,
    #    verbose_name='Do NOT Show Interfaces',
    #    help_text='If checked, do not ever show interfaces of this device! Mostly useful for command-only devices!'
    # )
    snmp_oid = models.CharField(
        max_length=100,
        default='',
        blank=True,
        verbose_name='SNMP systemOID for this switch',
        help_text='The switch OID as reported via snmp.',
    )

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Switches'
        unique_together = [
            ['primary_ip4', 'snmp_profile'],
        ]

    def display_name(self):
        """
        This is used in templates, so we can 'annotate' as needed
        """
        return self.name

    def __str__(self):
        return self.display_name()

    # called from SwitchAdmin 'list_display':
    def get_switchgroups(self):
        return ",".join([str(g) for g in self.switchgroups.all()])

    def is_valid_command_id(self, command_id, is_staff=False):
        """
        Verify that a command_id is actually valid(ie assigned) to this device.
        Returns True or False.
        """
        # to be implemented!
        return True

    # this needs to be accessed from templates:
    @property
    def has_interface_commands(self):
        """
        Simple check to see if this device has been assigned interface commands.
        Requires valid NetMiko profile!
        Returns True or False.
        """
        if self.netmiko_profile and self.command_list:
            if self.command_list.interface_commands.count > 0 or \
               self.command_list.interface_commands_staff.count > 0:
                # Looks like we do!
                return True
        return False

    # this needs to be accessed from templates:
    @property
    def has_global_commands(self):
        """
        Simple check to see if this device has been assigned valid global commands.
        Requires valid NetMiko profile!
        Returns True or False.
        """
        if self.netmiko_profile and self.command_list:
            if self.command_list.global_commands.count > 0 or \
               self.command_list.global_commands_staff.count > 0:
                # Looks like we do!
                return True
        return False

    # basic validation
    # see also https://docs.djangoproject.com/en/2.2/ref/models/instances/#validating-objects
    def clean(self):
        # check if IPv4 address or hostname given is valid!
        if not is_valid_hostname_or_ip(self.primary_ip4):
            raise ValidationError('Invalid Management IPv4 address or hostname.')
        # if SNMP, we need snmp_profile
        if self.connector_type == CONNECTOR_TYPE_SNMP:
            if not self.snmp_profile:
                raise ValidationError('SNMP Connector needs an SNMP Profile!')

        elif self.connector_type == CONNECTOR_TYPE_NAPALM:
            if not self.napalm_device_type:
                raise ValidationError('Napalm Connector needs a Napalm device type!')
            if not self.netmiko_profile:
                raise ValidationError('Napalm Connector needs a Netmiko/SSH Profile!')

    # this needs to be accessed from templates:
    @property
    def primary_ip(self):
        if settings.PREFER_IPV4 and self.primary_ip4:
            return self.primary_ip4
        # elif self.primary_ip6:
        #    return self.primary_ip6
        elif self.primary_ip4:
            return self.primary_ip4
        else:
            return None


# this adds the switches to a group, with all other things needed
class SwitchGroup(models.Model):

    name = models.CharField(
        max_length=64,
        unique=True,
    )
    # display name allows us to override the group name
    # mostly useful for auto-created LDAP groups, that populate 'name, and may need to follow company policies,
    # and may not be "user friendly"
    display_name = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="Display name overrides the group name",
        help_text="Display name allows you to override the group name. "
                  "This is mostly useful for auto-created LDAP groups, that may not have 'display friendly' names."
    )
    description = models.CharField(
        max_length=120,
        blank=True,
        help_text="Description is shown when hovering over SwitchGroup in main menu."
    )
    # start with the relationship to the User object
    users = models.ManyToManyField(
        User,
        # see https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.ForeignKey.related_name
        related_name='switchgroups',      # from User object, we can now reference "User.switchgroups"
        blank=True,      # we don't require to have a vlan
        verbose_name='Group Users',
        help_text="Users add to this group have access to the switches in this group,"
                  " and the ports on the vlans in this group.",
    )
    # now add additional fields
    read_only = models.BooleanField(
        default=False,
        verbose_name='Read-Only access',
        help_text="If set, the switches in this group are read-only for all users."
    )
    bulk_edit = models.BooleanField(
        default=True,
        verbose_name='Bulk-editing of interfaces',
        help_text='If Bulk Edit is set, we can edit multiple interfaces at once on the switches in this group.',
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
    switches = models.ManyToManyField(
        to='Switch',
        # see https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.ForeignKey.related_name
        related_name='switchgroups',  # from switch object, we can now reference "Switch.switchgroups"
        # see https://docs.djangoproject.com/en/2.2/topics/db/models/#intermediary-manytomany
        # and https://www.revsys.com/tidbits/tips-using-djangos-manytomanyfield/
        through='SwitchGroupMembership',
        blank=True,      # we don't require to have a switch
        verbose_name='Member Switches',
        help_text="For all the switches in this group, group users can manage any "
                  "interface with a PVID in this list of VLANs. "
                  "Other interfaces can not be managed."
    )
    """
    Allow the above list of switches to be queried in proper sort order from templates
    """
    # @property
    # def sorted_switches(self):
    #    return self.switches.order_by("order")
    allow_all_vlans = models.BooleanField(
        default=False,
        verbose_name='Allow All Vlans',
        help_text='If set, allow access to all vlans.'
    )
    vlan_groups = models.ManyToManyField(
        to='VlanGroup',
        # see https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.ForeignKey.related_name
        related_name='vlangroups',
        blank=True,     # we don't require to have vlans from the start!
        verbose_name='Allowed VLAN Groups',
        help_text="For all the switches in this group, users in this group can "
                  "manage any interface with a PVID in these VLAN Groups. "
                  "Interfaces on VLANs not listed in these groups or "
                  "the individual vlans below cannot be managed.",
    )
    vlans = models.ManyToManyField(
        to='VLAN',
        # see https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.ForeignKey.related_name
        related_name='vlans',
        blank=True,     # we don't require to have vlans from the start!
        verbose_name='Allowed VLANs',
        help_text="For all the switches in this group, users in this group can "
                  "manage any interface with a PVID on these VLANs. "
                  "Interfaces on VLANs not listed here or in the Vlan Groups "
                  "above cannot be managed.",
    )
    comments = models.TextField(
        blank=True,
        help_text="Comment are for additional admin observations only, e.g. ticket #, notes about usage. etc."
                  "Comments are not shown in the user interface."
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Switch Group'
        verbose_name_plural = 'Switch Groups'

    def __str__(self):
        return self.name

    # called from SwitchGroupAdmin 'list_display':
    def get_switchgroup_users(self):
        return ",".join([str(u) for u in self.users.all()])


# needed classes for django-ordered-model:
class SwitchesManager(OrderedModelManager):
    pass


class SwitchGroupMembership(OrderedModel):
    switchgroup = models.ForeignKey(SwitchGroup, on_delete=models.CASCADE)
    switch = models.ForeignKey(Switch, on_delete=models.CASCADE)
    order_with_respect_to = 'switchgroup'
    objects = SwitchesManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        ordering = ('switchgroup', 'order')


#
# Activity Logging related
#
class Log(models.Model):
    """
    An ActivityLog entry respresent something that was done to a device,
    either a view/list, or a change.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    timestamp = models.DateTimeField(
        auto_now_add=True,  # set on save, do not allow changes in code.
        blank=True,
        null=True,
    )
    # see: https://docs.djangoproject.com/en/1.10/topics/auth/customizing/#referencing-the-user-model
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,  # we don't require to have a user
    )
    group = models.ForeignKey(
        to='SwitchGroup',
        on_delete=models.CASCADE,
        related_name='logs',
        blank=True,
        null=True,   # we don't require to have a group
    )
    switch = models.ForeignKey(
        to='Switch',
        on_delete=models.CASCADE,
        related_name='logs',
        blank=True,
        null=True,  # we don't require to have a switch
    )
    if_index = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='SNMP interface index',
    )
    if_name = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="Interface name",
    )
    ip_address = models.TextField(
        max_length=20,
        default='0.0.0.0',
        help_text='The user IP address that created the log entry',
    )
    """
    see constants.py for defined log values and their meanings
    """
    type = models.PositiveSmallIntegerField(
        choices=LOG_TYPE_CHOICES,
        default=LOG_TYPE_VIEW,
        verbose_name='Type of Log Entry',
    )
    action = models.PositiveSmallIntegerField(
        choices=LOG_ACTION_CHOICES,
        default=LOG_VIEW_SWITCH,
        verbose_name='Activity or Action to log',
    )
    description = models.TextField(
        blank=True, null=True,  # we don't require it, see save() where a default will be set
    )

    def save(self, *args, **kwargs):
        # set default description if none given
        if not self.description:
            # see if this is a valid action index:
            try:
                self.description = LOG_ACTION_CHOICES[self.action]
            except Exception:
                # not found (should not happen!)
                self.description = "Unknown action!"

        # here is the actual work of saving:
        # see https://docs.djangoproject.com/en/2.2/topics/db/models/#overriding-predefined-model-methods
        super().save(*args, **kwargs)

        # if requested, also sent to Syslog host
        if settings.SYSLOG_HOST:
            # we are defining a logger, and then check if it has a handler.
            # each time you create a named logger, python will add handler to existing,
            # even if you delete the object. this is a 'globally' defined logger in apps.py :
            syslogger = logging.getLogger('log_to_syslog')
            if not syslogger.hasHandlers():
                handler = logging.handlers.SysLogHandler(address=(settings.SYSLOG_HOST, settings.SYSLOG_PORT))
                syslogger.addHandler(handler)
            syslogger.setLevel(logging.DEBUG)
            if settings.SYSLOG_JSON:
                syslogger.info(self.as_json())
            else:
                syslogger.info(self.as_string())

    def as_string(self):
        """
        return all the details of this log entry as a string
        """
        info = 'OpenL2M Log: '
        if self.user:
            info += f'User={self.user.username}, '
        info += f'IP={self.ip_address}, Type={self.get_type_display()}, Action={self.get_action_display()}, '
        if self.switch:
            info = info + f"Switch={self.switch.name}, ifIndex={self.if_index}, Interface={self.if_name}, "
        info = info + f"Descr={self.description}"
        return info

    def as_json(self):
        """
        return all the details of this log entry as a JSON formatted string
        """
        log_dict = {}
        log_dict['application'] = f'OpenL2M v{settings.VERSION}'
        if self.user:
            log_dict['username'] = self.user.username
        log_dict['ip'] = self.ip_address
        log_dict['type_id'] = self.type
        log_dict['type'] = self.get_type_display()
        log_dict['action_id'] = self.action
        log_dict['action'] = self.get_action_display()
        if self.switch:
            log_dict['switch'] = self.switch.name
            log_dict['switch_id'] = self.switch.id
            if self.if_index:
                log_dict['if_index'] = self.if_index
            if self.if_name:
                log_dict['interface'] = self.if_name
        log_dict['description'] = self.description
        return json.dumps(log_dict)

    def display_name(self):
        """
        This is used in templates, so we can 'annotate' as needed
        """
        return f"{self.user}-{self.switch}-{self.get_action_display()}"

    def __str__(self):
        return self.display_name()

    class Meta:
        ordering = ['timestamp']
        verbose_name_plural = 'Activity Logs'


#
# Task model
#
class Task(models.Model):
    """
    A Task entry respresent information about a scheduled task or job,
    """
    created = models.DateTimeField(
        auto_now_add=True,  # set on save, do not allow changes in code.
        blank=True,
        null=True,
    )
    eta = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Estimated Time task will be started",
    )
    started = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last time task was started",
    )
    completed = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Time of completion",
    )
    email_result = models.BooleanField(
        default=True,
        verbose_name='Email results to user',
    )
    start_count = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Run Count',
        help_text="The number of times the task was started",
    )
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tasks',
        blank=True,
        null=True,  # we don't require to have a user
        help_text='The user who submitted the task',
    )
    group = models.ForeignKey(
        to='SwitchGroup',
        on_delete=models.CASCADE,
        related_name='tasks',
        blank=True,
        null=True,   # we don't require to have a group
    )
    switch = models.ForeignKey(
        to='Switch',
        on_delete=models.CASCADE,
        related_name='tasks',
        blank=True,
        null=True,  # we don't require to have a switch
    )
    type = models.PositiveSmallIntegerField(
        choices=TASK_TYPE_CHOICES,
        default=TASK_TYPE_NONE,
        verbose_name='Type of Task',
    )
    status = models.PositiveSmallIntegerField(
        choices=TASK_STATUS_CHOICES,
        default=TASK_STATUS_CREATED,
        verbose_name='Status of this task',
    )
    description = models.TextField(
        blank=True, null=True,  # description or comments about the task
    )
    arguments = models.TextField(
        blank=True,     # any parameters for this task, in JSON format
        null=True,
        help_text="Task arguments, in JSON format",
    )
    reverse_arguments = models.TextField(
        blank=True,     # the parameters to reverse the changes, in JSON format
        null=True,
        help_text="Arguments to undo the changes of this task, at submit time, in JSON format",
    )
    runtime_reverse_arguments = models.TextField(
        blank=True,     # the parameters to reverse the changes, stored right before the changes are applied, in JSON format
        null=True,
        help_text="Arguments to undo the changes of this task, just prior to task executing, in JSON format",
    )
    celery_task_id = models.TextField(
        blank=True,
        null=True,
        help_text='Celery task id returned when task is submitted'
    )
    results = models.TextField(
        blank=True,     # any results, in JSON format
        null=True,
        help_text="Task results, in JSON format",
    )

    def display_name(self):
        """
        This is used in templates, so we can 'annotate' as needed
        """
        return f"Task {self.id}: User {self.user.username} - Switch {self.switch.name} - {self.description}"

    def __str__(self):
        return self.display_name()

    class Meta:
        ordering = ['eta']
        verbose_name_plural = 'Scheduled Tasks'
