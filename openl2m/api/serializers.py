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


class EthernetSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    interface_name = serializers.IntegerField(
        required=True,
        read_only=False,
    )
    ethernet = serializers.CharField(
        required=False,
        read_only=False,
        allow_blank=True,
        max_length=32,
    )
