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
from rest_framework import serializers

from switches.models import Switch, NetmikoProfile, SnmpProfile, SwitchGroup
from switches.utils import dprint


class SwitchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Switch
        fields = '__all__'
        # fields = [
        #     'id',
        #     'name',
        #     'description',
        #     'primary_ip4',
        # ]

    def my_create(self, validated_data):
        '''
        We override the create() function
        Obviously also need to set the other attributes!
        '''
        dprint("SwitchSerializer.Create() called!")
        switch = Switch.objects.create(
            name=validated_data['username'],
        )
        switch.save()
        return switch


class NetmikoProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetmikoProfile
        # fields = '__all__'
        # we exclude the password fields!
        exclude = ['password', 'enable_password']


class SnmpProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SnmpProfile
        # fields = '__all__'
        # we exclude all 'password' like fields:
        exclude = ['community', 'passphrase', 'priv_passphrase']


class SwitchGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = SwitchGroup
        fields = '__all__'
        # we exclude all 'password' like fields:
        # exclude = ['community', 'passphrase', 'priv_passphrase']
