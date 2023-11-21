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
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
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
        return render(
            request,
            self.template_name,
            {
                'user': request.user,
            },
        )


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
        else:
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


@login_required(redirect_field_name=None)
def token_delete(request, token_id):
    """Delete a token for a user.

    Args:
        request (HttpRequest): the request object
        token_id (int): the pk of the Token() to delete.

    Returns:
        HttpResponse: calls either error_page() or success_page() to return HttpResponse.
    """

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
    else:
        log.action = LOG_REST_API_TOKEN_DELETE
        log.description = f"API Key deleted! (id={token_id}, token={partial_token})"
        log.save()
        return success_page(request=request, group=None, switch=None, description=log.description)


@login_required(redirect_field_name=None)
def token_edit(request, token_id):
    """Edit a token for a user.

    Args:
        request (HttpRequest): the request object
        token_id (int): the pk of the Token() to delete.

    Returns:
        HttpResponse: calls either error_page() or success_page() to return HttpResponse.
    """
    template_name = "users/token_edit.html"

    log = Log(
        type=LOG_TYPE_CHANGE,
        action=LOG_REST_API_TOKEN_EDIT,
        user=request.user,
        ip_address=get_remote_ip(request),
    )
    if request.method == "GET":
        try:
            token = Token.objects.get(user=request.user, id=token_id)
        except Exception as err:
            error = Error()
            error.description = "Error editing API key!"
            error.details = str(err)
            log.type = LOG_TYPE_ERROR
            log.description = f"Error editing API key ({partial_token})!"
            log.save()
            return error_page(request=request, group=None, switch=None, error=error)
        else:
            return render(
                request,
                template_name,
                {
                    'action': 'edit',
                    'request': request,
                    'token': token,
                },
            )
    elif request.method == "POST":
        # save this token!
        try:
            token = Token.objects.get(user=request.user, id=token_id)
        except Exception as err:
            error = Error()
            error.description = "Error updating API key!"
            error.details = str(err)
            log.type = LOG_TYPE_ERROR
            log.description = f"Error updating API key (id={token_id}, err={err})!"
            log.save()
            return error_page(request=request, group=None, switch=None, error=error)
        else:
            token.description = str(request.POST.get('description', ''))
            expires = str(request.POST.get('expires', ''))
            dprint(f"EXPIRES = '{expires}'")
            if expires:
                dprint("  SETTING!")
                token.expires = expires
            token.allowed_ips = str(request.POST.get('allowed_ips', ''))
            if str(request.POST.get("write_enabled", "")) == "on":
                token.write_enabled = True
            else:
                token.write_enabled = False
            try:
                token.save()
            except Exception as err:
                log.type = LOG_TYPE_ERROR
                log.description = f"Error updating API key (id={token_id}, err={err})!"
                log.save()
                error = Error()
                error.description = "Error updating API key!"
                error.details = str(err)
                return error_page(request=request, group=None, switch=None, error=error)

            else:
                log.description = f"Token updated (id={token.id}, partial={token.partial})"
                return success_page(request=request, group=None, switch=None, description="Token updated successfully!")

        error = Error()
        error.description = "POST not implemented yet!"
        return error_page(request=request, group=None, switch=None, error=error)

    # unsupported HTTP method
    log.type = LOG_TYPE_ERROR
    log.description = f"Unsupported Request method: {request.method}"
    log.save()
    error = Error()
    error.description = "Unknown HTTP Method!"
    error.details = log.description
    return error_page(request=request, group=None, switch=None, error=error)


@login_required(redirect_field_name=None)
def token_add(request):
    """Add a token for a user. Either GET or POST method.

    Args:
        request (HttpRequest): the request object

    Returns:
        HttpResponse: calls either error_page() or success_page() to return HttpResponse.
    """
    template_name = "users/token_edit.html"

    count = Token.objects.filter(user=request.user).count()
    if count >= settings.MAX_API_TOKENS:
        error = Error()
        error.description = f"You cannot create more API tokens (max = { settings.MAX_API_TOKENS })"
        return error_page(request=request, group=None, switch=None, error=error)

    if request.method == "GET":
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

    elif request.method == "POST":
        log = Log(
            type=LOG_TYPE_CHANGE,
            action=LOG_REST_API_TOKEN_CREATED,
            user=request.user,
            ip_address=get_remote_ip(request),
        )
        # save this token!
        token = Token()
        token.user = request.user
        token.description = str(request.POST.get('description', ''))
        token.allowed_ips = str(request.POST.get('allowed_ips', ''))
        token.key = request.POST.get('key', '')
        if not token.key:
            log.type = LOG_TYPE_ERROR
            log.description = "Invalid new API token, key not set!"
            log.save()
            error = Error()
            error.description = log.description
            return error_page(request=request, group=None, switch=None, error=error)
        try:
            token.save()
        except Exception as err:
            error = Error()
            error.description = "Error saving API key!"
            error.details = str(err)
            log.type = LOG_TYPE_ERROR
            log.description = f"Error saving API key!"
            log.save()
            return error_page(request=request, group=None, switch=None, error=error)
        else:
            log.description = f"Token created! (partial={token.partial})"
            log.save()
            return success_page(request=request, group=None, switch=None, description="Token created!")

    # unsupported HTTP method
    log.type = LOG_TYPE_ERROR
    log.description = f"Unsupported Request method: {request.method}"
    log.save()
    error = Error()
    error.description = "Unknown HTTP Method!"
    error.details = log.description
    return error_page(request=request, group=None, switch=None, error=error)
