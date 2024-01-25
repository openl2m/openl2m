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


class InterfaceNameConvertor:
    # convertor class to make sure interface names follow url-safe formats
    regex = "[a-zA-Z0-9\/_\-]*"  # regex entry is required, but not used here!

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
    path(
        '',
        views.Switches.as_view(),
        name='groups',
    ),
    path(
        'search',
        views.SwitchSearch.as_view(),
        name='switch_search',
    ),
    path(
        'activity',
        views.SwitchAdminActivity.as_view(),
        name='admin_activity',
    ),
    path(
        'stats',
        views.ShowStats.as_view(),
        name='show_stats',
    ),
    path(
        '<int:group_id>/<int:switch_id>/',
        views.SwitchBasics.as_view(),
        name='switch_basics',
    ),
    path(
        '<int:group_id>/<int:switch_id>/activity/',
        views.SwitchActivity.as_view(),
        name='switch_activity',
    ),
    path(
        '<int:group_id>/<int:switch_id>/bulkedit/',
        views.SwitchBulkEdit.as_view(),
        name='switch_bulkedit',
    ),
    path(
        '<int:group_id>/<int:switch_id>/vlan_manage/',
        views.SwitchVlanManage.as_view(),
        name='switch_vlan_manage',
    ),
    path(
        '<int:group_id>/<int:switch_id>/command/',
        views.SwitchCmdOutput.as_view(),
        name='switch_cmd_output',
    ),
    path(
        '<int:group_id>/<int:switch_id>/command_template/',
        views.SwitchCmdTemplateOutput.as_view(),
        name='switch_cmd_template_output',
    ),
    path(
        '<int:group_id>/<int:switch_id>/details/',
        views.SwitchDetails.as_view(),
        name='switch_arp_lldp',
    ),
    path(
        '<int:group_id>/<int:switch_id>/hwinfo/',
        views.SwitchHardwareInfo.as_view(),
        name='switch_hw_info',
    ),
    path(
        '<int:group_id>/<int:switch_id>/reload/<str:view>/',
        views.SwitchReload.as_view(),
        name='switch_reload',
    ),
    path(
        '<int:group_id>/<int:switch_id>/save/',
        views.SwitchSaveConfig.as_view(),
        name='switch_save_config',
    ),
    path(
        '<int:group_id>/<int:switch_id>/download_ethernet/',
        views.SwitchDownloadEthernetAndNeighbors.as_view(),
        name='switch_download_ethernet_neighbors',
    ),
    path(
        '<int:group_id>/<int:switch_id>/download_interfaces/',
        views.SwitchDownloadInterfaces.as_view(),
        name='switch_download_interfaces',
    ),
    path(
        '<int:group_id>/<int:switch_id>/<ifname:interface_name>/admin/<int:new_state>/',
        views.InterfaceAdminChange.as_view(),
        name='admin_change',
    ),
    path(
        '<int:group_id>/<int:switch_id>/<ifname:interface_name>/newdescription/',
        views.InterfaceDescriptionChange.as_view(),
        name='description_change',
    ),
    path(
        '<int:group_id>/<int:switch_id>/<ifname:interface_name>/newpvid/',
        views.InterfacePvidChange.as_view(),
        name='pvid_change',
    ),
    path(
        '<int:group_id>/<int:switch_id>/<ifname:interface_name>/poe/<int:new_state>/',
        views.InterfacePoeChange.as_view(),
        name='poe_change',
    ),
    path(
        '<int:group_id>/<int:switch_id>/<ifname:interface_name>/poetoggle/',
        views.InterfacePoeDownUp.as_view(),
        name='poe_down_up',
    ),
    path(
        '<int:group_id>/<int:switch_id>/<ifname:interface_name>/command/',
        views.InterfaceCmdOutput.as_view(),
        name='interface_cmd_output',
    ),
]
