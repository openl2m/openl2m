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
from django.contrib.auth.models import User
from rest_framework import permissions, viewsets
from rest_framework import status as http_status
from rest_framework.response import Response
from rest_framework.views import APIView

from openl2m.api.authentication import IsSuperUser

from switches.constants import (
    LOG_TYPE_CHANGE,
    LOG_TYPE_ERROR,
    LOG_TYPE_VIEW,
    LOG_REST_API_ADMIN_USER_GET_ALL,
    LOG_REST_API_ADMIN_USER_CREATE,
    LOG_REST_API_ADMIN_USER_GET,
    LOG_REST_API_ADMIN_USER_MODIFY,
)

from switches.models import Log
from switches.utils import dprint
from users.api.admin.serializers import UserSerializer, ProfileSerializer
from users.api.admin.utils import add_user_to_switchgroups, update_user_profile


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class APIAdminUsers(APIView):
    '''
    API Class to return all users (GET), or create a new user (POST)
    '''

    permission_classes = [IsSuperUser]

    # get all users
    def get(self, request):
        dprint(f"APIAdminUsers(GET)- get all by '{request.user.username}'")
        # return all users.
        users = User.objects.all()
        serializer = UserSerializer(users, many=True, context={'request': request})
        log = Log(
            type=LOG_TYPE_VIEW,
            action=LOG_REST_API_ADMIN_USER_GET_ALL,
            user=request.user,
            ip_address=get_remote_ip(request),
            description="API Admin get all users",
        )
        log.save()
        return Response(data=serializer.data, status=http_status.HTTP_200_OK)

    # create a new user
    def post(self, request):
        dprint("APIAdminUsers(POST) - create new user")
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return_data = serializer.data
            add_user_to_switchgroups(request, user)
            profile = update_user_profile(request, user)
            if profile:
                # add profile data to return
                profile_serializer = ProfileSerializer(profile)
                return_data['profile'] = profile_serializer.data
            log = Log(
                type=LOG_TYPE_CHANGE,
                action=LOG_REST_API_ADMIN_USER_CREATE,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin create user, parameters: {request.data}",
            )
            log.save()
            return Response(data=return_data, status=http_status.HTTP_201_CREATED)
        # invalid data:
        log = Log(
            type=LOG_TYPE_ERROR,
            action=LOG_REST_API_ADMIN_USER_CREATE,
            user=request.user,
            ip_address=get_remote_ip(request),
            description=f"API Admin create user error: '{serializer.errors}', parameters: {request.data}",
        )
        log.save()
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


class APIAdminUserDetail(APIView):
    '''
    API class to read (GET) or update (PATCH) the details of a user.
    '''

    permission_classes = [IsSuperUser]

    def get(self, request, pk):
        '''GET return the user object for a primary key 'pk' '''
        dprint(f"APIAdminUserDetail.get(): pk={pk}, user={request.user.username}, profile={request.user.profile}")
        try:
            user = User.objects.get(pk=pk)
        except Exception as err:
            # log the error
            log = Log(
                type=LOG_TYPE_ERROR,
                action=LOG_REST_API_ADMIN_USER_GET,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin get user error: unknown id={pk}",
            )
            log.save()
            # return error
            return Response(
                data={
                    "reason": "Invalid user id!",
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        serializer = UserSerializer(user, context={'request': request})
        # also get the profile
        profile_serializer = ProfileSerializer(user.profile, context={'request': request})
        # collect user and profile data
        data = serializer.data
        data['profile'] = profile_serializer.data
        # log the request
        log = Log(
            type=LOG_TYPE_VIEW,
            action=LOG_REST_API_ADMIN_USER_GET,
            user=request.user,
            ip_address=get_remote_ip(request),
            description=f"API Admin get user for pk={pk}, user={user.name}",
        )
        log.save()
        # and return it:
        return Response(
            data=data,
            status=http_status.HTTP_200_OK,
        )

    def patch(self, request, pk):
        dprint("APIAdminUserDetail.patch() passing to post")
        return self.post(request, pk)

    def post(self, request, pk):
        '''Handle POST to update attributes of the User object for private key 'pk' '''
        dprint(f"APIAdminUserDetail.post(): pk={pk}, user={request.user.username}")
        try:
            user = User.objects.get(pk=pk)
        except Exception as err:
            # log the error
            log = Log(
                type=LOG_TYPE_ERROR,
                action=LOG_REST_API_ADMIN_USER_MODIFY,
                user=request.user,
                ip_address=get_remote_ip(request),
                description=f"API Admin modify user error: unknown id={pk}",
            )
            log.save()
            # send the error
            return Response(
                data={
                    "reason": "Invalid user id!",
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return_data = serializer.data
            add_user_to_switchgroups(request, user)
            profile = update_user_profile(request, user)
            if profile:
                # add profile data to return
                profile_serializer = ProfileSerializer(profile)
                return_data['profile'] = profile_serializer.data
                # log the change
                log = Log(
                    type=LOG_TYPE_CHANGE,
                    action=LOG_REST_API_ADMIN_USER_MODIFY,
                    user=request.user,
                    ip_address=get_remote_ip(request),
                    description=f"API Admin modify user for id={pk}, user={user.name}, parameters={request.data}",
                )
                log.save()

            return Response(
                data=return_data,
                # data={'result': f"User id {pk} has been updated!"},
                status=http_status.HTTP_200_OK,
            )
        # log the error:
        log = Log(
            type=LOG_TYPE_ERROR,
            action=LOG_REST_API_ADMIN_USER_MODIFY,
            user=request.user,
            ip_address=get_remote_ip(request),
            description=f"API Admin modify user error for id={pk}, user={u.name}: {serializer.errors}",
        )
        log.save()

        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)
