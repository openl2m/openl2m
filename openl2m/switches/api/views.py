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
from rest_framework import status as http_status
from rest_framework.request import Request as RESTRequest
from rest_framework.response import Response
from rest_framework.reverse import reverse as rest_reverse
from rest_framework.views import APIView

from switches.actions import perform_interface_description_change, perform_switch_save_config
from switches.connect.connect import get_connection_object
from switches.connect.constants import POE_PORT_ADMIN_ENABLED, POE_PORT_ADMIN_DISABLED
from switches.permissions import get_my_device_groups
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
        if isinstance(request, RESTRequest):
            dprint("***REST CALL ***")
        dprint(f"  REST Menu: user={request.user.username}, auth={request.auth}")

        groups, group, switch = get_my_device_groups(request=request)
        data = {
            "user": request.user.username,
            'groups': groups,
        }
        return Response(
            data=data,
            status=http_status.HTTP_200_OK,
        )


def switch_info(request, group_id, switch_id, details):
    conn, response_error = get_connection_switch(
        request=request, group_id=group_id, switch_id=switch_id, details=details
    )
    if response_error:
        return response_error
    data = {
        "switch": conn.as_dict(),
    }
    interfaces = list()
    for key, iface in conn.interfaces.items():
        inf = iface.as_dict()
        # add some url info:
        inf["url_set_vlan"] = rest_reverse(
            "switches-api:api_interface_set_vlan",
            request=request,
            kwargs={"group_id": group_id, "switch_id": switch_id, "interface_id": iface.key},
        )
        inf["url_set_state"] = rest_reverse(
            "switches-api:api_interface_set_state",
            request=request,
            kwargs={"group_id": group_id, "switch_id": switch_id, "interface_id": iface.key},
        )
        inf["url_set_poe_state"] = rest_reverse(
            "switches-api:api_interface_set_poe_state",
            request=request,
            kwargs={"group_id": group_id, "switch_id": switch_id, "interface_id": iface.key},
        )
        inf["url_set_description"] = rest_reverse(
            "switches-api:api_interface_set_description",
            request=request,
            kwargs={"group_id": group_id, "switch_id": switch_id, "interface_id": iface.key},
        )
        # now append this data to the list of interfaces:
        interfaces.append(inf)
    # add to return data:
    data["interfaces"] = interfaces
    conn.save_cache()  # this only works for SessionAuthentication !
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


