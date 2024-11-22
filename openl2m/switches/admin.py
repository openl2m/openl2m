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
from django.contrib import admin
from django.contrib.admin.models import LogEntry, DELETION
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

# local copy of django-ordered-model, with some fixes:
# from libraries.django_ordered_model.ordered_model.admin import OrderedStackedInline, OrderedTabularInline, OrderedInlineModelAdminMixin
from ordered_model.admin import OrderedTabularInline, OrderedInlineModelAdminMixin

# Register your models here.
from switches.models import (
    Command,
    CommandList,
    CommandTemplate,
    Switch,
    SwitchGroup,
    SwitchGroupMembership,
    SnmpProfile,
    NetmikoProfile,
    VLAN,
    VlanGroup,
)

# register with the custom admin site
from openl2m.admin import admin_site

# See:
# https://docs.djangoproject.com/en/dev/ref/contrib/admin/#django.contrib.admin.ModelAdmin.filter_horizontal
#


# Change the Switch admin display to add the list of groups where this is used:
class SwitchInline(admin.TabularInline):
    model = SwitchGroup.switches.through
    verbose_name = 'Switch Group membership'
    verbose_name_plural = 'Switch Group memberships'


# Change the Switch admin page to show horizontal listing of selected Switch Groups:
# class SwitchAdmin(admin.StackedInline):
class SwitchAdmin(admin.ModelAdmin):
    save_on_top = True
    save_as = True
    list_display = ['name', 'access_count', 'last_accessed', 'change_count', 'last_changed', 'get_switchgroups']
    readonly_fields = (
        'hostname',
        'created',
        #        'modified',
        'last_accessed',
        'access_count',
        'last_changed',
        'change_count',
        'last_command_time',
        'command_count',
    )
    filter_horizontal = ('command_templates',)
    search_fields = ['name']
    inlines = (SwitchInline,)
    fieldsets = (
        (None, {'fields': ('name', 'description', 'primary_ip4')}),
        (
            'Connection Configuration',
            {
                'fields': (
                    'connector_type',
                    'snmp_profile',
                    'netmiko_profile',
                )
            },
        ),
        ('Napalm Options', {'fields': ('napalm_device_type',)}),
        (
            'Commands Configuration',
            {
                'fields': (
                    'command_list',
                    'command_templates',
                )
            },
        ),
        (
            'View Options',
            {
                'fields': (
                    'indent_level',
                    'default_view',
                )
            },
        ),
        (
            'Access Options',
            {
                'fields': (
                    'status',
                    'read_only',
                    'bulk_edit',
                    'allow_poe_toggle',
                    'edit_if_descr',
                )
            },
        ),
        ('Other Options', {'fields': ('nms_id',)}),
        ('Read-Only Fields', {'fields': ('hostname',)}),
        (
            'Stats',
            {
                'fields': (
                    'created',
                    #                    'modified',
                    'last_accessed',
                    'access_count',
                    'last_changed',
                    'change_count',
                    'last_command_time',
                    'command_count',
                )
            },
        ),
    )


# class SwitchGroupMembershipStackedInline(OrderedStackedInline):
class SwitchGroupMembershipStackedInline(OrderedTabularInline):
    model = SwitchGroupMembership
    fields = (
        'switch',
        'order',
        'move_up_down_links',
    )
    readonly_fields = (
        'order',
        'move_up_down_links',
    )
    extra = 1
    ordering = ('order',)
    verbose_name = 'Switch to Group'
    verbose_name_plural = 'Switch Group Memberships'


# Change the SwitchGroup admin page to show horizontal listing of selected items:
class SwitchGroupAdmin(OrderedInlineModelAdminMixin, admin.ModelAdmin):
    save_on_top = True
    save_as = True
    search_fields = ['name']
    filter_horizontal = ('users', 'vlan_groups', 'vlans')
    list_display = ['name', 'switch_count', 'get_switchgroup_users']
    # inlines = (SwitchGroupSwitchesThroughModelTabularInline, )
    inlines = (SwitchGroupMembershipStackedInline,)
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'name',
                    'display_name',
                    'description',
                )
            },
        ),
        (
            'Users in this group',
            {
                'fields': ('users',),
            },
        ),
        (
            'VLAN Allowances',
            {
                'fields': (
                    'allow_all_vlans',
                    'vlan_groups',
                    'vlans',
                ),
            },
        ),
        (
            'Other options',
            {
                'fields': (
                    'read_only',
                    'bulk_edit',
                    'allow_poe_toggle',
                    'edit_if_descr',
                    'comments',
                ),
            },
        ),
    )

    # return the number of Switch() objects that are used by a given SwitchGroup (obj)
    def switch_count(self, obj):
        return obj.switches.count()


