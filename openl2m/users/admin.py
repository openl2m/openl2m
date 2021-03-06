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
from django import forms

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.widgets import FilteredSelectMultiple

from .models import Profile
from switches.models import SwitchGroup

# pull in the custom admin site
from openl2m.admin import admin_site


# Define an inline admin descriptor for the Profile model
# so we can add it to the User admin view
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profile'


class SwitchGroupInline(admin.TabularInline):
    model = SwitchGroup.users.through


# Define a new User admin
class MyUserAdmin(UserAdmin):
    # add the Profile view
    inlines = (SwitchGroupInline, ProfileInline,)

    # this removes the object 'permissions' stuff
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',)}),
        (('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )


# we have a custom admin site, i.e. register with admin_site, not with default "admin.site"!
admin_site.register(User, MyUserAdmin)
