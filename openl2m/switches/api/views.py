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
from django.shortcuts import get_object_or_404

# Use the Django Rest Framework:
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request as RESTRequest
from rest_framework.response import Response
from rest_framework.reverse import reverse as rest_reverse
from rest_framework.views import APIView

from switches.views import confirm_access_rights
from switches.connect.connect import get_connection_object
from switches.constants import SWITCH_STATUS_ACTIVE, SWITCH_VIEW_BASIC
from switches.connect.constants import POE_PORT_ADMIN_ENABLED, POE_PORT_ADMIN_DISABLED
from switches.utils import dprint
from switches.models import Switch, SwitchGroup, Log

on_values = ["on", "yes", "y", "enabled", "enable", "true", "1"]


class APISwitchMenuView(
    APIView,
):
    """
    Return the groups and devices we have access to.
    """

    # permission_classes = [
    #     IsAuthenticated,
    # ]

    def get(
        self,
        request,
    ):
        if isinstance(request, RESTRequest):
            dprint("***REST CALL ***")
        (permissions, permitted) = get_my_device_permissions(request=request)
        data = {
            "user": request.user.username,
            'groups': permissions,
        }
        return Response(
            data=data,
            status=status.HTTP_200_OK,
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
        status=status.HTTP_200_OK,
    )


class APISwitchBasicView(
    APIView,
):
    """
    Return the basic information for a device. This includes all interfaces.
    To save time we do NOT include mac-address, lldp, poe and other details.
    """

    # permission_classes = [
    #     IsAuthenticated,
    # ]

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

    # permission_classes = [
    #     IsAuthenticated,
    # ]

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

    # permission_classes = [
    #     IsAuthenticated,
    # ]

    def post(
        self,
        request,
        group_id,
        switch_id,
        interface_id,
    ):
        dprint("APISwitchSaveConfig(POST)")
        conn, response_error = get_connection_switch(request=request, group_id=group_id, switch_id=switch_id)
        if response_error:
            return response_error
        # TODO: now here we need to parse the incoming data to actually change the state of the interface.
        dprint(f"  POST = {request.POST}")
        # need to test access permissions here!
        # TBD
        try:
            save = request.POST['save']
        except Exception:
            return respond_error("Missing required parameter and value: 'save=yes'")
        if save.lower() not in on_values:
            return respond_error("No save requested (why did you call us?).")

        # now go save the config:
        retval = conn.save_running_config()
        if retval < 0:
            return respond_error(f"Save ERROR: {conn.error.description}")
        return respond_ok("Configuration saved!")


class APIInterfaceSetState(
    APIView,
):
    """
    Set the admin state of the selected interface.
    """

    # permission_classes = [
    #     IsAuthenticated,
    # ]

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

    # permission_classes = [
    #     IsAuthenticated,
    # ]

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

    # permission_classes = [
    #     IsAuthenticated,
    # ]

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

    # permission_classes = [
    #     IsAuthenticated,
    # ]

    def post(
        self,
        request,
        group_id,
        switch_id,
        interface_id,
    ):
        dprint("APIInterfaceSetDescription(POST)")
        conn, response_error = get_connection_switch(request=request, group_id=group_id, switch_id=switch_id)
        if response_error:
            return response_error
        # TODO: now here we need to parse the incoming data to actually change the state of the interface.
        dprint(f"  POST = {request.POST}")
        # need to test permissions - TBD
        try:
            description = request.POST['description']
        except Exception:
            return respond_error("Missing required parameter: 'description'")
        # now go set the new description:
        dprint(f"*** REST description = '{description}'")
        iface = conn.get_interface_by_key(interface_id)
        if not iface:
            return respond_error(f"Interface ID not found: '{interface_id}'")

        if not iface.manageable:
            return respond_error(iface.unmanage_reason)

        retval = conn.set_interface_description(iface, description)
        if retval < 0:
            return respond_error(f"Interface {iface.name}: Descr ERROR: {conn.error.description}")
        return respond_ok("New description applied!")


class APISwitchAddVlan(
    APIView,
):
    """
    Add a VLAN to a switch.
    """

    # permission_classes = [
    #     IsAuthenticated,
    # ]

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


