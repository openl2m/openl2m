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
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import View


from switches.connect.classes import Error
from switches.constants import (
    LOG_TYPE_CHANGE,
    LOG_TYPE_ERROR,
    LOG_REST_API_TOKEN_CREATED,
    LOG_REST_API_TOKEN_DELETE,
    LOG_REST_API_TOKEN_EDIT,
)
from switches.models import Log
from switches.views import close_device
from switches.utils import dprint, success_page, error_page, get_remote_ip
from users.models import Token


#
# New Login view to always redirect to /switches
#
class MyLoginView(LoginView):

    # we define the "success ULR" as always going to "/switches/"
    def get_success_url(self) -> str:
        return reverse_lazy("home")


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

        # close out any previous device user was working on
        close_device(request=request)
        # Log out the user
        auth_logout(request)
        messages.success(request, "You have successfully logged out!")

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
        # set the new theme in
        return render(
            request,
            self.template_name,
            {
                'user': request.user,
            },
        )


#
# Class to support switching Themes
#

valid_themes = [
    'light',
    'dark',
]


class ThemeView(LoginRequiredMixin, View):

    def get(self, request, name):
        if name not in valid_themes:
            dprint(f"INVALID THEME: '{name}'")
            error = Error()
            error.description = f"Invalid theme selected: '{name}'"
            return error_page(request=request, group=None, switch=None, error=error)
        # set selected theme in profile
        dprint(f"THEME set to '{name}'")
        request.user.profile.theme = name
        request.user.save()
        # and redirect to the "menu" page
        return HttpResponseRedirect(reverse('home'))


#
# Class to show or hide the device menu
#
class MenuView(LoginRequiredMixin, View):

    def get(self, request, menu):
        # set selected theme in profile
        dprint(f"MENU set to '{menu}'")
        request.user.profile.menu = menu
        request.user.save()
        # and redirect to the "menu" page
        return HttpResponseRedirect(reverse('home'))


#
# Class to show admin/staff info about another user.
#


class InfoView(LoginRequiredMixin, View):
    template_name = 'users/profile.html'

    def get(self, request, user_id):
        if request.user.is_superuser or request.user.is_staff:
            user = get_object_or_404(User, pk=user_id)
            tokens = Token.objects.filter(user=user)
            return render(
                request,
                self.template_name,
                {
                    'user': user,
                    'tokens': tokens,
                },
            )

        return HttpResponseNotFound("You do not have access to this page!")


#
# API Token related
#


class TokenListView(LoginRequiredMixin, View):
    template_name = 'users/token_list.html'

    def get(self, request):
        tokens = Token.objects.filter(user=request.user)
        return render(
            request,
            self.template_name,
            {
                'tokens': tokens,
            },
        )


class TokenDelete(LoginRequiredMixin, View):
    """Delete a token for a user.

    Args:
        request (HttpRequest): the request object
        token_id (int): the pk of the Token() to delete.

    Returns:
        HttpResponse: calls either error_page() or success_page() to return HttpResponse.
    """

    def get(
        self,
        request,
        token_id,
    ):
        dprint("TokenDelete() - GET")
        log = Log(
            type=LOG_TYPE_CHANGE,
            user=request.user,
            ip_address=get_remote_ip(request),
        )
        partial_token = ""
        try:
            token = Token.objects.get(user=request.user, id=token_id)
            partial_token = token.partial
            token.delete()
        except Exception as err:
            error = Error()
            error.description = "Error deleting API key!"
            error.details = str(err)
            log.action = LOG_REST_API_TOKEN_DELETE
            if partial_token:
                log.description = f"Error deleting API key! (id={token_id}, token={partial_token})"
            else:
                log.description = f"Error deleting API key! (id={token_id})"
            log.save()
            return error_page(request=request, group=None, switch=None, error=error)

        log.action = LOG_REST_API_TOKEN_DELETE
        log.description = f"API Key deleted! (id={token_id}, token={partial_token})"
        log.save()
        return success_page(
            request=request, group=None, switch=None, description=f"API Key deleted! (token={partial_token})"
        )


