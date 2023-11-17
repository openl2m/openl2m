.. image:: ../_static/openl2m_logo.png

========
API Menu
========

The "Menu" endpoint returns a list of devices you can access with your token.

Here is an example of a call to the "menu" endpoint:

.. code-block:: python

    http http://localhost:8000/api/switches/ 'Authorization: Token ***34b'

It returns a dictionary with 2 keys, "groups",  and "user".

**The "groups" entry:**

This is a dictionary of items, where the key is the group ID.

The items of each group are a series of named attributes for the group, and the device "members".

"members" is a dictionary of one or more devices, where the key is the device ID,
and the value is a dictionary of attributes of that device.

**The "user" entry:**

This dictionary contains the username for this token, and some permissions flags.

Example output
--------------

The example below shows 2 groups (#2 and #35), with one (#54) and three (#272, #623, #703) devices respectively.

.. code-block:: python

    {
        "groups": {
            "2": {
                "comments": "",
                "description": "",
                "display_name": "Test Group #1",
                "members": {
                    "54": {
                        "comments": "",
                        "connector_type": 0,
                        "connector_type_name": "SNMP",
                        "default_view": 1,
                        "default_view_name": "Details",
                        "description": "The big, bad device!",
                        "hostname": "my_device_1",
                        "indent_level": 0,
                        "name": "My Device #1",
                        "primary_ipv4": "192.168.100.100",
                        "read_only": true,
                        "url": "http://localhost:8000/api/switches/details/2/54/",
                        "url_add_vlan": "http://localhost:8000/api/switches/vlan/add/2/54/"
                    },
                },
                "name": "Test-Group-1",
                "read_only": True
            },
            "35": {
                "comments": "",
                "description": "Test Group Description!",
                "display_name": "",
                "members": {
                    "272": {
                        "comments": "Test switch",
                        "connector_type": 0,
                        "connector_type_name": "SNMP",
                        "default_view": 0,
                        "default_view_name": "Basic",
                        "description": "",
                        "hostname": "TEST-LAB-5130",
                        "indent_level": 1,
                        "name": "TEST-LAB 5130",
                        "primary_ipv4": "10.100.100.100",
                        "read_only": false,
                        "url": "http://localhost:8000/api/switches/basic/35/272/",
                        "url_add_vlan": "http://localhost:8000/api/switches/vlan/add/35/272/"
                    },
                    "623": {
                        "comments": "",
                        "connector_type": 1,
                        "connector_type_name": "Aruba AOS-CX",
                        "default_view": 0,
                        "default_view_name": "Details",
                        "description": "CX6300 test switch in lab",
                        "hostname": "aos-cx-test-switch",
                        "indent_level": 1,
                        "name": "AOS-CX-Test",
                        "primary_ipv4": "10.100.100.101",
                        "read_only": false,
                        "url": "http://localhost:8000/api/switches/basic/35/623/",
                        "url_add_vlan": "http://localhost:8000/api/switches/vlan/add/35/623/"
                    },
                    "703": {
                        "comments": "",
                        "connector_type": 2,
                        "connector_type_name": "Junos (PyEZ)",
                        "default_view": 0,
                        "default_view_name": "Basic",
                        "description": "Juniper EX2300 Test Switch in Lab",
                        "hostname": "ex2300-test-switch",
                        "indent_level": 1,
                        "name": "Junos-EX2300-TEST",
                        "primary_ipv4": "10.100.100.102",
                        "read_only": false,
                        "url": "http://localhost:8000/api/switches/basic/35/703/",
                        "url_add_vlan": "http://localhost:8000/api/switches/vlan/add/35/703/"
                    },
                },
                "name": "Test-Group",
                "read_only": false
            },
        },
        "user": {
            "allow_poe_toggle": true,
            "edit_if_descr": true,
            "name": "user",
            "read_only": false,
            "vlan_edit": false
        }
    }