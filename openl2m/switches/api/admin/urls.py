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

from switches.api.admin.views import (
    APIAdminSwitches,
    APIAdminSwitchDetail,
    APIAdminNetmikoProfiles,
    APIAdminNetmikoProfileDetail,
    APIAdminSnmpProfiles,
    APIAdminSnmpProfileDetail,
    APIAdminSwitchGroups,
    APIAdminSwitchGroupDetail,
)

app_name = 'api-admin-switches'

urlpatterns = [
    # api token path @post only
    path("", APIAdminSwitches.as_view(), name="api-admin-switches"),
    path("<int:pk>/", APIAdminSwitchDetail.as_view(), name="api-admin-switch-detail"),
    path("netmikoprofiles/", APIAdminNetmikoProfiles.as_view(), name="api-admin-credentials"),
    path("netmikoprofiles/<int:pk>/", APIAdminNetmikoProfileDetail.as_view(), name="api-admin-credential-detail"),
    path("snmpprofiles/", APIAdminSnmpProfiles.as_view(), name="api-admin-snmp-profiles"),
    path("snmpprofiles/<int:pk>/", APIAdminSnmpProfileDetail.as_view(), name="api-admin-snmp-profile-detail"),
    path("switchgroups/", APIAdminSwitchGroups.as_view(), name="api-admin-switchgroups"),
    path("switchgroups/<int:pk>/", APIAdminSwitchGroupDetail.as_view(), name="api-admin-switchgroup-detail"),
]