class TokenEdit(LoginRequiredMixin, View):
    """Edit a token for a user.

    Args:
        request (HttpRequest): the request object
        token_id (int): the pk of the Token() to delete.

    Returns:
        HttpResponse: calls either error_page() or success_page() to return HttpResponse.
    """

    def get(
        self,
        request,
        token_id,
    ):
        dprint("TokenEdit() - GET")
        template_name = "users/token_edit.html"
        log = Log(
            type=LOG_TYPE_CHANGE,
            action=LOG_REST_API_TOKEN_EDIT,
            user=request.user,
            ip_address=get_remote_ip(request),
        )
        try:
            token = Token.objects.get(user=request.user, id=token_id)
        except Exception as err:
            error = Error()
            error.description = "Error editing API key!"
            error.details = str(err)
            log.type = LOG_TYPE_ERROR
            log.description = f"Error editing API key for token id {token_id}!"
            log.save()
            return error_page(request=request, group=None, switch=None, error=error)

        return render(
            request,
            template_name,
            {
                'action': 'edit',
                'request': request,
                'token': token,
            },
        )

    def post(
        self,
        request,
        token_id,
    ):
        dprint("TokenEdit() - POST")
        log = Log(
            type=LOG_TYPE_CHANGE,
            action=LOG_REST_API_TOKEN_EDIT,
            user=request.user,
            ip_address=get_remote_ip(request),
        )
        # save this token!
        status, info = update_or_add_token(request=request, token_id=token_id)
        if status:
            log.description = info.description
            log.save()
            return success_page(request=request, group=None, switch=None, description=info.description)

        # error occurred
        log.type = LOG_TYPE_ERROR
        log.description = info.description
        log.save()
        return error_page(request=request, group=None, switch=None, error=info)


class TokenAdd(LoginRequiredMixin, View):
    """Add a token for a user. Either GET or POST method.

    Args:
        request (HttpRequest): the request object

    Returns:
        HttpResponse: calls either error_page() or success_page() to return HttpResponse.
    """

    def get(
        self,
        request,
    ):
        dprint("TokenAdd() - GET")
        template_name = "users/token_edit.html"

        count = Token.objects.filter(user=request.user).count()
        if count >= settings.MAX_API_TOKENS:
            error = Error()
            error.description = f"You cannot create more API tokens (max = {settings.MAX_API_TOKENS})"
            return error_page(request=request, group=None, switch=None, error=error)

        # create a new token, and show the form:
        token = Token()
        token.key = Token.generate_key()
        return render(
            request,
            template_name,
            {
                'action': 'add',
                'request': request,
                'token': token,
            },
        )

    def post(
        self,
        request,
    ):
        dprint("TokenAdd() - POST")

        count = Token.objects.filter(user=request.user).count()
        if count >= settings.MAX_API_TOKENS:
            error = Error()
            error.description = f"You cannot create more API tokens (max = {settings.MAX_API_TOKENS})"
            return error_page(request=request, group=None, switch=None, error=error)

        log = Log(
            type=LOG_TYPE_CHANGE,
            action=LOG_REST_API_TOKEN_CREATED,
            user=request.user,
            ip_address=get_remote_ip(request),
        )
        # save this token!
        status, info = update_or_add_token(request=request)
        if status:
            log.description = info.description
            log.save()
            return success_page(request=request, group=None, switch=None, description=info.description)

        # error occurred
        log.type = LOG_TYPE_ERROR
        log.description = "Error creating API key!"
        log.save()
        return error_page(request=request, group=None, switch=None, error=info)


def update_or_add_token(request, token_id=-1):
    """Modify an existing token, or create a new token

    Args:
        request (HttpRequest()): the request object.
        token_id (int): the pk of the token, or -1 to create a new token.

    Returns:
        boolean, info: where
            True is token created or updated, False on errors.
            info is Error() object with descriptions and details set as needed.
    """
    dprint(f"update_or_add_token() id={token_id}")
    if token_id != -1:
        # get existing token
        try:
            token = Token.objects.get(user=request.user, id=token_id)
        except Exception as err:
            error = Error()
            error.description = "Error updating API key!"
            error.details = str(err)
            return False, error
        action = "updated"
    else:
        # create new token
        token = Token()
        token.user = request.user
        token.key = request.POST.get('key', '')
        # this should not happen!
        if not token.key:
            error = Error()
            error.description = "Invalid new API token, key not set!"
            return False, error
        action = "created"

    # read the rest of the form data:
    token.description = str(request.POST.get('description', ''))
    token.allowed_ips = str(request.POST.get('allowed_ips', ''))
    # only allow writable tokens when user is read/write (i.e. not read_only!)
    token.write_enabled = False
    if not request.user.profile.read_only and str(request.POST.get("write_enabled", "")) == "on":
        token.write_enabled = True

    # handle expiration, if any
    expires = str(request.POST.get('expires', ''))
    if expires:
        dprint(f"   token expires = '{expires}'")
        # parse ISO time from html datetime-localtime input element.
        # make sure we add timezone support!
        token.expires = timezone.make_aware(datetime.fromisoformat(expires))
    if settings.API_MAX_TOKEN_DURATION:  # need to set max age!
        max_expire = timezone.now() + timedelta(settings.API_MAX_TOKEN_DURATION)
        if not token.expires or token.expires > max_expire:
            token.expires = max_expire

    # time to save the token:
    try:
        token.save()
    except Exception as err:
        error = Error()
        error.description = "Error saving API key!"
        error.details = str(err)
        return False, error

    info = Error()
    info.status = False  # not an error!
    if token.expires:
        info.description = f"Token {action}! Note: token expires on {token.expires}"
    else:
        info.description = f"Token {action}!"
    return True, info