class APISwitchDetailView(
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
            save = request.POST['save']
        except Exception:
            return respond_error("Missing required parameter and value: 'save=yes'")
        if save.lower() not in on_values:
            return respond_error("No save requested (why did you call us?).")

        retval, error = perform_switch_save_config(request, group_id, switch_id)
        if not retval:
            return respond(status=error.code, text=error.description)
        return respond_ok("Configuration saved!")


class APIInterfaceSetState(
    APIView,
):
    """
    Set the admin state of the selected interface.
    """

    def post(
        self,
        request,
        group_id,
        switch_id,
        interface_id,
    ):
        dprint("APIInterfaceSetState(POST)")
        conn, response_error = get_connection_switch(request=request, group_id=group_id, switch_id=switch_id)
        if response_error:
            return response_error
        # TODO: now here we need to parse the incoming data to actually change the state of the interface.
        dprint(f"  POST = {request.POST}")
        # need to test access permissions here!
        # TBD
        try:
            state = request.POST['state']
        except Exception:
            return respond_error("Missing required parameter: 'state'")
        if state.lower() in on_values:
            new_state = True
        else:
            new_state = False
        # now go set the new admin state:
        dprint(f"*** REST admin state = '{new_state}' ({state})")
        iface = conn.get_interface_by_key(interface_id)
        if not iface:
            return respond_error(f"Interface ID not found: '{interface_id}'")

        if not iface.manageable:
            return respond_error(iface.unmanage_reason)

        retval = conn.set_interface_admin_status(iface, new_state)
        if retval < 0:
            return respond_error(f"Interface {iface.name}: Admin State ERROR: {conn.error.description}")
        return respond_ok("New admin state applied!")


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
        conn, response_error = get_connection_switch(request=request, group_id=group_id, switch_id=switch_id)
        if response_error:
            return response_error
        # TODO: here we need to parse all information and validate the information so that we can do a bulk update for the interface
        dprint(f"  POST = {request.POST}")
        try:
            new_pvid = int(request.POST['vlan'])
        except Exception:
            return respond_error("Missing required numeric parameter: 'vlan'")
        dprint(f"*** REST vlan = '{new_pvid}'")

        # need to test if this user is allowed to change to this vlan!
        conn._set_allowed_vlans()
        if new_pvid not in conn.allowed_vlans.keys():  # now go set the new vlan
            return respond_error(f"Access to vlan {new_pvid} is denied!")

        iface = conn.get_interface_by_key(interface_id)
        if not iface:
            return respond_error(f"Interface ID not found: '{interface_id}'")

        if not iface.manageable:
            return respond_error(iface.unmanage_reason)

        if new_pvid == iface.untagged_vlan:
            return respond_ok(f"Ignored, vlan already {new_pvid}")
        retval = conn.set_interface_untagged_vlan(iface, new_pvid)
        if retval < 0:
            return respond_error(f"Interface {iface.name}: change Vlan ERROR: {conn.error.description}")
        return respond_ok("New Vlan applied!")


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
        conn, response_error = get_connection_switch(request=request, group_id=group_id, switch_id=switch_id)
        if response_error:
            return response_error
        # TODO: now here we need to parse the incoming data to actually change the state of the interface.
        dprint(f"  POST = {request.POST}")

        # need to test permissions - TBD

        try:
            poe_state = request.POST['poe_state']
        except Exception:
            return respond_error("Missing required parameter: 'poe_state'")
        if poe_state.lower() in on_values:
            new_state = POE_PORT_ADMIN_ENABLED
        else:
            new_state = POE_PORT_ADMIN_DISABLED
        # now go set the new PoE state:
        dprint(f"*** REST poe_state = '{poe_state} ({new_state})'")
        iface = conn.get_interface_by_key(interface_id)
        if not iface:
            return respond_error(f"Interface ID not found: '{interface_id}'")

        if not iface.manageable:
            return respond_error(iface.unmanage_reason)

        retval = conn.set_interface_poe_status(iface, new_state)
        if retval < 0:
            return respond_error(f"Interface {iface.name}: PoE State ERROR: {conn.error.description}")
        return respond_ok("New PoE state applied!")


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
        # need to test permissions - TBD
        try:
            description = request.POST['description']
        except Exception:
            return respond_error("Missing required parameter: 'description'")
        retval, error = perform_interface_description_change(request, group_id, switch_id, interface_id, description)
        if not retval:
            return respond(status=error.code, text=error.description)
        return respond_ok("New description applied!")


class APISwitchAddVlan(
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
        dprint("APISwitchAddVlan(POST)")
        conn, response_error = get_connection_switch(request=request, group_id=group_id, switch_id=switch_id)
        if response_error:
            return response_error
        # TODO: here we need to parse all information and validate the information so that we can do a bulk update for the interface
        dprint(f"  POST = {request.POST}")
        # need to test permissions - TBD
        try:
            vlan_name = str(request.POST['vlan_name']).strip()
            vlan_id = int(request.POST['vlan_id'])
        except Exception:
            return respond_error("Missing required parameter: 'vlan_name' or 'vlan_id'")
        # now go create the new vlan:
        dprint(f"*** REST new vlan: '{vlan_name}' = {vlan_id}")

        # test if user is permitted to add vlans:
        # if not not user_can_edit_vlans(request.user, group, switch)

        if conn.vlan_exists(vlan_id) or not vlan_name:
            respond_error("Invalid parameters!")

        retval = conn.vlan_create(vlan_id=vlan_id, vlan_name=vlan_name)
        if not retval:
            return respond_error(f"Vlan creation error: {conn.error.description}")
        return respond_ok("New vlan created!")


"""
Support functions.
"""


def get_connection_switch(request, group_id, switch_id, details=False):
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
    dprint("API-get_connection_switch()")
    # test permission first:
    groups, group, switch = get_my_device_groups(
        request=request,
        group_id=group_id,
        switch_id=switch_id,
    )
    if not group or not switch:
        return None, response(status=http_status.HTTP_403_FORBIDDEN, comment="Access denied!")

    # access allowed, try to get a connection:
    try:
        dprint("  BEFORE get_connection_object()")
        conn = get_connection_object(request, group, switch)
        dprint("  AFTER get_connection_object()")
    except Exception as e:
        dprint(f"A Connection Error occured: {conn.error.description}")
        return None, respond_error(reason=conn.error.description)

    # read details as needed:
    if details and not conn.get_client_data():
        dprint(f"ERROR gettting device details: {conn.error.description}")
        return None, respond_error(reason=conn.error.description)

    return conn, None


def respond(status, text):
    if status == http_status.HTTP_200_OK:
        data = {"result": text}
    else:
        data = {"reason": text}
    return Response(
        data=data,
        status=status,
    )


def respond_ok(comment):
    return Response(
        data={
            "result": comment,
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
