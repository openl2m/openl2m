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
import distro
import os
import platform

from django import __version__ as DJANGO_VERSION
from django.conf import settings

# restframework related:
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from switches.utils import dprint


API_VERSION = 1


class APIRootView(APIView):
    """
    This is the root of OpenL2M's REST API. API endpoints are arranged by app; e.g. `/api/switches/`.
    """

    # permission_classes = [
    #     IsAuthenticated,
    # ]

    def get_view_name(self):
        return "API Root"

    @extend_schema(exclude=True)
    def get(self, request, format=None):
        dprint("APIRootView(GET)")
        return Response(
            {
                'switches': reverse('switches-api:api_switch_menu_view', request=request, format=format),
                #                'switches/description': reverse('switches-api:api_interface_set_description', request=request, format=format),
                'stats': reverse('api-stats', request=request, format=format),
            }
        )


class APIStatsView(APIView):
    """
    A lightweight read-only endpoint for conveying OpenL2M's current usage statistics.
    """

    # permission_classes = [
    #     IsAuthenticated,
    # ]

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        dprint("APIStatsView(GET)")
        uname = os.uname()
        return Response(
            {
                'api-version': API_VERSION,
                'django-version': DJANGO_VERSION,
                'openl2m-version': settings.VERSION,
                'os': f"{uname.sysname} ({uname.release})",
                'distro': f"{distro.name()} {distro.version(best=True)}",
                'hostname': uname.nodename,
                'python-version': platform.python_version(),
            }
        )
