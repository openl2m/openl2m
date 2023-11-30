.. image:: ../_static/openl2m_logo.png

=================
API Configuration
=================

There are a number of settings related to the REST API of OpenL2M.

**Enable/disabled**

API access can be turn off. If this setting is False, API access is disabled:

.. code-block:: python

    API_ENABLED = True

**Limit IP access**

You can provide IP subnets to both deny, and permit client API access from.
The check order is deny, allow.

I.e. if a client IP is NOT on the deny list, and IS on the allow list, then API access is granted.
(Clients can futher be limited by a permit IP list as part of a specific access token!)

This is controlled by the following two settings, which can handle both IPv4 and IPv6 (once suppported)
subnets, in CIDR format. Multiple entries should be space delimited.

.. code-block:: python

    # If the API client IP is in this denied list, access is globally denied.
    # This is a comma-separated list of IPv4/IPv6 networks in CIDR notation.
    # Leave blank for no restrictions.
    API_CLIENT_IP_DENIED = ""

    # If the API client IP is in this allowed list, access is globally allowed.
    # Each Token can further restricted by setting the 'allowed_ips' attribute.
    # This is a comma-separated list of IPv4/IPv6 networks in CIDR notation
    # Leave blank for no restrictions.
    API_CLIENT_IP_ALLOWED = ""

**Max token age**

You can globally set a maximum token age. If set, when users try to create unlimited tokens,
or tokens with ages too long, the management interface will automatically set the token to
expired after the configured number of days.

.. code-block:: python

    # Max token duration, in days. If user sets token expiration beyond this number
    # of days into future, it will be limited to this number of days into future.
    # Ignored if 0.
    API_MAX_TOKEN_DURATION = 0

**Other options**

Finally, you can limited the number of API tokens per user, and if they can see the full token value
after creation. We recommend for security reasons you leave the latter to False
(i.e. Off, user cannot see full token again)

.. code-block:: python

    # if True, users can see their tokens again after they have been created.
    # if False, only last few chars will be shown.
    ALLOW_TOKEN_RETRIEVAL = False
    # maximum number of tokens per user
    MAX_API_TOKENS = 3
