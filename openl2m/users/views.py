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
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.generic import View

#
# Logout view only, Login comes from default auth.
#


class LogoutView(View):

    def get(self, request):
        return self.logout(request)

    def post(self, request):
        return self.logout(request)

    def logout(self, request):
        # logging is done in signal handler in models.py
        # Log out the user
        auth_logout(request)
        messages.info(request, "You have successfully logged out!")

        # Delete session key cookie (if set) upon logout
        response = HttpResponseRedirect(reverse('home'))
        response.delete_cookie('session_key')

        return response


#
# Class to show the user their profiles
#

class ProfileView(LoginRequiredMixin, View):
    template_name = 'users/profile.html'

    def get(self, request):

        return render(request, self.template_name, {
            'user': request.user,
        })


#
# Class to show admin/staff info about another user.
#

class InfoView(LoginRequiredMixin, View):
    template_name = 'users/profile.html'

    def get(self, request, user_id):

        if request.user.is_superuser or request.user.is_staff:
            user = get_object_or_404(User, pk=user_id)
            return render(request, self.template_name, {
                'user': user,
            })
        else:
            return HttpResponseNotFound("You do not have access to this page!")
