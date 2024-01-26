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
"""
openl2m URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
https://docs.djangoproject.com/en/2.2/topics/http/urls/
"""
from django.conf import settings
from django.contrib.auth.views import (
    LoginView,
    PasswordChangeDoneView,
    PasswordChangeView,
)
from django.urls import include, path

# from django.conf.urls import include
from django.http import HttpResponseRedirect

from openl2m.api.views import APIRootView, APIStatsView, APIEnvironmentView

from users.views import LogoutView

# Custom admin site:
from .admin import admin_site

app_name = "openl2m"
urlpatterns = [
    # / view redirects to the "switches" app
    path("", lambda r: HttpResponseRedirect("switches/"), name="home"),
    # our own customized form for logout
    # note that we capture login/logout signals in "users/models.py", so we can add log entries
    path("logout/", LogoutView.as_view(), name="logout"),
    path("admin/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/login/", LoginView.as_view(), name="login"),
    # override some of the password templates, so we can disabled that for ldap
    path(
        "accounts/password_change/",
        PasswordChangeView.as_view(template_name="registration/password_change.html"),
        name="password_change",
    ),
    path(
        "accounts/password_change/done/",
        PasswordChangeDoneView.as_view(template_name="registration/password_change_done.html"),
        name="password_change_done",
    ),
    # and the rest are not used:
    # url(r'^accounts/$', include('django.contrib.auth.urls')),
    # application paths
    path("switches/", include("switches.urls")),
    # user profiles, etc.
    path("users/", include("users.urls")),
    # Admin - customized, see admin.py
    path("admin/", admin_site.urls),
    #
    # API paths
    path("api/", APIRootView.as_view(), name="api-root"),
    path("api/switches/", include("switches.api.urls"), name="switches-api"),
    path("api/stats/", APIStatsView.as_view(), name='api-stats'),
    path("api/environment/", APIEnvironmentView.as_view(), name='api-environment'),
    path("api/users/", include("users.api.urls"), name="users-api"),
    # to be implemented:
    # path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='api_docs'),
    # path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='api_redocs'),
]

if settings.DEBUG and settings.DEBUG_TOOLBAR:
    # import debug_toolbar
    urlpatterns += [
        # debug toolbar:
        path("__debug__/", include("debug_toolbar.urls")),
    ]
