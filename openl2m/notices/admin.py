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

from django.contrib import admin

# pull in the custom admin site
from openl2m.admin import admin_site

from .models import Notice


# we have a custom admin site, i.e. register with admin_site, not with default "admin.site"!
class NoticeAdmin(admin.ModelAdmin):
    save_on_top = True
    search_fields = ['title']
    # fields to list in admin view:
    list_display = ('title', 'start_time', 'end_time', 'enabled')


admin_site.register(Notice, NoticeAdmin)
