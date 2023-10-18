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
from django.urls import path, register_converter

# from django.conf.urls import url

from switches import views
from switches.views import (
    APISwitchDetailView,
    APISwitchSpeedView,
    APISwitchArpView,
    APISwitchStateView,
    APISwitchVlanView,
    APIInterfaceDetailView,
    APIInterfaceSpeedView,
    APIInterfaceArpView,
    APIInterfaceStateView,
    APIInterfaceVlanView,
    APIObtainAuthToken,
)


class InterfaceNameConvertor:
    # convertor class to make sure interface names follow url-safe formats
    regex = "[a-zA-Z0-9\/_\-]*"

    def to_python(self, value):
        # replace _ with /
        return value.replace("_", "/")

    def to_url(self, value):
        # replace / with _
        return value.replace("/", "_")


register_converter(
    InterfaceNameConvertor,
    "ifname",
)

app_name = "switches"
urlpatterns = [
    path('', views.switches, name='groups'),
    path(r'search', views.switch_search, name='switch_search'),
    path(r'activity', views.admin_activity, name='admin_activity'),
    path(r'stats', views.show_stats, name='show_stats'),
    path('<int:group_id>/<int:switch_id>/', views.switch_basics, name='switch_basics'),
    path('<int:group_id>/<int:switch_id>/activity/', views.switch_activity, name='switch_activity'),
    path('<int:group_id>/<int:switch_id>/bulkedit/', views.switch_bulkedit, name='switch_bulkedit'),
    path('<int:group_id>/<int:switch_id>/vlan_manage/', views.switch_vlan_manage, name='switch_vlan_manage'),
    path('<int:group_id>/<int:switch_id>/command/', views.switch_cmd_output, name='switch_cmd_output'),
    path(
        '<int:group_id>/<int:switch_id>/command_template/',
        views.switch_cmd_template_output,
        name='switch_cmd_template_output',
    ),
    path('<int:group_id>/<int:switch_id>/details/', views.switch_arp_lldp, name='switch_arp_lldp'),
    path('<int:group_id>/<int:switch_id>/hwinfo/', views.switch_hw_info, name='switch_hw_info'),
    path('<int:group_id>/<int:switch_id>/reload/<str:view>/', views.switch_reload, name='switch_reload'),
    path('<int:group_id>/<int:switch_id>/save/<str:view>/', views.switch_save_config, name='switch_save_config'),
    path(
        '<int:group_id>/<int:switch_id>/<ifname:interface_name>/admin/<int:new_state>/',
        views.interface_admin_change,
        name='admin_change',
    ),
    path(
        '<int:group_id>/<int:switch_id>/<ifname:interface_name>/newdescription/',
        views.interface_description_change,
        name='description_change',
    ),
    path(
        '<int:group_id>/<int:switch_id>/<ifname:interface_name>/newpvid/',
        views.interface_pvid_change,
        name='pvid_change',
    ),
    path(
        '<int:group_id>/<int:switch_id>/<ifname:interface_name>/poe/<int:new_state>/',
        views.interface_poe_change,
        name='poe_change',
    ),
    path(
        '<int:group_id>/<int:switch_id>/<ifname:interface_name>/poetoggle/',
        views.interface_poe_down_up,
        name='poe_down_up',
    ),
    path(
        '<int:group_id>/<int:switch_id>/<ifname:interface_name>/command/',
        views.interface_cmd_output,
        name='interface_cmd_output',
    ),
    # api switch views
    path(
        "api/details/<int:group_id>/<int:switch_id>/",
        APISwitchDetailView.as_view(),
        name="api_interface_detail_view",
    ),
    path(
        "api/speed/<int:group_id>/<int:switch_id>/",
        APISwitchSpeedView.as_view(),
        name="api_interface_detail_view",
    ),
    path(
        "api/arp/<int:group_id>/<int:switch_id>/",
        APISwitchArpView.as_view(),
        name="api_interface_detail_view",
    ),
    path(
        "api/vlan/<int:group_id>/<int:switch_id>/",
        APISwitchVlanView.as_view(),
        name="api_interface_detail_view",
    ),
    path(
        "api/state/<int:group_id>/<int:switch_id>/",
        APISwitchStateView.as_view(),
        name="api_interface_detail_view",
    ),
    # api interface views
    path(
        "api/details/<int:group_id>/<int:switch_id>/<ifname:interface_name>/",
        APIInterfaceDetailView.as_view(),
        name="api_interface_detail_view",
    ),
    path(
        "api/speed/<int:group_id>/<int:switch_id>/<ifname:interface_name>/",
        APIInterfaceSpeedView.as_view(),
        name="api_interface_detail_view",
    ),
    path(
        "api/arp/<int:group_id>/<int:switch_id>/<ifname:interface_name>/",
        APIInterfaceArpView.as_view(),
        name="api_interface_detail_view",
    ),
    path(
        "api/vlan/<int:group_id>/<int:switch_id>/<ifname:interface_name>/",
        APIInterfaceVlanView.as_view(),
        name="api_interface_detail_view",
    ),
    path(
        "api/state/<int:group_id>/<int:switch_id>/<ifname:interface_name>/",
        APIInterfaceStateView.as_view(),
        name="api_interface_detail_view",
    ),
    # api token path @post only
    path(
        "api/token/",
        APIObtainAuthToken.as_view(),
        name="api_get_token_for_user",
    ),
]
