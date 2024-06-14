.. image:: ../../_static/openl2m_logo.png

===============
Users Admin API
===============

There are two parts of the users admin api:

Get Users
---------

The "/api/admin/users/" GET endpoint returns a list of users in OpenL2M.

Here is an example call:

.. code-block:: python

    http http://localhost:8000/api/admin/users/ 'Authorization: Token ***34b'

This returns the list of users:

.. code-block:: python

    HTTP/1.1 200 OK
    ...

    [
        {
            "date_joined": "2024-06-04T22:25:58.747427Z",
            "email": "jdoe@localhost",
            "first_name": "Jane",
            "groups": [],
            "id": 12,
            "is_active": true,
            "is_staff": false,
            "is_superuser": true,
            "last_login": "2024-06-04T22:26:38.834121Z",
            "last_name": "Doe",
            "password": "pbkdf2_sha256$720000$***=",
            "profile": 12,
            "user_permissions": [],
            "username": "jane.doe"
        },
        ...
        more users
        ...
    ]

.. note::

    The user profile details are not available from the 'all users' list.
    To see profile details, see *Get User Details* below.


Add a New User
--------------

The "/api/admin/users/" POST endpoint allows you to create a new user account.
The new account object will be returned if the call succeeds. Valid field names are as shown in the above output example.

Here is an example call. Note that *username* and *password* are required fields!
This example also sets a few fields of the new user's profile.

.. code-block:: python

    http --form POST http://localhost:8000/api/admin/users/ 'Authorization: Token ***34b' first_name="Jane" last_name="Doe" email="jane.doe@test.com" username="jane123" password="my_new_password" profile='{"allow_poe_toggle": false, "are_you_sure": false, "theme": "dark"}'

and the example output:

.. code-block:: python

    HTTP/1.1 201 Created
    ...
    {
        "date_joined": "2024-06-05T19:09:51.365106Z",
        "email": "jane.doe@test.com",
        "first_name": "Jane",
        "groups": [],
        "id": 25,
        "is_active": true,
        "is_staff": false,
        "is_superuser": false,
        "last_login": null,
        "last_name": "Doe",
        "password": "pbkdf2_sha256$720000$NAq8rXDnTLT80a0OiWYtcB$F2wiyYH/yZkEi8ZFHr/kRyQvHg4GfdGsPkJoKlwfEWE=",
        "profile": {
            "allow_poe_toggle": false,
            "are_you_sure": false,
            "bulk_edit": true,
            "edit_if_descr": true,
            "id": 25,
            "last_ldap_dn": "",
            "last_ldap_login": null,
            "read_only": false,
            "theme": "dark",
            "user": 25,
            "vlan_edit": false
        },
        "user_permissions": [],
        "username": "jane123"
    }

.. note::

    You will need the returned user *id* for future update calls.

.. warning::

    Profile fields need to be properly encoded as a JSON dictionary when adding new users, as shown above.


Get Users Details
-----------------

The "/api/admin/users/<id>/" GET endpoint returns the details about a specific user object.

The returned data is identical to the "add user" data in the above example. It includes the profile fields.

Example:

.. code-block:: python

    http http://localhost:8000/api/admin/users/25/ 'Authorization: Token ***34b'


Set User Attributes
-------------------

The "/api/admin/users/<id>/" POST (or PATCH) endpoint allows you to change attributes of a specific user object. You can change one or more fields at the same time.

The returned data is identical to the "create user" data in the above example.

**Example: Change the password.**

.. code-block:: python

    http --form POST http://localhost:8000/api/admin/users/25/ 'Authorization: Token ***34b' password="new_password"


**Example: Set a single field in the user profile.**

.. code-block:: python

    http --form POST http://192.168.1.41:8000/api/admin/users/25/ 'Authorization: Token ***34b' profile='{"theme": "light"}'


As stated above, Profile fields need to be properly encoded as a JSON dictionary when updating a user, as shown above.