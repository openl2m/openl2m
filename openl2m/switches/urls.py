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
from django.conf.urls import url

from . import views

app_name = 'switches'
urlpatterns = [
    path('', views.switches, name='groups'),
    path(r'activity', views.admin_activity, name='admin_activity'),
    path(r'stats', views.show_stats, name='show_stats'),
    path(r'tasks', views.tasks, name='tasks'),
    path(r'tasks/details/<int:task_id>/', views.task_details, name='task_details'),
    path(r'tasks/delete/<int:task_id>/', views.task_delete, name='task_delete'),
    path(r'tasks/terminate/<int:task_id>/', views.task_terminate, name='task_terminate'),

    path('<int:group_id>/<int:switch_id>/', views.switch_basics, name='switch_basics'),
    path('<int:group_id>/<int:switch_id>/activity/', views.switch_activity, name='switch_activity'),
    path('<int:group_id>/<int:switch_id>/bulkedit/', views.switch_bulkedit, name='switch_bulkedit'),
    path('<int:group_id>/<int:switch_id>/bulkedit_task/', views.switch_bulkedit_task, name='switch_bulkedit_task'),
    path('<int:group_id>/<int:switch_id>/command/', views.switch_cmd_output, name='switch_cmd_output'),
    path('<int:group_id>/<int:switch_id>/details/', views.switch_arp_lldp, name='switch_arp_lldp'),
    path('<int:group_id>/<int:switch_id>/hwinfo/', views.switch_hw_info, name='switch_hw_info'),
    path('<int:group_id>/<int:switch_id>/reload/<str:view>/', views.switch_reload, name='switch_reload'),
    path('<int:group_id>/<int:switch_id>/save/<str:view>/', views.switch_save_config, name='switch_save_config'),

    path('<int:group_id>/<int:switch_id>/<int:interface_id>/admin/<int:new_state>/', views.interface_admin_change, name='admin_change'),
    path('<int:group_id>/<int:switch_id>/<int:interface_id>/newalias/', views.interface_alias_change, name='alias_change'),
    path('<int:group_id>/<int:switch_id>/<int:interface_id>/newpvid/', views.interface_pvid_change, name='pvid_change'),
    path('<int:group_id>/<int:switch_id>/<int:interface_id>/poe/<int:new_state>/', views.interface_poe_change, name='poe_change'),
    path('<int:group_id>/<int:switch_id>/<int:interface_id>/poetoggle/', views.interface_poe_down_up, name='poe_down_up'),
    path('<int:group_id>/<int:switch_id>/<int:interface_id>/command/', views.interface_cmd_output, name='interface_cmd_output'),
]
