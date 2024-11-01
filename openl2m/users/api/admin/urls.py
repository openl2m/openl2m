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
from django.urls import path

from users.api.admin.views import APIAdminUsers, APIAdminUserDetail

app_name = 'api-admin-users'

urlpatterns = [
    # api token path @post only
    path("", APIAdminUsers.as_view(), name="api-admin-users"),
    path("<int:pk>/", APIAdminUserDetail.as_view(), name="api-admin-user-detail"),
]
