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
from django.conf import settings
from django.contrib.admin import AdminSite

# Create a custom Admin site.
# NOTE: User admin is registered in the users/ application!


class OpenL2MAdminSite(AdminSite):
    """
    Custom admin site
    """

    site_header = 'OpenL2M Administration'
    site_title = 'OpenL2M'
    site_url = f'/{settings.BASE_PATH}'


# create new admin site
admin_site = OpenL2MAdminSite(name='admin')
