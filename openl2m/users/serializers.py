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
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from rest_framework import serializers

from users.models import Profile

from switches.utils import dprint


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"

    def create(self, validated_data):
        '''
        We override the create() function so we can properly set the password.
        Obviously also need to set the other attributes!
        '''
        dprint("UserSerializer.Create() called!")

        # optional fields:
        if 'email' in validated_data:
            email = validated_data['email']
        else:
            email = ""
        if 'first_name' in validated_data:
            first_name = validated_data['first_name']
        else:
            first_name = ""
        if 'last_name' in validated_data:
            last_name = validated_data['last_name']
        else:
            last_name = ""
        # create the new user object:
        user = User.objects.create(
            username=validated_data['username'],
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
