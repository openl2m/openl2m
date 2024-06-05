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
from rest_framework.generics import RetrieveUpdateAPIView

from openl2m.api.authentication import IsSuperUser

from users.serializers import UserSerializer

from switches.utils import dprint


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
        return Response(data=serializer.data, status=http_status.HTTP_200_OK)

    # create a new user
    def post(self, request):
        dprint("APIAdminUsers(POST) - create new user")
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=http_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


class APIAdminUserDetail(RetrieveUpdateAPIView):
    '''
    API class to GET or update (PUT, PATCH) the details of a user.
    '''

    permission_classes = [IsSuperUser]

    def get(self, request, pk):
        dprint(f"APIAdminUserDetail.get(): pk={pk}, user={request.user.username}, auth={request.auth}")
        try:
            u = User.objects.get(pk=pk)
        except Exception as err:
            return Response(
                data={
                    "reason": "Invalid user id!",
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserSerializer(u, context={'request': request})
        if serializer.is_valid():
            return Response(
                data=serializer.data,
                status=http_status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)
