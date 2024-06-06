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
            "context_engine_id": null,
            "context_name": null,
            "description": "",
            "id": 1,
            "name": "v2-read-only",
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

Note this is a V2 snmp profile, so *priv_protocol* and *sec_level* are don't cares.
Community and V3 pass phrases are not shown for obvious reasons!

Add SNMP Profile
----------------

The "/api/switches/snmpprofiles/" POST endpoint allows you to create a new SNMP Profile.
The new object will be returned if the call succeeds.

Here is an example call.

.. code-block:: python

    http --form POST http://localhost:8000/api/admin/switches/snmpprofiles/ 'Authorization: Token ***34b' args-to-be-added

and the example output:

.. code-block:: python

    HTTP/1.1 201 Created
    ...
    {
    TBD
    }

.. note::

    You will need the returned SNMP Profile *id* for future update calls.


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