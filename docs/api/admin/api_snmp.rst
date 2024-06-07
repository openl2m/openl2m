.. image:: ../../_static/openl2m_logo.png

==============
SNMP Admin API
==============

There are two parts of the SNMP admin api:

Get SNMP Profiles
-----------------

The "/api/switches/snmpprofiles/" GET endpoint returns a list of all SNMP Profiles.

Here is an example call:

.. code-block:: python

    http http://localhost:8000/api/admin/switches/snmpprofiles/ 'Authorization: Token ***34b'

The returned data will look similar to this:

.. code-block:: python

    HTTP/1.1 200 OK
    ...
    [
        {
            "auth_protocol": 2,
            "community": "public",
            "context_engine_id": null,
            "context_name": null,
            "description": "",
            "id": 1,
            "name": "v2-read-only",
            "passphrase": null,
            "priv_passphrase": null,
            "priv_protocol": 3,
            "sec_level": 2,
            "udp_port": 161,
            "username": null,
            "version": 2
        },
        ...
        more snmp profiles
        ...
    ]

Note this is a V2 snmp profile, so *passphrases*, *priv_protocol* and *sec_level* are don't cares.


Add SNMP Profile
----------------

The "/api/switches/snmpprofiles/" POST endpoint allows you to create a new SNMP Profile.
The new object will be returned if the call succeeds. Valid field names are as shown in the above output example.

Here is an example call to create a new SNMP v2 profile:

.. code-block:: python

    http --form POST http://localhost:8000/api/admin/switches/snmpprofiles/ 'Authorization: Token ***34b' name="New SNMP v2" community="private" version="2"


and the example output:

.. code-block:: python

    HTTP/1.1 201 Created
    ...
    {
        "auth_protocol": 2,
        "community": "private",
        "context_engine_id": null,
        "context_name": null,
        "description": "",
        "id": 5,
        "name": "New SNMP v2",
        "priv_protocol": 3,
        "sec_level": 2,
        "udp_port": 161,
        "username": null,
        "version": 2
    }

.. note::

    You will need the returned SNMP Profile *id* for future update calls.

For SNMP v3, you will need to set the following values.

For *auth_protocol*:

MD5 = 1
SHA = 2

For *priv_protocol*:

DES = 1
AES = 3

and for *sec_level*:

NOAUTH_NOPRIV = 0
AUTH_NOPRIV = 1
AUTH_PRIV = 2


Other values may be supported in the future, please see the source code for more details at
https://github.com/openl2m/openl2m/blob/main/openl2m/switches/constants.py


Get SNMP Details
----------------

The "/api/switches/snmpprofiles/<id>/" GET endpoint returns the details about a specific SNMP Profile object.

The returned data is identical to the "create" data in the above example.

Example:

.. code-block:: python

    http http://localhost:8000/api/admin/switches/snmpprofiles/5/ 'Authorization: Token ***34b'


Set SNMP Profile Attributes
---------------------------

The "/api/switches/snmpprofiles/<id>/" POST (or PATCH) endpoint allows you to change attributes of a
specific Profile object. You can change one or more at the same time.

The returned data is identical to the "create" data in the above example.

Example:

.. code-block:: python

    http --form POST http://localhost:8000/api/admin/switches/snmpprofiles/5/ 'Authorization: Token ***34b' arguments_to_be_added