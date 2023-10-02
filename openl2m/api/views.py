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
import sys
import os
import distro
import time
import datetime
import traceback
import re

import django
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.urls import reverse
from django.utils.html import mark_safe
from django.utils import timezone
from django.core.paginator import Paginator
from django.shortcuts import redirect, get_object_or_404, render
from django.template import Template, Context

from switches.connect.classes import Error
from switches.models import (
    SnmpProfile,
    NetmikoProfile,
    Command,
    CommandList,
    CommandTemplate,
    VLAN,
    VlanGroup,
    Switch,
    SwitchGroup,
    Log,
)
from switches.constants import (
    LOG_TYPE_VIEW,
    LOG_TYPE_CHANGE,
    LOG_TYPE_ERROR,
    LOG_TYPE_COMMAND,
    LOG_TYPE_CHOICES,
    LOG_ACTION_CHOICES,
    LOG_CHANGE_INTERFACE_DOWN,
    LOG_CHANGE_INTERFACE_UP,
    LOG_CHANGE_INTERFACE_POE_DOWN,
    LOG_CHANGE_INTERFACE_POE_UP,
    LOG_CHANGE_INTERFACE_POE_TOGGLE_DOWN_UP,
    LOG_CHANGE_INTERFACE_PVID,
    LOG_CHANGE_INTERFACE_ALIAS,
    LOG_CHANGE_BULK_EDIT,
    LOG_VIEW_SWITCHGROUPS,
    LOG_CONNECTION_ERROR,
    LOG_BULK_EDIT_TASK_START,
    LOG_VIEW_SWITCH,
    LOG_VIEW_ALL_LOGS,
    LOG_VIEW_ADMIN_STATS,
    LOG_VIEW_SWITCH_SEARCH,
    LOG_EXECUTE_COMMAND,
    LOG_SAVE_SWITCH,
    LOG_RELOAD_SWITCH,
    INTERFACE_STATUS_NONE,
    BULKEDIT_POE_NONE,
    BULKEDIT_POE_CHOICES,
    BULKEDIT_ALIAS_TYPE_CHOICES,
    BULKEDIT_INTERFACE_CHOICES,
    BULKEDIT_ALIAS_TYPE_REPLACE,
    BULKEDIT_ALIAS_TYPE_APPEND,
    BULKEDIT_POE_DOWN_UP,
    BULKEDIT_POE_CHANGE,
    BULKEDIT_POE_DOWN,
    BULKEDIT_POE_UP,
    SWITCH_STATUS_ACTIVE,
    LOG_TYPE_WARNING,
    INTERFACE_STATUS_CHANGE,
    INTERFACE_STATUS_DOWN,
    INTERFACE_STATUS_UP,
    LOG_VLAN_CREATE,
    LOG_VLAN_EDIT,
    LOG_VLAN_DELETE,
)
from switches.connect.connector import clear_switch_cache
from switches.connect.connect import get_connection_object
from switches.connect.constants import (
    POE_PORT_ADMIN_ENABLED,
    POE_PORT_ADMIN_DISABLED,
)
from switches.utils import (
    success_page,
    warning_page,
    error_page,
    dprint,
    get_from_http_session,
    save_to_http_session,
    get_remote_ip,
    time_duration,
    string_contains_regex,
    string_matches_regex,
    get_choice_name,
)
from switches.views import (
    rights_to_group_and_switch,
    user_can_access_task,
)
from users.utils import user_can_bulkedit, user_can_edit_vlans, get_current_users
from counters.models import Counter, counter_increment
from counters.constants import (
    COUNTER_CHANGES,
    COUNTER_BULKEDITS,
    COUNTER_ERRORS,
    COUNTER_ACCESS_DENIED,
    COUNTER_COMMANDS,
    COUNTER_VIEWS,
    COUNTER_DETAILVIEWS,
    COUNTER_HWINFO,
    COUNTER_VLAN_MANAGE,
)
from notices.models import Notice

# rest_framework
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class ApiBasicsView(TemplateView):
    template_name = "api_base.html"
    """
    Return all possible api views 
    """


class InterfaceArpView(APIView):
    """
    Return the ARP Information for an interface if there is any to return
    All Interfaces should be integer
    """

    def get(
        self,
        request,
        group_id,
        switch_id,
        interface_name="",
    ):
        group = get_object_or_404(SwitchGroup, pk=group_id)
        switch = get_object_or_404(Switch, pk=switch_id)
        if not rights_to_group_and_switch(
            request=request, group_id=group_id, switch_id=switch_id
        ):
            error = Error()
            error.description = "Access denied!"
            error.details = "You do not have access to this device!"
            return error_page(request=request, group=False, switch=False, error=error)
        try:
            conn = get_connection_object(request, group, switch)
        except ConnectionError as e:
            error = f"The following ConnectionError: {e} occurred."
            print(error)
            raise Http404
        try:
            if not conn.get_basic_info():
                error = "ERROR in get_basic_switch_info()"
                print(error)
            if not conn.get_client_data():
                error = "ERROR in get_client_data()"
                print(error)
        except Exception as e:
            error = "Exception for get switch info"
            print(error)
            raise Http404
        conn.save_cache()
        data = {
            "connection": conn,
        }
        print(data)
        for key, iface in conn.interfaces.items:
            print(key)
            print(iface)
        # Here we parse the data for the correct return values
        try:
            if conn.interfaces.items[int(interface_name)]:
                data["interface"] = int(interface_name)
                data["mac-address"] = conn.interfaces.items[int(interface_name)]
        except Exception as e:
            error = "ERROR in parsing for interface"
            print(error)
            raise Http404
        return Response(data=data)
