.. image:: ../../_static/openl2m_logo.png

============
API Overview
============

We have implemented a REST API. This uses the Django Rest Framework, see https://www.django-rest-framework.org/

Installation is mostly standard, see https://www.django-rest-framework.org/#installation

:doc:`Additional REST API References<references>`

Custom Authentication
---------------------

API authentication is configured in *openl2m/settings.py*, and would typically look something like this:

.. code-block:: python

    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework.authentication.TokenAuthentication",
            "rest_framework.authentication.SessionAuthentication",  # useful for AJAX calls from web ui clients.
        ]
    }

We use a custom *Token()* class, defined in *users/models.py*. This adds some extra fields,
such as expiration time, permitted client IP, etc. (Note: this is copied from the Netbox code)

The authentication against this token is implemented in the TokenAuthentication() class in *openl2m/api/authentication.py*

So we have modified the authentication stanza as follows, to use our custom class for token auth:

.. code-block:: python

    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "openl2m.api.authentication.TokenAuthentication",  # custom Token(), adopted from Netbox.
            "rest_framework.authentication.SessionAuthentication",  # useful for AJAX calls from web ui clients.
        ]
    }

API Root
--------

API urls are defined in openl2m/urls.py, under the *api/* path. We define the root,
and an endpoint called *api/stats/* that returns some statistics about OpenL2M.

Here, we also include API paths to the various apps that implement API extensions.

E.g. the API paths below */api/switches/* come from the file *switches/api/urls.py*,
which maps to specific functions or classes for each api url.

The API root is defined in openl2m/views.py, in *class APIRootView()*,
as is the statistics endpoint in *class APIStatsView()*.


Switches API
------------

Switches app API endpoints are defined in *switches/api/urls.py*,
and the implementations of those are in *switches/api/views.py*

All API endpoints are :doc:`documented here.<../../api/endpoints>`

Code has been refactored, such that both the WEB UI, and the API use the same functions to perform actions.
Ie. both *switches/views.py* and *switches/api/views.py* now call various *perform_xyz()* functions implemented in *switches/actions.py*

This ensures that security, and actions are identical, independent of the path to the action (WEB UI or API).


Users API
---------

Users app API endpoints are defined in *users/api/urls.py*,
and the implementations of those are in *users/api/views.py*

All API endpoints are :doc:`documented here.<../../api/endpoints>`

At time of this writing, the Users API only implemented the 'get token' call, at /api/users/token.
