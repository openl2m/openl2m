.. image:: ../_static/openl2m_logo.png

=================
API Search Device
=================

This endpoint can be used to find a device and it's group membership.
You will need to know the OpenL2M device name or hostname for this call.
Note this same info can be found in the 'menu' API call,
only then you receive all devices your token allows to access.

Here is an example of calls to the "*search*" endpoint. This returns switch and group information:

.. code-block:: python

    http http://localhost:8000/api/switches/search/<name>/ 'Authorization: Token ***34b'


Make sure your use proper URL encoding if the name contains spaces, etc.


Example output
--------------

The abbreviated example output below is from the search for '*switch-1*'.
It shows information about the switch, and the groups it is a member of.
Note the group information contains the REST url to access the device using that group.

.. code-block:: python

    http http://localhost:8000/api/switches/search/switch-1/ 'Authorization: Token ***34b'

    HTTP/1.1 200 OK
    ...
    {
        "groups": {
            "12": {
                "description": "Group Twelve",
                "id": "12",
                "name": "group-12",
                "read_only": false,
                "switch_url": "http://localhost:8000/api/switches/12/798/"
            },
            "27": {
                "description": "Another Group",
                "id": "27",
                "name": "group-27",
                "read_only": false,
                "switch_url": "http://localhost:8000/api/switches/27/798/"
            }
        },
        "switch": {
            "comments": "",
            "connector_type": 0,
            "connector_type_name": "SNMP",
            "default_view": 0,
            "default_view_name": "Basic",
            "description": "Switch 1",
            "hostname": "switch-1",
            "id": "798",
            "name": "switch-1",
            "nms_id": "",
            "primary_ipv4": "10.1.1.1",
            "read_only": false
        }
    }
