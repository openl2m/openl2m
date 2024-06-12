.. image:: ../../_static/openl2m_logo.png

==================
Switches Admin API
==================

There are two parts of the Switches (i.e. Devices) admin api:

Get Switches
------------

The "/api/admin/switches/" GET endpoint returns a list of Switches (i.e. Devices) in OpenL2M.

Here is an example call:

.. code-block:: python

    http http://localhost:8000/api/admin/switches/ 'Authorization: Token ***34b'

This returns something similar to:

.. code-block:: python

    HTTP/1.1 200 OK
    ...

    [
        {
            "allow_poe_toggle": true,
            "bulk_edit": true,
            "command_list": 2,
            "command_templates": [
                2,
                1
            ],
            "comments": "",
            "connector_type": 0,
            "default_view": 0,
            "description": "Some Interesting Switch",
            "edit_if_descr": true,
            "hostname": "switch1.local",
            "id": 1,
            "indent_level": 0,
            "name": "switch-1",
            "napalm_device_type": null,
            "netmiko_profile": null,
            "nms_id": null,
            "primary_ip4": "192.168.1.100",
            "read_only": false,
            "snmp_profile": 1,
            "status": 1
            "switchgroups": [
                1,
                3,
                12
            ]
        },
        ...
        <more devices>
        ...
    ]


Note that **snmp_profile** and **netmiko_profile** refer to ID's of those objects.
See below for accessing these objects via the API.

**command** and **command_list** refer to ID of those object,
and they are current not available via the API.

Switches also belong to SwitchGroups, but membership can only be read (or added)
from the SwitchGroup objects. See below for API access.

Adding Devices
--------------

The "/api/admin/switches/" POST endpoint allows you to add a new device (aka switch).
As a minimum, you need to provide a *name* and *address_ip4* device address.

Depending on the *'connector_type'*, some other fields are required:

**connector_type = 0** (SNMP), requires *'snmp_profile'* This is the default, if *connector_type* is omitted.

**connector_type = 1,2,98,99** (AosCX, PyEZ, Commands, Napalm), require a *netmiko_profile*.




Add SNMP Device
---------------

The new switch object will be returned if the call succeeds. Valid field names are as shown in the above output example.

Here is an example call. This creates a new devices, and adds it to switchgroups 1,2 and 3:

.. code-block:: python

    http --form POST http://localhost:8000/api/admin/switches/ 'Authorization: Token ***34b' name="New Device Name" primary_ip4="10.2.3.4" snmp_profile=3 switchgroups="1,2,3"


and the example output:

.. code-block:: python

    HTTP/1.1 201 Created
    ...
    {
        "allow_poe_toggle": false,
        "bulk_edit": false,
        "command_list": null,
        "command_templates": [],
        "comments": "",
        "connector_type": 0,
        "default_view": 0,
        "description": "",
        "edit_if_descr": false,
        "hostname": "",
        "id": 16,
        "indent_level": 0,
        "name": "New Device Name",
        "napalm_device_type": "",
        "netmiko_profile": null,
        "nms_id": null,
        "primary_ip4": "10.2.3.4",
        "read_only": false,
        "snmp_profile": 3,
        "status": 1,
        "switchgroups": [
            1,
            2,
            3
        ]
    }

.. note::

    You will need the returned user *id* for future update calls.


Get Switch Detail
-----------------

The "/api/admin/switches/<id>/" GET endpoint returns the details about a specific switch (device) object.

The returned data is identical to the "create" data in the above example.

Example:

.. code-block:: python

    http http://localhost:8000/api/admin/switches/3/ 'Authorization: Token ***34b'


Set Switch Attributes
---------------------

The "/api/admin/switches/<id>/" POST (or PATCH) endpoint allows you to change attributes of a specific switch object.
You can change one or more attributes (fields) at the same time.

The returned data is identical to the "create" data in the above example.

Example:

.. code-block:: python

    http --form POST http://localhost:8000/api/admin/switches/3/ 'Authorization: Token ***34b' arguments-to-be-changed