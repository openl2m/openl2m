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
# Here we implement all user admin API views as classes
#
from rest_framework import status as http_status
from rest_framework.response import Response
from rest_framework.views import APIView

from openl2m.api.authentication import IsSuperUser

from switches.constants import (
    LOG_TYPE_CHANGE,
    LOG_TYPE_ERROR,
    LOG_TYPE_VIEW,
    LOG_REST_API_ADMIN_SWITCH_GET_ALL,
    LOG_REST_API_ADMIN_SWITCH_CREATE,
    LOG_REST_API_ADMIN_SWITCH_GET,
    LOG_REST_API_ADMIN_SWITCH_MODIFY,
    LOG_REST_API_ADMIN_SWITCHGROUP_GET_ALL,
    LOG_REST_API_ADMIN_SWITCHGROUP_CREATE,
    LOG_REST_API_ADMIN_SWITCHGROUP_GET,
    LOG_REST_API_ADMIN_SWITCHGROUP_MODIFY,
    LOG_REST_API_ADMIN_SNMP_PROFILE_GET_ALL,
    LOG_REST_API_ADMIN_SNMP_PROFILE_CREATE,
    LOG_REST_API_ADMIN_SNMP_PROFILE_GET,
    LOG_REST_API_ADMIN_SNMP_PROFILE_MODIFY,
    LOG_REST_API_ADMIN_NETMIKO_PROFILE_GET_ALL,
    LOG_REST_API_ADMIN_NETMIKO_PROFILE_CREATE,
    LOG_REST_API_ADMIN_NETMIKO_PROFILE_GET,
    LOG_REST_API_ADMIN_NETMIKO_PROFILE_MODIFY,
)

from switches.models import Log, Switch, SwitchGroup, SnmpProfile, NetmikoProfile
from switches.api.admin.serializers import (
    SwitchSerializer,
    NetmikoProfileSerializer,
    SnmpProfileSerializer,
    SwitchGroupSerializer,
)
from switches.utils import dprint, get_remote_ip

from switches.api.admin.utils import add_switch_to_switchgroup


class APIAdminSwitches(APIView):
    '''
    API Class to GET the details on all devices/switches,
    or create a new device/switch (POST)
    '''

    permission_classes = [IsSuperUser]

    # get all devices (switches)
    def get(self, request):
        '''
        Return all switches
        '''
        dprint(f"APIAdminSwitches.get(): user={request.user.username}")
        # return all devices.
        switches = Switch.objects.all()
        serializer = SwitchSerializer(switches, many=True, context={'request': request})
        log = Log(
            type=LOG_TYPE_VIEW,
            action=LOG_REST_API_ADMIN_SWITCH_GET_ALL,
            user=request.user,
            ip_address=get_remote_ip(request),
            description="API Admin get all devices",
        )
        log.save()
        return Response(data=serializer.data, status=http_status.HTTP_200_OK)

    # create a new switch
    def post(self, request):
        '''
        Add a new switch, and set switch group membership
        '''
        dprint(f"APIAdminSwitches.post(): user={request.user.username}")
        serializer = SwitchSerializer(data=request.data)
        if serializer.is_valid():
            switch = serializer.save()
            dprint(f"NEW switch pk={switch.pk}")
            if 'switchgroups' in request.data:
                dprint("Switch created, adding to SwitchGroups!")
                # add switch groups.
                add_switch_to_switchgroup(request, switch)
            log = Log(
                type=LOG_TYPE_CHANGE,
                action=LOG_REST_API_ADMIN_SWITCH_CREATE,
                switch=switch,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin create device id={switch.pk}, parameters: {request.data}",
            )
            log.save()
            return Response(serializer.data, status=http_status.HTTP_201_CREATED)
        # invalid data:
        log = Log(
            type=LOG_TYPE_ERROR,
            action=LOG_REST_API_ADMIN_SWITCH_CREATE,
            user=request.user,
            ip_address=get_remote_ip(request),
            description=f"API Admin create device error: '{serializer.errors}', parameters: {request.data}",
        )
        log.save()
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


