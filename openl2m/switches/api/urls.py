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

from switches.urls import InterfaceNameConvertor

from switches.api.views import (
    APISwitchMenuView,
    APISwitchBasicView,
    APISwitchDetailView,
    APISwitchSaveConfig,
    APISwitchVlanAdd,
    APISwitchVlanEdit,
    APISwitchVlanDelete,
    APIInterfaceSetVlan,
    APIInterfaceSetState,
    APIInterfaceSetPoE,
    APIInterfaceSetDescription,
)

app_name = 'switches-api'

register_converter(
    InterfaceNameConvertor,
    "ifname",
)

# api switch views
urlpatterns = [
    path(
        "",
        APISwitchMenuView.as_view(),
        name="api_switch_menu_view",
    ),
    path(
        "<int:group_id>/<int:switch_id>/basic/",
        APISwitchBasicView.as_view(),
        name="api_switch_basic_view",
    ),
    path(
        "<int:group_id>/<int:switch_id>/details/",
        APISwitchDetailView.as_view(),
        name="api_switch_detail_view",
    ),
    path(
        "<int:group_id>/<int:switch_id>/save/",
        APISwitchSaveConfig.as_view(),
        name="api_switch_save_config",
    ),
    path(
        "<int:group_id>/<int:switch_id>/vlan/add/",
        APISwitchVlanAdd.as_view(),
        name="api_switch_vlan_add",
    ),
    path(
        "<int:group_id>/<int:switch_id>/vlan/edit/",
        APISwitchVlanEdit.as_view(),
        name="api_switch_vlan_edit",
    ),
    path(
        "<int:group_id>/<int:switch_id>/vlan/delete/",
        APISwitchVlanDelete.as_view(),
        name="api_switch_vlan_delete",
    ),
    path(
        "<int:group_id>/<int:switch_id>/interface/<ifname:interface_id>/vlan/",
        APIInterfaceSetVlan.as_view(),
        name="api_interface_set_vlan",
    ),
    path(
        "<int:group_id>/<int:switch_id>/interface/<ifname:interface_id>/state/",
        APIInterfaceSetState.as_view(),
        name="api_interface_set_state",
    ),
    path(
        "<int:group_id>/<int:switch_id>/interface/<ifname:interface_id>/poe_state/",
        APIInterfaceSetPoE.as_view(),
        name="api_interface_set_poe_state",
    ),
    path(
        "<int:group_id>/<int:switch_id>/interface/<ifname:interface_id>/description/",
        APIInterfaceSetDescription.as_view(),
        name="api_interface_set_description",
    ),
]
