.. image:: ../../_static/openl2m_logo.png

======================
Switch Group Admin API
======================

There are two parts of the Switch Group admin api:

Get Switch Groups
-----------------

The "/api/switches/switchgroups/" GET endpoint returns a list of all Switch Groups.

Here is an example call:

.. code-block:: python

    http http://localhost:8000/api/admin/switches/switchgroups/ 'Authorization: Token ***34b'

The returned data will look similar to this:

.. code-block:: python

    HTTP/1.1 200 OK
    ...

    [
        {
            "allow_all_vlans": true,
            "allow_poe_toggle": true,
            "bulk_edit": true,
            "comments": "",
            "description": "Device for Department X",
            "display_name": "",
            "edit_if_descr": true,
            "id": 1,
            "name": "Department X",
            "read_only": false,
            "switches": [
                1,
                14,
                2,
                3,
                15
            ],
            "users": [
                4,
                5,
                12
            ],
            "vlan_groups": [],
            "vlans": []
        },
        ...
        more Groups
        ...
    ]


Add Switch Group
----------------

The "/api/switches/switchgroups/" POST endpoint allows you to create a new Switch Group.
The new object will be returned if the call succeeds. Valid field names are as shown in the above output example.

Here is an example call. The minimum required field is *name*:

.. code-block:: python

    http --form POST http://localhost:8000/api/admin/switches/switchgroups/ 'Authorization: Token ***34b' name="New Group"


and the example output:

.. code-block:: python

    HTTP/1.1 201 Created
    ...
    {
        "allow_all_vlans": false,
        "allow_poe_toggle": false,
        "bulk_edit": false,
        "comments": "",
        "description": "",
        "display_name": "",
        "edit_if_descr": false,
        "id": 4,
        "name": "New Group",
        "read_only": false,
        "switches": [],
        "users": [],
        "vlan_groups": [],
        "vlans": []
    }


.. note::

    You will need the returned Switch Group *id* for future update calls.

Add Switch Group with switches
------------------------------

ßTo add some switches (devices) to the new group as it is being created, add the switch IDs as shown here.
Set (add) additional fields as required. Field values are as shown in the above output example.

.. code-block:: python


Get Switch Group Details
------------------------

The "/api/switches/switchgroups/<id>/" GET endpoint returns the details about a specific Switch Group object.

The returned data is identical to the "create" data in the above example.

Example:

.. code-block:: python

    http http://localhost:8000/api/admin/switches/switchgroups/2/ 'Authorization: Token ***34b'


Set Switch Group Attributes
---------------------------

The "/api/switches/switchgroups/<id>/" POST (or PATCH) endpoint allows you to change attributes of a
specific Switch Group object. You can change one or more at the same time.

The returned data is identical to the "create" data in the above example.

Example:

.. code-block:: python

    http --form POST http://localhost:8000/api/admin/switches/switchgroups/2/ 'Authorization: Token ***34b' arguments_to_be_added