class APIAdminSwitchDetail(APIView):
    '''
    API class to GET or update (POST/PATCH) the details of a switch (device).
    '''

    permission_classes = [IsSuperUser]

    def get(self, request, pk):
        """Get the details of a device/switch object.

        Params:
            pk (int): the key of the Switch() object
        """
        dprint(f"APIAdminSwitchDetail(): pk={pk}, user={request.user.username}")
        try:
            switch = Switch.objects.get(pk=pk)
        except Exception:
            # log the error
            log = Log(
                type=LOG_TYPE_ERROR,
                action=LOG_REST_API_ADMIN_SWITCH_GET,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin get device error: unknown id={pk}",
            )
            log.save()
            return Response(
                data={
                    "reason": "Invalid switch id!",
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        # log the request
        log = Log(
            type=LOG_TYPE_VIEW,
            action=LOG_REST_API_ADMIN_SWITCH_GET,
            switch=switch,
            user=request.user,
            ip_address=get_remote_ip(request),
            description=f"API Admin get device for id={pk}, name={switch.name}",
        )
        log.save()

        serializer = SwitchSerializer(switch, context={'request': request})
        return Response(
            data=serializer.data,
            status=http_status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        dprint("APIAdminSwitchDetail.patch() passing to post")
        return self.post(request, pk)

    def post(self, request, pk):
        """Modify the attributes of a device/switch object.

        Params:
            pk (int): the key of the Switch() object

            request.data is a Dict() with the attributes to modify.
        """
        dprint(f"APIAdminSwitchDetail.post() for pk={pk}, user={request.user.username}")
        try:
            switch = Switch.objects.get(pk=pk)
        except Exception:
            # log the error:
            log = Log(
                type=LOG_TYPE_ERROR,
                action=LOG_REST_API_ADMIN_SWITCH_MODIFY,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin modify device error: unknown id={pk}",
            )
            log.save()
            return Response(
                data={
                    "reason": "Invalid id!",
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        serializer = SwitchSerializer(switch, data=request.data, context={'request': request}, partial=True)
        if serializer.is_valid():
            serializer.save()
            add_switch_to_switchgroup(request, switch)
            log = Log(
                type=LOG_TYPE_CHANGE,
                action=LOG_REST_API_ADMIN_SWITCH_MODIFY,
                switch=switch,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin modify device for id={pk}, name={switch.name}, parameters={request.data}",
            )
            log.save()
            return Response(serializer.data, status=http_status.HTTP_200_OK)
        else:
            # invalid data
            log = Log(
                type=LOG_TYPE_ERROR,
                action=LOG_REST_API_ADMIN_SWITCH_MODIFY,
                switch=switch,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin modify device error for id={pk}, name={switch.name}, parameters={request.data}: '{serializer.errors}'",
            )
            log.save()
            return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


class APIAdminNetmikoProfiles(APIView):
    '''
    API class to GET all Credential Profiles (NetmikoProfile objects)
    or POST to create a new one.
    '''

    permission_classes = [IsSuperUser]

    def get(self, request):
        '''
        Return all Credential Profiles
        '''
        dprint("APIAdminNetmikoProfiles.get()")
        # return all credentials.
        profiles = NetmikoProfile.objects.all()
        serializer = NetmikoProfileSerializer(profiles, many=True, context={'request': request})
        log = Log(
            type=LOG_TYPE_VIEW,
            action=LOG_REST_API_ADMIN_NETMIKO_PROFILE_GET_ALL,
            user=request.user,
            ip_address=get_remote_ip(request),
            description="API Admin get all credential profiles",
        )
        log.save()
        return Response(data=serializer.data, status=http_status.HTTP_200_OK)

    def post(self, request):
        '''
        Add a new Credential Profile ()
        '''
        dprint("APIAdminNetmikoProfiles.post()")
        serializer = NetmikoProfileSerializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.save()
            log = Log(
                type=LOG_TYPE_CHANGE,
                action=LOG_REST_API_ADMIN_NETMIKO_PROFILE_CREATE,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin create credential profile id={profile.id}, parameters: {request.data}",
            )
            log.save()
            return Response(serializer.data, status=http_status.HTTP_201_CREATED)
        # invalid data:
        log = Log(
            type=LOG_TYPE_ERROR,
            action=LOG_REST_API_ADMIN_NETMIKO_PROFILE_CREATE,
            user=request.user,
            ip_address=get_remote_ip(request),
            description=f"API Admin create credential profile error: '{serializer.errors}', parameters: {request.data}",
        )
        log.save()
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


class APIAdminNetmikoProfileDetail(APIView):
    '''
    API class to read or update a specific Credential Profile (NetmikoProfile) or create a new one.
    '''

    permission_classes = [IsSuperUser]

    def get(self, request, pk):
        '''Return a specific Credential Profile (NetmikoProfile) object

        Params:
            pk (int): the id of the NetmikoProfile() object

        '''
        dprint(f"APIAdminNetmikoProfileDetail.get() for pk={pk}")
        try:
            profile = NetmikoProfile.objects.get(pk=pk)
        except Exception:
            # log the error
            log = Log(
                type=LOG_TYPE_ERROR,
                action=LOG_REST_API_ADMIN_NETMIKO_PROFILE_GET,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin get credential profile error: unknown id={pk}",
            )
            log.save()
            return Response(
                data={
                    "reason": "Invalid profile id!",
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        # log the request
        log = Log(
            type=LOG_TYPE_VIEW,
            action=LOG_REST_API_ADMIN_NETMIKO_PROFILE_GET,
            user=request.user,
            ip_address=get_remote_ip(request),
            description=f"API Admin get credential profile for id={pk}, name={profile.name}",
        )
        log.save()
        serializer = NetmikoProfileSerializer(profile, context={'request': request})
        return Response(
            data=serializer.data,
            status=http_status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        dprint("APIAdminNetmikoProfileDetail.patch() passing to post")
        return self.post(request, pk)

    def post(self, request, pk):
        '''Update a Credential Profile (NetmikoProfile) object

        Params:
            pk (int): the key of the Switch() object

            request.data is a Dict() with the attributes to modify.
        '''
        dprint(f"APIAdminNetmikoProfileDetail.post() for pk={pk}")
        try:
            profile = NetmikoProfile.objects.get(pk=pk)
        except Exception:
            # log the error:
            log = Log(
                type=LOG_TYPE_ERROR,
                action=LOG_REST_API_ADMIN_NETMIKO_PROFILE_MODIFY,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin modify credential profile error: unknown id={pk}",
            )
            log.save()
            return Response(
                data={
                    "reason": "Invalid profile id!",
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        serializer = NetmikoProfileSerializer(profile, data=request.data, context={'request': request}, partial=True)
        if serializer.is_valid():
            serializer.save()
            log = Log(
                type=LOG_TYPE_CHANGE,
                action=LOG_REST_API_ADMIN_NETMIKO_PROFILE_MODIFY,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin modify credential profile for id={pk}, name={profile.name}, parameters={request.data}",
            )
            log.save()
            return Response(
                data=serializer.data,
                status=http_status.HTTP_200_OK,
            )
        else:
            # invalid data
            log = Log(
                type=LOG_TYPE_ERROR,
                action=LOG_REST_API_ADMIN_NETMIKO_PROFILE_MODIFY,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin modify credential profile error for id={pk}, name={profile.name}, parameters={request.data}: '{serializer.errors}'",
            )
            log.save()
            return Response(
                data=serializer.errors,
                status=http_status.HTTP_400_BAD_REQUEST,
            )


class APIAdminSnmpProfiles(APIView):
    '''
    API class to GET all SNMP Profiles or POST to create a new one.
    '''

    permission_classes = [IsSuperUser]

    def get(self, request):
        '''
        Return all SnmpProfile objects
        '''
        dprint("APIAdminSnmpProfiles.get()")
        # return all snmp profiles.
        profiles = SnmpProfile.objects.all()
        serializer = SnmpProfileSerializer(profiles, many=True, context={'request': request})
        log = Log(
            type=LOG_TYPE_VIEW,
            action=LOG_REST_API_ADMIN_SNMP_PROFILE_GET_ALL,
            user=request.user,
            ip_address=get_remote_ip(request),
            description="API Admin get all SNMP profiles",
        )
        log.save()
        return Response(data=serializer.data, status=http_status.HTTP_200_OK)

    def post(self, request):
        '''
        Add a new SnmpProfile object
        '''
        dprint("APIAdminSnmpProfiles.post()")
        serializer = SnmpProfileSerializer(data=request.data)
        # dprint(repr(serializer))
        if serializer.is_valid():
            profile = serializer.save()
            log = Log(
                type=LOG_TYPE_CHANGE,
                action=LOG_REST_API_ADMIN_SNMP_PROFILE_CREATE,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin create SNMP profile id={profile.id}, parameters: {request.data}",
            )
            log.save()
            return Response(serializer.data, status=http_status.HTTP_201_CREATED)
        else:
            # invalid data:
            log = Log(
                type=LOG_TYPE_ERROR,
                action=LOG_REST_API_ADMIN_SNMP_PROFILE_CREATE,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin create SNMP profile error: '{serializer.errors}', parameters: {request.data}",
            )
            log.save()
            return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


class APIAdminSnmpProfileDetail(APIView):
    '''
    API class to read (GET) or update (POST/PATCH) a specific SNMP Profile
    '''

    permission_classes = [IsSuperUser]

    def get(self, request, pk):
        '''Return a specific SnmpProfile object

        Params:
            pk (int): the key of the object
        '''

        dprint(f"APIAdminSnmpProfileDetail.get() for pk={pk}")
        try:
            profile = SnmpProfile.objects.get(pk=pk)
        except Exception:
            # log the error
            log = Log(
                type=LOG_TYPE_ERROR,
                action=LOG_REST_API_ADMIN_SNMP_PROFILE_GET,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin get SNMP profile error: unknown id={pk}",
            )
            log.save()
            return Response(
                data={
                    "reason": "Invalid profile id!",
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        # log the request
        log = Log(
            type=LOG_TYPE_VIEW,
            action=LOG_REST_API_ADMIN_SNMP_PROFILE_GET,
            user=request.user,
            ip_address=get_remote_ip(request),
            description=f"API Admin get SNMP profile for id={pk}, name={profile.name}",
        )
        log.save()
        serializer = SnmpProfileSerializer(profile, context={'request': request})
        return Response(
            data=serializer.data,
            status=http_status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        dprint("APIAdminSnmpProfileDetail.patch() passing to post")
        return self.post(request, pk)

    def post(self, request, pk):
        '''Update a specific SnmpProfile object

        Params:
            pk (int): the key of the object

            request.data is a Dict() with the attributes to modify.
        '''
        dprint("APIAdminSnmpProfileDetail.post() for pk={pk}")
        try:
            profile = SnmpProfile.objects.get(pk=pk)
        except Exception:
            # log the error:
            log = Log(
                type=LOG_TYPE_ERROR,
                action=LOG_REST_API_ADMIN_SNMP_PROFILE_MODIFY,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin modify SNMP profile error: unknown id={pk}",
            )
            log.save()
            return Response(
                data={
                    "reason": "Invalid profile id!",
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        serializer = SnmpProfileSerializer(profile, data=request.data, context={'request': request}, partial=True)
        if serializer.is_valid():
            serializer.save()
            log = Log(
                type=LOG_TYPE_VIEW,
                action=LOG_REST_API_ADMIN_SNMP_PROFILE_MODIFY,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin modify SNMP profile for id={pk}, name={profile.name}, parameters={request.data}",
            )
            log.save()
            return Response(
                data=serializer.data,
                status=http_status.HTTP_200_OK,
            )
        else:
            # invalid data
            log = Log(
                type=LOG_TYPE_ERROR,
                action=LOG_REST_API_ADMIN_SNMP_PROFILE_MODIFY,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin modify SNMP profile error for id={pk}, name={profile.name}, parameters={request.data}: '{serializer.errors}'",
            )
            log.save()
            return Response(
                data=serializer.errors,
                status=http_status.HTTP_400_BAD_REQUEST,
            )


class APIAdminSwitchGroups(APIView):
    '''
    API class to GET all SwitchGroups or POST to create a new one.
    '''

    permission_classes = [IsSuperUser]

    def get(self, request):
        '''
        Return all SwitchGroup objects
        '''
        dprint("APIAdminSwitchGroups.get()")
        # return all switchgroups.
        groups = SwitchGroup.objects.all()
        serializer = SwitchGroupSerializer(groups, many=True, context={'request': request})
        log = Log(
            type=LOG_TYPE_VIEW,
            action=LOG_REST_API_ADMIN_SWITCHGROUP_GET_ALL,
            user=request.user,
            ip_address=get_remote_ip(request),
            description="API Admin get all switchgroups",
        )
        log.save()
        return Response(data=serializer.data, status=http_status.HTTP_200_OK)

    def post(self, request):
        '''
        Add a new SwitchGroup object
        '''
        dprint("APIAdminSwitchGroups.post()")
        serializer = SwitchGroupSerializer(data=request.data)
        if serializer.is_valid():
            switchgroup = serializer.save()
            log = Log(
                type=LOG_TYPE_CHANGE,
                action=LOG_REST_API_ADMIN_SWITCHGROUP_CREATE,
                user=request.user,
                group=switchgroup,
                ip_address=get_remote_ip(request),
                description=f"API Admin create switchgroup id={switchgroup.id}, parameters: {request.data}",
            )
            log.save()
            return Response(serializer.data, status=http_status.HTTP_201_CREATED)
        else:
            # invalid data:
            log = Log(
                type=LOG_TYPE_ERROR,
                action=LOG_REST_API_ADMIN_SWITCHGROUP_CREATE,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin create switchgroup error: '{serializer.errors}', parameters: {request.data}",
            )
            log.save()
            return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


class APIAdminSwitchGroupDetail(APIView):
    '''
    API class to read (GET) or update (POST/PATCH)a specific SwitchGroup
    '''

    permission_classes = [IsSuperUser]

    def get(self, request, pk):
        '''
        Return a specific SwitchGroup object
        '''
        dprint(f"APIAdminSwitchGroupDetail.get() for pk={pk}")
        try:
            switchgroup = SwitchGroup.objects.get(pk=pk)
        except Exception:
            # log the error
            log = Log(
                type=LOG_TYPE_ERROR,
                action=LOG_REST_API_ADMIN_SWITCHGROUP_GET,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin get switchgroup error: unknown id={pk}",
            )
            log.save()
            return Response(
                data={
                    "reason": "Invalid switchgroup id!",
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        # log the request
        log = Log(
            type=LOG_TYPE_VIEW,
            action=LOG_REST_API_ADMIN_SWITCHGROUP_GET,
            user=request.user,
            group=switchgroup,
            ip_address=get_remote_ip(request),
            description=f"API Admin get switchgroup for id={pk}, name={switchgroup.name}",
        )
        log.save()

        serializer = SwitchGroupSerializer(switchgroup, context={'request': request})
        return Response(
            data=serializer.data,
            status=http_status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        dprint("APIAdminSwitchGroupDetail.patch() passing to post")
        return self.post(request, pk)

    def post(self, request, pk):
        '''Update a specific SwitchGroup object

        Params:
            pk (int): the key of the object

            request.data is a Dict() with the attributes to modify.
        '''
        dprint("APIAdminSwitchGroupDetail.post() for pk={pk}")
        try:
            switchgroup = SwitchGroup.objects.get(pk=pk)
        except Exception:
            # log the error:
            log = Log(
                type=LOG_TYPE_ERROR,
                action=LOG_REST_API_ADMIN_SWITCHGROUP_MODIFY,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin modify switchgroup error: unknown id={pk}",
            )
            log.save()
            return Response(
                data={
                    "reason": "Invalid group id!",
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        serializer = SwitchGroupSerializer(switchgroup, data=request.data, context={'request': request}, partial=True)
        if serializer.is_valid():
            dprint(f"Valid data: {repr(serializer.validated_data)}")
            serializer.save()
            log = Log(
                type=LOG_TYPE_VIEW,
                action=LOG_REST_API_ADMIN_SWITCHGROUP_MODIFY,
                group=switchgroup,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin modify switchgroup for id={pk}, name={switchgroup.name}, parameters={request.data}",
            )
            log.save()
            return Response(
                data=serializer.data,
                status=http_status.HTTP_200_OK,
            )
        else:
            # invalid data
            log = Log(
                type=LOG_TYPE_ERROR,
                action=LOG_REST_API_ADMIN_SWITCHGROUP_MODIFY,
                group=switchgroup,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin modify switchgroup error for id={pk}, name={switchgroup.name}, parameters={request.data}: '{serializer.errors}'",
            )
            return Response(
                data=serializer.errors,
                status=http_status.HTTP_400_BAD_REQUEST,
            )
