"""
This file as adapted from Netbox
"""
from django.conf import settings
from django.utils import timezone
from rest_framework import authentication, exceptions

from users.models import Token
from switches.utils import get_remote_ip, dprint

from switches.constants import LOG_TYPE_LOGIN_OUT, LOG_TYPE_ERROR, LOG_LOGIN_REST_API
from switches.models import Log

# FULL_URL_WITH_QUERY_STRING: request.build_absolute_uri()
# FULL_URL: request.build_absolute_uri('?')
# ABSOLUTE_ROOT: request.build_absolute_uri('/')[:-1].strip('/')
# ABSOLUTE_ROOT_URL: request.build_absolute_uri('/').strip('/')


class TokenAuthentication(authentication.TokenAuthentication):
    """
    A custom authentication scheme which enforces Token expiration times and source IP restrictions.
    """

    model = Token

    def authenticate(self, request):
        ip_address = get_remote_ip(request)
        url = f"{request.method}: {request.get_full_path_info()}"
        dprint(f"*** REST: authenticate() from {ip_address} for {url}")
        result = super().authenticate(request)  # this calls authenticate_credentials() below

        if result:
            dprint("  REST auth OK, checking token IP and Time")
            user = result[0]
            token = result[1]

            # Enforce source IP restrictions (if any) set on the token
            if token.allowed_ips:
                client_ip = get_remote_ip(request)
                if client_ip is None:
                    # log access denied!
                    log = Log(
                        user=user,
                        ip_address=ip_address,
                        # switch=None,
                        # # group=False,
                        action=LOG_LOGIN_REST_API,
                        type=LOG_TYPE_ERROR,
                        description=f"Could not get client IP. ({url})",
                    )
                    log.save()
                    raise exceptions.AuthenticationFailed(
                        "Client IP address could not be determined for validation. Check that the HTTP server is "
                        "correctly configured to pass the required header(s)."
                    )
                if not token.validate_client_ip(client_ip):
                    # log access denied!
                    log = Log(
                        user=user,
                        ip_address=ip_address,
                        # switch=None,
                        # # group=False,
                        action=LOG_LOGIN_REST_API,
                        type=LOG_TYPE_ERROR,
                        description=f"Invalid client IP. ({url})",
                    )
                    log.save()
                    raise exceptions.AuthenticationFailed(
                        f"Source IP {client_ip} is not permitted to authenticate using this token."
                    )

            # log access OK!
            log = Log(
                user=user,
                ip_address=ip_address,
                # switch=None,
                # # group=False,
                action=LOG_LOGIN_REST_API,
                type=LOG_TYPE_LOGIN_OUT,
                description=f"API login succeeded. ({url})",
            )
            log.save()

        else:
            dprint("  REST auth DENIED!")
            # log access denied!
            log = Log(
                # user=user,
                ip_address=ip_address,
                # switch=None,
                # # group=False,
                action=LOG_LOGIN_REST_API,
                type=LOG_TYPE_ERROR,
                description=f"Invalid token. ({url})",
            )
            log.save()

        return result

    def authenticate_credentials(self, key):
        dprint(f"*** REST: authenticate_credentials(key={key})")
        model = self.get_model()
        try:
            token = model.objects.prefetch_related('user').get(key=key)
        except model.DoesNotExist:
            # log access denied!
            log = Log(
                # user=user,
                # ip_address=ip_address,
                # switch=None,
                # # group=False,
                action=LOG_LOGIN_REST_API,
                type=LOG_TYPE_ERROR,
                description=f"Invalid Token.",
            )
            log.save()
            raise exceptions.AuthenticationFailed("Invalid token")

        # Update last used, but only once per minute at most. This reduces write load on the database
        if not token.last_used or (timezone.now() - token.last_used).total_seconds() > 60:
            # If maintenance mode is enabled, assume the database is read-only, and disable updating the token's
            # last_used time upon authentication.
            if settings.MAINTENANCE_MODE:
                logger = logging.getLogger('openl2m.auth.login')
                logger.debug("Maintenance mode enabled: Disabling update of token's last used timestamp")
            else:
                Token.objects.filter(pk=token.pk).update(last_used=timezone.now())

        # Enforce the Token's expiration time, if one has been set.
        if token.is_expired:
            # log access denied!
            log = Log(
                # user=user,
                # ip_address=ip_address,
                # switch=None,
                # # group=False,
                action=LOG_LOGIN_REST_API,
                type=LOG_TYPE_ERROR,
                description=f"Token has expired.",
            )
            log.save()
            raise exceptions.AuthenticationFailed("Token expired")

        user = token.user
        #
        # this needs work:
        #
        # # When LDAP authentication is active try to load user data from LDAP directory
        # if settings.LDAP_CONFIG is not None:
        #     from open.authentication import LDAPBackend
        #     ldap_backend = LDAPBackend()

        #     # Load from LDAP if FIND_GROUP_PERMS is active
        #     # Always query LDAP when user is not active, otherwise it is never activated again
        #     if ldap_backend.settings.FIND_GROUP_PERMS or not token.user.is_active:
        #         ldap_user = ldap_backend.populate_user(token.user.username)
        #         # If the user is found in the LDAP directory use it, if not fallback to the local user
        #         if ldap_user:
        #             user = ldap_user

        if not user.is_active:
            # log access denied!
            log = Log(
                user=user,
                # ip_address=ip_address,
                # switch=None,
                # # group=False,
                action=LOG_LOGIN_REST_API,
                type=LOG_TYPE_ERROR,
                description=f"User account is inactive.",
            )
            log.save()
            raise exceptions.AuthenticationFailed("User inactive")

        return user, token