def get_my_device_permissions(request, group_id=-1, switch_id=-1):
    """
    find the SwitchGroups, and Switch()-es in those groups, that this user has rights to

    Args:
        request:  current Request() object
        group_id (int): the pk of the SwitchGroup()
        switch_id (int): the pk of the Switch()

    Returns:
        tuple of
        permissions:    dict of pk's of SwitchGroup() objects this user is member of,
                        each is a dict of active devices(switches).
        permitted (boolean): True if group_id and switch_id given, and they are allowed!
    """
    if request.user.is_superuser or request.user.is_staff:
        # optimize data queries, get all related field at once!
        switchgroups = SwitchGroup.objects.all().order_by("name")

    else:
        # figure out what this user has access to.
        # Note we use the ManyToMany 'related_name' attribute for readability!
        switchgroups = request.user.switchgroups.all().order_by("name")

    # now find active devices in these groups
    permissions = {}
    permitted = False

    for group in switchgroups:
        if group.switches.count():
            # set this group, and the switches, in web session to track permissions
            group_info = {
                'name': group.name,
                'description': group.description,
                'display_name': group.display_name,
                'read_only': group.read_only,
                'comments': group.comments,
            }
            members = {}
            for switch in group.switches.all():
                if switch.status == SWITCH_STATUS_ACTIVE:
                    # we save the names as well, so we can search them!
                    if switch.default_view == SWITCH_VIEW_BASIC:
                        url = rest_reverse(
                            "switches-api:api_switch_basic_view",
                            request=request,
                            kwargs={"group_id": group.id, "switch_id": switch.id},
                        )
                    else:
                        url = rest_reverse(
                            "switches-api:api_switch_detail_view",
                            request=request,
                            kwargs={"group_id": group.id, "switch_id": switch.id},
                        )
                    members[int(switch.id)] = {
                        "name": switch.name,
                        # "hostname": switch.hostname,
                        "description": switch.description,
                        "default_view": switch.default_view,
                        "default_view_name": switch.get_default_view_display(),
                        "url": url,
                        "url_add_vlan": rest_reverse(
                            "switches-api:api_switch_add_vlan",
                            request=request,
                            kwargs={"group_id": group.id, "switch_id": switch.id},
                        ),
                        "connector_type": switch.connector_type,
                        "connector_type_name": switch.get_connector_type_display(),
                        "read_only": switch.read_only,
                        "primary_ipv4": switch.primary_ip4,
                        "comments": switch.comments,
                    }
                    # is this the switch in the group we are looking for?
                    if switch.id == switch_id and group.id == group_id:
                        permitted = True
            group_info['members'] = members
            permissions[int(group.id)] = group_info
    return (permissions, permitted)


def confirm_access_rights_api(
    request=None,
    group_id=None,
    switch_id=None,
):
    """
    Check if the current user has rights to this switch in this group
    Returns the switch_group and switch_id for further processing
    """
    permissions, permitted = get_my_device_permissions(request=request, group_id=group_id, switch_id=switch_id)
    if permitted:
        group = get_object_or_404(
            SwitchGroup,
            pk=group_id,
        )
        switch = get_object_or_404(
            Switch,
            pk=switch_id,
        )
        dprint("confirm_access_rights_api(): OK!")
        return permitted, group, switch
    else:
        return False, None, None


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
    response_error = None
    # test permission first:
    permitted, group, switch = confirm_access_rights_api(
        request=request,
        group_id=group_id,
        switch_id=switch_id,
    )
    if not permitted:
        return None, response_error(reason="Access denied!")

    # access allowed, try to get a connection:
    try:
        dprint("  BEFORE get_connection_object()")
        conn = get_connection_object(request, group, switch)
        dprint("  AFTER get_connection_object()")
    except Exception as e:
        error = f"A Connection Error occured: {e}"
        dprint(error)
        return None, respond_error(reason=error)
    # finally try to read the data:
    try:
        if not conn.get_basic_info():
            error = "ERROR in get_basic_switch_info()"
            dprint(error)
        if details and not conn.get_client_data():
            error = "ERROR in get_client_data()"
            dprint(error)
    except Exception as e:
        error = f"Error getting switch info: {e}"
        dprint(error)
        response_error = respond_error(reason=error)
    # conn.save_cache() #
    return conn, response_error


def respond_ok(comment):
    return Response(
        data={
            "result": comment,
        },
        status=status.HTTP_200_OK,
    )


def respond_error(reason):
    return Response(
        data={
            "reason": reason,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )
