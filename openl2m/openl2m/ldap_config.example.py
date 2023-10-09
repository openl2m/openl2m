# this is an example LDAP authentication Configuration
# this works with Windows AD servers, and uses secure ldap
import ldap
from django_auth_ldap.config import LDAPSearch, NestedGroupOfNamesType


#############################
# Server Authentication part:

# Server URI
AUTH_LDAP_SERVER_URI = "ldaps://dc.yourdomain.com:3269"

# The following may be needed if you are binding to Active Directory.
AUTH_LDAP_CONNECTION_OPTIONS = {ldap.OPT_REFERRALS: 0}

# Set the DN and password for the OpenL2M service account.
AUTH_LDAP_BIND_DN = "CN=openl2m,OU=services,DC=yoursite,DC=yourdomain,DC=com"
AUTH_LDAP_BIND_PASSWORD = "your-password"

# Include this setting if you want to ignore certificate errors. This might be needed to accept a self-signed cert.
# Note that this is a OpenL2M-specific setting which sets:
#     ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
LDAP_IGNORE_CERT_ERRORS = True

#############################
# User Authentication part: #
#############################

# This search matches users with the sAMAccountName equal to the provided username. This is required if the user's
# username is not in their DN (Active Directory).
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "OU=baseou,DC=yoursite,DC=yourdomain,DC=com", ldap.SCOPE_SUBTREE, "(sAMAccountName=%(user)s)"
)

# If a user's DN is producible from their username, we don't need to search.
# When using Windows Server 2012, AUTH_LDAP_USER_DN_TEMPLATE should be set to None.
# AUTH_LDAP_USER_DN_TEMPLATE = "uid=%(user)s,ou=users,dc=example,dc=com"
AUTH_LDAP_USER_DN_TEMPLATE = None

# You can map user attributes to Django attributes as so.
AUTH_LDAP_USER_ATTR_MAP = {"first_name": "givenName", "last_name": "sn", "email": "mail"}


#############################
# Group and other settings: #
#############################

# This search ought to return all groups to which the user belongs. django_auth_ldap uses this to determine group
# hierarchy.
AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    "OU=groups,DC=yoursite,DC=yourdomain,DC=com", ldap.SCOPE_SUBTREE, "(objectClass=group)"
)
AUTH_LDAP_GROUP_TYPE = NestedGroupOfNamesType()

# Define a group required to login.
AUTH_LDAP_REQUIRE_GROUP = "CN=openl2m-users,OU=groups,DC=yoursite,DC=yourdomain,DC=com"

# Do NOT Mirror LDAP group assignments.
AUTH_LDAP_MIRROR_GROUPS = False

# Define special user types using groups. Exercise great caution when assigning superuser status.
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    # is_active: users that can login to OpenL2M:
    "is_active": "CN=openl2m-users,OU=groups,DC=yoursite,DC=yourdomain,DC=com",
    # is_staff: users that have access to the "Admin" tab under profile
    #    "is_staff": "CN=openl2m-staff,OU=groups,DC=yoursite,DC=yourdomain,DC=com",
    # is_superuser: users that can do anything!
    #    "is_superuser": "CN=openl2m-superusers,OU=groups,DC=yoursite,DC=yourdomain,DC=com",
}

# For more granular permissions, we can map LDAP groups to Django groups.
AUTH_LDAP_FIND_GROUP_PERMS = False

# Cache groups for one hour to reduce LDAP traffic
AUTH_LDAP_CACHE_GROUPS = True
AUTH_LDAP_GROUP_CACHE_TIMEOUT = 3600

# Map LDAP group membership to SwitchGroup membership with this regular expression.
# if matched, the first match hit, ie. match[1], will be used as a SwitchGroup name.
# eg. "^switches-([\w\d\s-]+)$"  matches "switches-group1" and
# creates a SwitchGroup named "group1"
# If not set, or no matches, SwitchGroup() objects will NOT be created!
AUTH_LDAP_GROUP_TO_SWITCHGROUP_REGEX = "^switches-([\w\d\s-]+)$"
