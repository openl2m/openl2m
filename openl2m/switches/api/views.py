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

# Use the Django Rest Framework:
from rest_framework import status as http_status
from rest_framework.response import Response
from rest_framework.reverse import reverse as rest_reverse
from rest_framework.views import APIView

from switches.actions import (
    perform_interface_description_change,
    perform_interface_admin_change,
    perform_interface_pvid_change,
    perform_interface_poe_change,
    perform_switch_save_config,
    perform_switch_vlan_add,
    perform_switch_vlan_edit,
    perform_switch_vlan_delete,
)
from switches.connect.connect import get_connection_object
from switches.permissions import get_my_device_groups, get_group_and_switch
from switches.utils import dprint

on_values = ["on", "yes", "y", "enabled", "enable", "true", "1"]


class APISwitchMenuView(
    APIView,
):
    """
    Return the groups and devices we have access to.
    """

    def get(
        self,
        request,
    ):
        dprint(f"APISwitchMenuView(): user={request.user.username}, auth={request.auth}")

        groups = get_my_device_groups(request=request)
        user = {
            "name": request.user.username,
            "read_only": request.user.profile.read_only,
            "vlan_edit": request.user.profile.vlan_edit,
            "allow_poe_toggle": request.user.profile.allow_poe_toggle,
            "edit_if_descr": request.user.profile.edit_if_descr,
        }
        data = {
            "user": user,
            'groups': groups,
        }
        return Response(
            data=data,
            status=http_status.HTTP_200_OK,
        )


def switch_info(request, group_id, switch_id, details):
    connection, response_error = get_connection_to_switch(
        request=request, group_id=group_id, switch_id=switch_id, details=details
    )
    if response_error:
        return response_error
    data = {
        "switch": connection.as_dict(),
        "vlans": connection.vlans_as_dict(),
    }
    interfaces = list()
    for key, iface in connection.interfaces.items():
        if not iface.visible:  # only return interfaces visible to this user!
            continue
        # append this interface data to the list of interfaces:
        interfaces.append(iface.as_dict())
    # add to return data:
    data["interfaces"] = interfaces
    connection.save_cache()  # this only works for SessionAuthentication !
    return Response(
        data=data,
        status=http_status.HTTP_200_OK,
    )


class APISwitchBasicView(
    APIView,
):
    """
    Return the basic information for a device. This includes all interfaces.
    To save time we do NOT include mac-address, lldp, poe and other details.
    """

    def get(
        self,
        request,
        group_id,
        switch_id,
    ):
        return switch_info(request=request, group_id=group_id, switch_id=switch_id, details=False)


class APISwitchDetailsView(
    APIView,
):
    """
    Return the full information for a device. This includes all interfaces,
    with mac-address, lldp, poe and other details.
    """

    def get(
        self,
        request,
        group_id,
        switch_id,
    ):
        return switch_info(request=request, group_id=group_id, switch_id=switch_id, details=True)


class APISwitchSaveConfig(
    APIView,
):
    """
    Save the device configuration.
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
    ):
        dprint("APISwitchSaveConfig(POST)")
        try:
            save = request.data['save']
        except Exception:
            return respond_error("Missing required parameter and value: 'save=yes'")
        if save.lower() not in on_values:
            return respond_error("No save requested (why did you call us?).")

        retval, info = perform_switch_save_config(request, group_id, switch_id)
        if not retval:
            return respond(status=info.code, text=info.description)
        return respond_ok("Configuration saved!")


class APIInterfaceSetState(
    APIView,
):
    """
    Set the description for the selected interface.
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
        interface_id,
    ):
        dprint("APIInterfaceSetState(POST)")
        # need to test permissions - TBD
        try:
            state = request.data['state']
        except Exception:
            return respond_error("Missing required parameter: 'state'")
        if state.lower() in on_values:
            new_state = True
        else:
            new_state = False
        retval, info = perform_interface_admin_change(
            request=request, group_id=group_id, switch_id=switch_id, interface_key=interface_id, new_state=new_state
        )
        if not retval:
            return respond(status=info.code, text=info.description)
        # on success, error.description
        return respond_ok(info.description)


class APIInterfaceSetVlan(
    APIView,
):
    """
    Set the untagged VLAN for an interface.
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
        interface_id,
    ):
        dprint("APIInterfaceSetVlan(POST)")
        try:
            new_pvid = int(request.data['vlan'])
        except Exception:
            return respond_error("Missing required numeric parameter: 'vlan'")
        retval, info = perform_interface_pvid_change(
            request=request, group_id=group_id, switch_id=switch_id, interface_key=interface_id, new_pvid=new_pvid
        )
        if not retval:
            return respond(status=info.code, text=info.description)
        # on success, error.description
        return respond_ok(info.description)


class APIInterfaceSetPoE(
    APIView,
):
    """
    Set the PoE state of an interface.
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
        interface_id,
    ):
        dprint("APIInterfaceSetPoE(POST)")
        try:
            poe_state = request.data['poe_state']
        except Exception:
            return respond_error("Missing required parameter: 'poe_state'")
        if poe_state.lower() in on_values:
            new_state = True
        else:
            new_state = False

        retval, info = perform_interface_poe_change(
            request=request, group_id=group_id, switch_id=switch_id, interface_key=interface_id, new_state=new_state
        )
        if not retval:
            return respond(status=info.code, text=info.description)
        # on success, error.description
        return respond_ok(info.description)


