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
            "enable_password": "enable_me",
            "id": 1,
            "name": "Department X SSH Creds",
            "password": "secret",
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
The new object will be returned if the call succeeds. Valid field names are as shown in the above output example.

Here is an example call.

.. code-block:: python

    http --form POST http://localhost:8000/api/admin/switches/netmikoprofiles/ 'Authorization: Token ***34b' name="Dept. Y SSH" description="Test SSH access" username="user" password="secret" tcp_port=2022


and the example output:

.. code-block:: python

    HTTP/1.1 201 Created
    ...

    {
        "description": "Test SSH access",
        "device_type": "hp_comware",
        "enable_password": null,
        "id": 2,
        "name": "Dept. Y SSH",
        "password": "secret",
        "tcp_port": 2022,
        "username": "user",
        "verify_hostkey": false
    }

For *device_type* you need to use a Netmiko device name that matches your device.
See the supported list at https://github.com/openl2m/openl2m/blob/main/openl2m/switches/connect/netmiko/constants.py

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
specific profile object. You can change one or more fields at the same time.

The returned data is identical to the "create" data in the above example.

Example:

.. code-block:: python

    http --form POST http://localhost:8000/api/admin/switches/netmikoprofiles/3/ 'Authorization: Token ***34b' arguments_to_be_added