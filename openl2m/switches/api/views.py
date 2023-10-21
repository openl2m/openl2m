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

#
# Here we implement all API views as classes
#

from django.conf import settings

# Use the Django Rest Framework:
from rest_framework.authentication import (
    SessionAuthentication,
    BasicAuthentication,
    TokenAuthentication,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from switches.views import confirm_access_rights
from switches.connect.connect import get_connection_object

API_VERSION = 1

"""
This class gets all information from a switch about its Interfaces
"""
api_info = {
    'version': API_VERSION,
    'openl2m_version': settings.VERSION,
}


class APISwitchBasicView(
    APIView,
):
    """
    Return the basic information for a device. This includes all interfaces.
    To save time we do NOT include mac-address, lldp, poe and other details.
    """

    authentication_classes = [
        TokenAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(
        self,
        request,
        group_id,
        switch_id,
    ):
        group, switch = confirm_access_rights(
            request=request,
            group_id=group_id,
            switch_id=switch_id,
        )
        conn, response_error = get_connection_switch(request=request, group=group, switch=switch)
        if response_error:
            return response_error
        data = {
            "switch": conn.as_dict(),
            "interfaces": None,
        }
        interfaces = list()
        for key, iface in conn.interfaces.items():
            interfaces.append(iface.as_dict())
        data["interfaces"] = interfaces
        return Response(
            data=data,
            status=status.HTTP_200_OK,
        )


#        return Response(
#            data=data,
#            status=status.HTTP_404_NOT_FOUND,
#        )


class APISwitchDetailView(
    APIView,
):
    """
    Return the full information for a device. This includes all interfaces,
    with mac-address, lldp, poe and other details.
    """

    authentication_classes = [
        TokenAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def get(
        self,
        request,
        group_id,
        switch_id,
    ):
        group, switch = confirm_access_rights(
            request=request,
            group_id=group_id,
            switch_id=switch_id,
        )
        conn, response_error = get_connection_switch(request=request, group=group, switch=switch, details=True)
        if response_error:
            return response_error
        data = {
            "switch": conn.as_dict(),
            "interfaces": None,
        }
        interfaces = list()
        for key, iface in conn.interfaces.items():
            interfaces.append(iface.as_dict())
        data["interfaces"] = interfaces
        return Response(
            data=data,
            status=status.HTTP_200_OK,
        )


#        return Response(
#            data=data,
#            status=status.HTTP_404_NOT_FOUND,
#        )


class APIInterfaceSetState(
    APIView,
):
    """
    Set the admin state of the selected interface.
    """

    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def post(
        self,
        request,
        group_id,
        switch_id,
        interface_id,
        state,
    ):
        group, switch = confirm_access_rights(
            request=request,
            group_id=group_id,
            switch_id=switch_id,
        )
        if interface_name:
            conn, response_error = get_connection_switch(request=request, group=group, switch=switch)
            if response_error:
                return response_error
            # TODO: now here we need to parse the incoming data to actually change the state of the interface.


class APIInterfaceSetVlan(
    APIView,
):
    """
    Set the untagged VLAN for an interface.
    """

    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def post(
        self,
        request,
        group_id,
        switch_id,
        interface_id,
        vlan,
    ):
        group, switch = confirm_access_rights(
            request=request,
            group_id=group_id,
            switch_id=switch_id,
        )
        conn, response_error = get_connection_switch(request=request, group=group, switch=switch)
        if response_error:
            return response_error
        # TODO: here we need to parse all information and validate the information so that we can do a bulk update for the interface


class APIInterfaceSetPoE(
    APIView,
):
    """
    Set the PoE state of an interface.
    """

    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def post(
        self,
        request,
        group_id,
        switch_id,
        interface_id,
        poe_state,
    ):
        group, switch = confirm_access_rights(
            request=request,
            group_id=group_id,
            switch_id=switch_id,
        )
        if interface_name:
            conn, response_error = get_connection_switch(request=request, group=group, switch=switch)
            if response_error:
                return response_error
            # TODO: now here we need to parse the incoming data to actually change the state of the interface.


class APIInterfaceSetDescription(
    APIView,
):
    """
    Set the description for the selected interface.
    """

    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def post(
        self,
        request,
        group_id,
        switch_id,
        interface_id,
        description,
    ):
        group, switch = confirm_access_rights(
            request=request,
            group_id=group_id,
            switch_id=switch_id,
        )
        if interface_name:
            conn, response_error = get_connection_switch(request=request, group=group, switch=switch)
            if response_error:
                return response_error
            # TODO: now here we need to parse the incoming data to actually change the state of the interface.


class APISwitchAddVlan(
    APIView,
):
    """
    Add a VLAN to a switch.
    """

    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [
        IsAuthenticated,
    ]

    def post(
        self,
        request,
        group_id,
        switch_id,
        vlan_id,
        vlan_name,
    ):
        group, switch = confirm_access_rights(
            request=request,
            group_id=group_id,
            switch_id=switch_id,
        )
        conn, response_error = get_connection_switch(request=request, group=group, switch=switch)
        if response_error:
            return response_error
        # TODO: here we need to parse all information and validate the information so that we can do a bulk update for the interface


"""
This function is used to return us a conn object for requests to switches.
Again it's useful in deduplication.
"""


def get_connection_switch(request, group, switch, details=False):
    response_error = None
    try:
        conn = get_connection_object(request, group, switch)
    except ConnectionError as e:
        error = f"The following ConnectionError occured: {e}"
        dprint(error)

        response_error = Response(
            data=error,
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        if not conn.get_basic_info():
            error = "ERROR in get_basic_switch_info()"
            dprint(error)
        if details and not conn.get_client_data():
            error = "ERROR in get_client_data()"
            dprint(error)
    except Exception as e:
        error = f"Exception for get switch info: {e}"
        dprint(error)
        response_error = Response(
            data=error,
            status=status.HTTP_400_BAD_REQUEST,
        )
    conn.save_cache()
    return conn, response_error
