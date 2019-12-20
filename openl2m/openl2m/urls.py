"""
openl2m URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from django.http import HttpResponseRedirect

from users.views import LogoutView

# Custom admin site:
from .admin import admin_site

app_name = 'openl2m'
urlpatterns = [

    # / view redirects to the "switches" app
    path('', lambda r: HttpResponseRedirect('switches/'), name='home'),

    # our own customized form for logout
    # note that we capture login/logout signals in "users/models.py", so we can add Log() entries
    path(r'logout/', LogoutView.as_view(), name='logout'),

    # Login/logout - the built-in forms:
    # see: https://wsvincent.com/django-user-authentication-tutorial-login-and-logout/
    # url(r'^accounts/$', include('django.contrib.auth.urls')),
    path('accounts/', include('django.contrib.auth.urls')),

    # application paths
    path('switches/', include('switches.urls')),

    # user profiles, etc.
    # path('users/', include('users.urls')),
    # path('users/', include('django.contrib.auth.urls')),

    # Admin - customized, see admin.py
    path('admin/', admin_site.urls),
]