# Change the VLAN() admin display to add the list of groups where this is used:
class VlanInline(admin.TabularInline):
    model = VlanGroup.vlans.through
    verbose_name = 'Vlan Group membership'
    verbose_name_plural = 'Vlan Group memberships'


class VlanSwitchInline(admin.TabularInline):
    model = SwitchGroup.vlans.through
    verbose_name = 'Switch Group membership'
    verbose_name_plural = 'Switch Group memberships'


# Change the VLAN() admin page to show horizontal listing of selected VLAN Groups:
class VLANAdmin(admin.ModelAdmin):
    save_on_top = True
    save_as = True
    search_fields = ['name', 'vid']
    # we just want all fields:
    # list_display = ['name', 'vid', 'description']
    list_display = ['name', 'use_count']
    inlines = (VlanInline, VlanSwitchInline)

    # return the number of VlanGroup() and SwitchGroups() objects that reference a given vlan (obj)
    def use_count(self, obj):
        return obj.vlangroups.count() + obj.vlans.count()


# Change the VlanGroup() admin display to add the list of groups where this is used:
class VlanGroupInline(admin.TabularInline):
    model = SwitchGroup.vlan_groups.through
    verbose_name = 'Vlan Group membership'
    verbose_name_plural = 'Vlan Group memberships'


# Change the VLAN admin page to show horizontal listing of selected VLAN Groups:
class VlanGroupAdmin(admin.ModelAdmin):
    save_on_top = True
    save_as = True
    search_fields = ['name']
    filter_horizontal = ('vlans',)
    # we just want all fields:
    # list_display = ['name', 'vid', 'description']
    list_display = ['name', 'use_count']
    inlines = (VlanGroupInline,)
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'name',
                    'description',
                )
            },
        ),
        (
            'VLANs Allowed',
            {
                'fields': ('vlans',),
            },
        ),
    )

    # return the number of SwitchGroups() objects that reference a given VlanGroup (obj)
    def use_count(self, obj):
        return obj.vlangroups.count()


class SnmpProfileAdmin(admin.ModelAdmin):
    save_on_top = True
    save_as = True
    search_fields = ['name']
    list_display = ['name', 'switch_count']
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'name',
                    'description',
                    'version',
                    'read_only',
                )
            },
        ),
        (
            'Version 2 options',
            {
                'fields': ('community',),
            },
        ),
        (
            'Version 3 options',
            {
                'fields': (
                    'sec_level',
                    'auth_protocol',
                    'username',
                    'passphrase',
                    'priv_protocol',
                    'priv_passphrase',
                    'context_name',
                    'context_engine_id',
                ),
            },
        ),
        (
            'Other options',
            {
                'fields': ('udp_port',),
            },
        ),
    )

    # return the number of switch() objects that reference a given snmp profile (obj)
    def switch_count(self, obj):
        return obj.snmp_profile.count()


class NetmikoProfileAdmin(admin.ModelAdmin):
    save_on_top = True
    save_as = True
    search_fields = ['name']
    list_display = ['name', 'switch_count']
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'name',
                    'description',
                ),
            },
        ),
        (
            'SSH/REST/API Account settings',
            {
                'fields': (
                    'username',
                    'password',
                ),
            },
        ),
        (
            'Netmiko/SSH Options',
            {
                'fields': (
                    'tcp_port',
                    'device_type',
                ),
            },
        ),
        (
            'Security Options',
            {
                'fields': ('verify_hostkey',),
            },
        ),
        (
            'Cisco-Specific Options',
            {
                'fields': ('enable_password',),
            },
        ),
    )

    # return the number of switch() objects that reference a given netmiko profile (obj)
    def switch_count(self, obj):
        return obj.netmiko_profile.count()


class CommandAdmin(admin.ModelAdmin):
    save_on_top = True
    save_as = True
    search_fields = ['name']
    list_display = ['name', 'os', 'command_list_count']

    # return the number of commandlist() objects that reference a given command (obj)
    # this can be in 4 difference ManyToManyField relationships:
    def command_list_count(self, obj):
        return (
            obj.global_commands.count()
            + obj.interface_commands.count()
            + obj.global_commands_staff.count()
            + obj.interface_commands_staff.count()
        )