class APIInterfaceSetDescription(
    APIView,
):
    """
    Set the description for the selected interface.
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
        interface_id,
    ):
        dprint("APIInterfaceSetDescription(POST)")
        try:
            description = request.data['description']
        except Exception:
            return respond_error("Missing required parameter: 'description'")
        retval, info = perform_interface_description_change(
            request=request,
            group_id=group_id,
            switch_id=switch_id,
            interface_key=interface_id,
            new_description=description,
        )
        if not retval:
            return respond(status=info.code, text=info.description)
        return respond_ok(info.description)


class APISwitchVlanAdd(
    APIView,
):
    """
    Add a VLAN to a switch.
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
    ):
        dprint("APISwitchVlanAdd(POST)")
        try:
            vlan_name = str(request.data['vlan_name']).strip()
            vlan_id = int(request.data['vlan_id'])
        except Exception:
            return respond_error("One or more missing or invalid required parameters: 'vlan_name', 'vlan_id'")
        # now go create the new vlan:
        dprint(f"   New vlan: '{vlan_name}' = {vlan_id}")
        retval, info = perform_switch_vlan_add(
            request=request, group_id=group_id, switch_id=switch_id, vlan_id=vlan_id, vlan_name=vlan_name
        )
        if not retval:
            return respond(status=info.code, text=info.description)
        return respond_ok(info.description)


class APISwitchVlanEdit(
    APIView,
):
    """
    Add a VLAN to a switch.
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
    ):
        dprint("APISwitchVlanEdit(POST)")
        try:
            vlan_name = str(request.data['vlan_name']).strip()
            vlan_id = int(request.data['vlan_id'])
        except Exception:
            return respond_error("One or more missing or invalid required parameters: 'vlan_name', 'vlan_id'")
        dprint(f"   Edit vlan: {vlan_id} = '{vlan_name}'")
        retval, info = perform_switch_vlan_edit(
            request=request, group_id=group_id, switch_id=switch_id, vlan_id=vlan_id, vlan_name=vlan_name
        )
        if not retval:
            return respond(status=info.code, text=info.description)
        return respond_ok(info.description)


class APISwitchVlanDelete(
    APIView,
):
    """
    Add a VLAN to a switch.
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
    ):
        dprint("APISwitchVlanDelete(POST)")
        try:
            vlan_id = int(request.data['vlan_id'])
        except Exception:
            return respond_error("Missing or invalid required parameter: 'vlan_id'")
        dprint(f"   Delete vlan: {vlan_id}")
        retval, info = perform_switch_vlan_delete(
            request=request, group_id=group_id, switch_id=switch_id, vlan_id=vlan_id
        )
        if not retval:
            return respond(status=info.code, text=info.description)
        return respond_ok(info.description)


"""
Support functions.
"""


def get_connection_to_switch(request, group_id, switch_id, details=False):
    """Test permission to switch, and get connection object if allowed.

    Params:
        request: the http Request() object of this call.
        group_id (int): the pk for the SwitchGroup() object
        switch_id (int): the pk for the Switch() object.
        details (boolean): the True, return will include ARP, MAC, LLDP data.

    Returns:
        (connection, response_error):
        connection is a fully loaded Connection() object if all is valid, or None if not.
        If all OK, response_error will None, but on errors it will be a valid Response() object.
    """
    dprint("get_connection_to_switch()")
    # test permission first:
    group, switch = get_group_and_switch(
        request=request,
        group_id=group_id,
        switch_id=switch_id,
    )
    if not group or not switch:
        return None, respond(status=http_status.HTTP_403_FORBIDDEN, text="Access denied!")

    # access allowed, try to get a connection:
    try:
        connection = get_connection_object(request, group, switch)
    except Exception as e:
        dprint(f"ERROR in get_connection_object(): {e}")
        return None, respond_error(f"ERROR in get_connection_object(): {e}")

    # read details as needed:
    if details and not connection.get_client_data():
        dprint(f"ERROR getting device details: {connection.error.description}")
        return None, respond_error(connection.error.description)

    return connection, None


def respond(status, text):
    if status == http_status.HTTP_200_OK:
        data = {"result": text}
    else:
        data = {"reason": text}
    return Response(
        data=data,
        status=status,
    )


def respond_ok(result):
    return Response(
        data={
            "result": result,
        },
        status=http_status.HTTP_200_OK,
    )


def respond_error(reason):
    return Response(
        data={
            "reason": reason,
        },
        status=http_status.HTTP_400_BAD_REQUEST,
    )
