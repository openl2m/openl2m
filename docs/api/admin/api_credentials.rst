.. image:: ../../_static/openl2m_logo.png

=====================
Credentials Admin API
=====================

Credentials, aka Netmiko Profiles, are used for SSH, REST, and other access methods that require username and password.

There are two parts of the Credentials admin api:

Get Credential Profiles
-----------------------

The "/api/switches/netmikoprofiles/" GET endpoint returns a list of all Netmiko/Credientials Profiles.

Here is an example call:

.. code-block:: python

    http http://localhost:8000/api/admin/switches/netmikoprofiles/ 'Authorization: Token ***34b'

The returned data will look similar to this:

.. code-block:: python

    HTTP/1.1 200 OK
    ...

    [
        {
            "description": "",
            "device_type": "cisco",
            "id": 1,
            "name": "Department X SSH Creds",
            "tcp_port": 22,
            "username": "admin",
            "verify_hostkey": false
        },
        ...
        more credentials
        ...
    ]


Add Credentials Profile
-----------------------

The "/api/switches/netmikoprofiles/" POST endpoint allows you to create a new Credentials Profile.
The new object will be returned if the call succeeds.

Here is an example call.

.. code-block:: python

    http --form POST http://localhost:8000/api/admin/switches/netmikoprofiles/ 'Authorization: Token ***34b' args-to-be-added


and the example output:

.. code-block:: python

    HTTP/1.1 201 Created
    ...
    {
    TBD
    }

.. note::

    You will need the returned Profile *id* for future update calls.


Get Credentials Details
-----------------------

The "/api/switches/netmikoprofiles/<id>/" GET endpoint returns the details about a specific Credential Profile object.

The returned data is identical to the "create" data in the above example.

Example:

.. code-block:: python

    http http://localhost:8000/api/admin/switches/netmikoprofiles/3/ 'Authorization: Token ***34b'


Set Credential Profile Attributes
---------------------------------

The "/api/switches/netmikoprofiles/<id>/" POST (or PATCH) endpoint allows you to change attributes of a
specific profile object. You can change one or more at the same time.

The returned data is identical to the "create" data in the above example.

Example:

.. code-block:: python

    http --form POST http://localhost:8000/api/admin/switches/netmikoprofiles/3/ 'Authorization: Token ***34b' arguments_to_be_added