class CommandListAdmin(admin.ModelAdmin):
    save_on_top = True
    save_as = True
    search_fields = ['name']
    list_display = ['name', 'switch_count']
    filter_horizontal = (
        'global_commands',
        'interface_commands',
        'global_commands_staff',
        'interface_commands_staff',
    )
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'name',
                    'description',
                )
            },
        ),
        (
            'Global System Commands',
            {
                'fields': (
                    'global_commands',
                    'global_commands_staff',
                ),
            },
        ),
        (
            'Interface Level Commands',
            {
                'fields': (
                    'interface_commands',
                    'interface_commands_staff',
                ),
            },
        ),
    )

    # return the number of switch() objects that reference a given command list (obj)
    def switch_count(self, obj):
        return obj.command_list.count()


class CommandTemplateAdmin(admin.ModelAdmin):
    save_on_top = True
    save_as = True
    search_fields = ['name']
    list_display = ['name', 'switch_count']
    fieldsets = (
        (None, {'fields': ('name', 'os', 'description', 'template')}),
        (
            'Output Matching',
            {
                'fields': ('output_match_regex', 'output_match_text', 'output_fail_text', 'output_lines_keep_regex'),
            },
        ),
        (
            'Field 1 (free form)',
            {
                'fields': ('field1_name', 'field1_description', 'field1_regex'),
            },
        ),
        (
            'Field 2 (free form)',
            {
                'fields': ('field2_name', 'field2_description', 'field2_regex'),
            },
        ),
        (
            'Field 3 (free form)',
            {
                'fields': ('field3_name', 'field3_description', 'field3_regex'),
            },
        ),
        (
            'Field 4 (free form)',
            {
                'fields': ('field4_name', 'field4_description', 'field4_regex'),
            },
        ),
        (
            'Field 5 (free form)',
            {
                'fields': ('field5_name', 'field5_description', 'field5_regex'),
            },
        ),
        (
            'Field 6 (free form)',
            {
                'fields': ('field6_name', 'field6_description', 'field6_regex'),
            },
        ),
        (
            'Field 7 (free form)',
            {
                'fields': ('field7_name', 'field7_description', 'field7_regex'),
            },
        ),
        (
            'Field 8 (free form)',
            {
                'fields': ('field8_name', 'field8_description', 'field8_regex'),
            },
        ),
        (
            'List 1',
            {
                'fields': ('list1_name', 'list1_description', 'list1_values'),
            },
        ),
        (
            'List 2',
            {
                'fields': ('list2_name', 'list2_description', 'list2_values'),
            },
        ),
        (
            'List 3',
            {
                'fields': ('list3_name', 'list3_description', 'list3_values'),
            },
        ),
        (
            'List 4',
            {
                'fields': ('list4_name', 'list4_description', 'list4_values'),
            },
        ),
    )

    # return the number of switch() objects that reference a given command template (obj)
    def switch_count(self, obj):
        return obj.command_templates.count()


# add a class to show the built-in admin pages LogEntry objects:
class LogEntryAdmin(admin.ModelAdmin):
    # to have a date-based drilldown navigation in the admin page
    date_hierarchy = 'action_time'

    # to filter the resultes by users, content types and action flags
    list_filter = ['user', 'content_type', 'action_flag']

    # when searching the user will be able to search in both object_repr and change_message
    search_fields = ['object_repr', 'change_message']

    list_display = [
        'action_time',
        'user',
        'content_type',
        'object_repr',
        'action_flag',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def object_link(self, obj):
        if obj.action_flag == DELETION:
            link = escape(obj.object_repr)
        else:
            ct = obj.content_type
            link = '<a href="%s">%s</a>' % (
                reverse('admin:%s_%s_change' % (ct.app_label, ct.model), args=[obj.object_id]),
                escape(obj.object_repr),
            )
        return mark_safe(link)


# Register your models here.
admin_site.register(Switch, SwitchAdmin)
admin_site.register(SwitchGroup, SwitchGroupAdmin)
admin_site.register(VLAN, VLANAdmin)
admin_site.register(VlanGroup, VlanGroupAdmin)
admin_site.register(SnmpProfile, SnmpProfileAdmin)
admin_site.register(NetmikoProfile, NetmikoProfileAdmin)
admin_site.register(Command, CommandAdmin)
admin_site.register(CommandList, CommandListAdmin)
admin_site.register(CommandTemplate, CommandTemplateAdmin)
admin_site.register(LogEntry, LogEntryAdmin)
