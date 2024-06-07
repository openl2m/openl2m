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
from rest_framework import permissions, viewsets
from rest_framework import status as http_status
from rest_framework.response import Response
from rest_framework.views import APIView

from openl2m.api.authentication import IsSuperUser

from switches.models import Switch, SwitchGroup, SnmpProfile, NetmikoProfile
from switches.api.admin.serializers import (
    SwitchSerializer,
    NetmikoProfileSerializer,
    SnmpProfileSerializer,
    SwitchGroupSerializer,
)
from switches.utils import dprint


class APIAdminSwitches(APIView):
    '''
    API Class to GET the details on all users, or create a new user (POST)
    '''

    permission_classes = [IsSuperUser]

    # get all users
    def get(self, request):
        dprint(f"APIAdminSwitches.get(): user={request.user.username}")
        # return all devices.
        users = Switch.objects.all()
        serializer = SwitchSerializer(users, many=True, context={'request': request})
        return Response(data=serializer.data, status=http_status.HTTP_200_OK)

    # create a new user
    def post(self, request):
        dprint("APIAdminSwitches.post(): user={request.user.username}")
        serializer = SwitchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=http_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


class APIAdminSwitchDetail(APIView):
    '''
    API class to GET or update the details of a switch (device).
    '''

    permission_classes = [IsSuperUser]

    def get(self, request, pk):
        dprint(f"APIAdminSwitchDetail(): pk={pk}, user={request.user.username}")
        try:
            s = Switch.objects.get(pk=pk)
        except Exception as err:
            return Response(
                data={
                    "reason": "Invalid switch id!",
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        serializer = SwitchSerializer(s, context={'request': request})
        return Response(
            data=serializer.data,
            status=http_status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        dprint("APIAdminSwitchDetail.patch() passing to post")
        return self.post(request, pk)

    def post(self, request, pk):
        dprint(f"APIAdminSwitchDetail.post() for pk={pk}, user={request.user.username}")
        serializer = SwitchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=http_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


class APIAdminNetmikoProfiles(APIView):
    '''
    API class to GET all Credential Profiles (NetmikoProfile objects) or create a new one.
    '''

    permission_classes = [IsSuperUser]

    def get(self, request):
        '''Return all Credential Profiles'''
        dprint("APIAdminNetmikoProfiles.get()")
        # return all credentials.
        profiles = NetmikoProfile.objects.all()
        serializer = NetmikoProfileSerializer(profiles, many=True, context={'request': request})
        return Response(data=serializer.data, status=http_status.HTTP_200_OK)

    def post(self, request):
        '''Add a new Credential Profile ()'''
        dprint("APIAdminNetmikoProfiles.post()")
        serializer = NetmikoProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=http_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


class APIAdminNetmikoProfileDetail(APIView):
    '''
    API class to read or update a specific Credential Profile (NetmikoProfile) or create a new one.
    '''

    permission_classes = [IsSuperUser]

    def get(self, request, pk):
        '''Return a specific Credential Profile (NetmikoProfile) object'''
        dprint(f"APIAdminNetmikoProfileDetail.get() for pk={pk}")
        try:
            profile = NetmikoProfile.objects.get(pk=pk)
        except Exception as err:
            return Response(
                data={
                    "reason": "Invalid profile id!",
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        serializer = NetmikoProfileSerializer(profile, context={'request': request})
        return Response(
            data=serializer.data,
            status=http_status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        dprint("APIAdminNetmikoProfileDetail.patch() passing to post")
        return self.post(request, pk)

    def post(self, request, pk):
        '''Update a Credential Profile (NetmikoProfile) object'''
        dprint(f"APIAdminNetmikoProfileDetail.post() for pk={pk}")


class APIAdminSnmpProfiles(APIView):
    '''
    API class to GET all SNMP Profiles or create a new one.
    '''

    permission_classes = [IsSuperUser]

    def get(self, request):
        '''Return all SnmpProfile objects'''
        dprint("APIAdminSnmpProfiles.get()")
        # return all snmp profiles.
        profiles = SnmpProfile.objects.all()
        serializer = SnmpProfileSerializer(profiles, many=True, context={'request': request})
        return Response(data=serializer.data, status=http_status.HTTP_200_OK)

    def post(self, request):
        '''Add a new SnmpProfile object'''
        dprint("APIAdminSnmpProfiles.post()")
        serializer = SnmpProfileSerializer(data=request.data)
        # dprint(repr(serializer))
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=http_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


class APIAdminSnmpProfileDetail(APIView):
    '''
    API class to read or update a specific SNMP Profile
    '''

    permission_classes = [IsSuperUser]

    def get(self, request, pk):
        '''Return a specific SnmpProfile object'''
        dprint(f"APIAdminSnmpProfileDetail.get() for pk={pk}")
        try:
            profile = SnmpProfile.objects.get(pk=pk)
        except Exception as err:
            return Response(
                data={
                    "reason": "Invalid profile id!",
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        serializer = SnmpProfileSerializer(profile, context={'request': request})
        return Response(
            data=serializer.data,
            status=http_status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        dprint("APIAdminSnmpProfileDetail.patch() passing to post")
        return self.post(request, pk)

    def post(self, request, pk):
        '''Update a specific SnmpProfile object'''
        dprint("APIAdminSnmpProfileDetail.post() for pk={pk}")


class APIAdminSwitchGroups(APIView):
    '''
    API class to GET all SwitchGroups or create a new one.
    '''

    permission_classes = [IsSuperUser]

    def get(self, request):
        '''Return all SwitchGroup objects'''
        dprint("APIAdminSwitchGroups.get()")
        # return all switchgroups.
        groups = SwitchGroup.objects.all()
        serializer = SwitchGroupSerializer(groups, many=True, context={'request': request})
        return Response(data=serializer.data, status=http_status.HTTP_200_OK)

    def post(self, request):
        '''Add a new SwitchGroup object'''
        dprint("APIAdminSwitchGroups.post()")
        serializer = SwitchGroupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=http_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


class APIAdminSwitchGroupDetail(APIView):
    '''
    API class to read or update a specific SwitchGroup
    '''

    permission_classes = [IsSuperUser]

    def get(self, request, pk):
        '''Return a specific SwitchGroup object'''
        dprint(f"APIAdminSwitchGroupDetail.get() for pk={pk}")
        try:
            switchgroup = SwitchGroup.objects.get(pk=pk)
        except Exception as err:
            return Response(
                data={
                    "reason": "Invalid switchgroup id!",
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        serializer = SwitchGroupSerializer(switchgroup, context={'request': request})
        return Response(
            data=serializer.data,
            status=http_status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        dprint("APIAdminSwitchGroupDetail.patch() passing to post")
        return self.post(request, pk)

    def post(self, request, pk):
        '''Update a specific SwitchGroup object'''
        dprint("APIAdminSwitchGroupDetail.post() for pk={pk}")
