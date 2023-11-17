.. image:: ../_static/openl2m_logo.png

======================
API Basic/Details Info
======================

These endpoints return the interface information of a device.

If the *details* call is made, additionally Ethernet, ARP and LLDP info will be returned.
(*Note: this takes longer!*)

Here is an example of calls to the "basic" and"details" endpoints:

.. code-block:: python

    http http://localhost:8000/api/switches/basic/35/272/ 'Authorization: Token ***34b'
    http http://localhost:8000/api/switches/details/35/272/ 'Authorization: Token ***34b'


It returns a dictionary with 2 keys, "interfaces", "switch" and "vlans".

**The "interfaces" entry:**

This is a list of interfaces of the device. The "id" field is what is required in interface specific API call.

The main difference between the "basic" and the "details" call is the latter showing the entries for *"ethernet_addresses": []* and *"neighbors": []*
If there are know ethernet addresses or LLDP neighbors, these will contains lists of data.

**The "switch" entry:**

This is a dictionary show the username for this token, and some permissions flags.

**The "vlans" entry:**

This is a dictionary of the vlans defined on the device, and various attributes about those vlans. The key is the vlan id.


Example output
--------------

The abbreviated example output below shows several interfaces, and the switch information.

.. code-block:: python

    {
        "interfaces": [
            {
                "description": "GigabitEthernet1/0/1 Interface",
                "duplex": "Unknown",
                "ethernet_addresses": [],
                "id": "1",
                "manageable": false,
                "mode": "Access",
                "name": "GigabitEthernet1/0/1",
                "neighbors": [],
                "online": false,
                "poe": {
                    "admin_status": "Enabled",
                    "detect_status": "Searching",
                    "max_power_consumed": 0,
                    "power_available": 0,
                    "power_consumed": 0,
                    "power_consumption_supported": true
                },
                "speed": 1000,
                "state": "Enabled",
                "unmanage_reason": "Interface access denied: you do not have access to the interface vlan!",
                "url_set_description": "http://localhost:8000/api/switches/interface/description/35/272/1/",
                "url_set_poe_state": "http://localhost:8000/api/switches/interface/poe_state/35/272/1/",
                "url_set_state": "http://localhost:8000/api/switches/interface/state/35/272/1/",
                "url_set_vlan": "http://localhost:8000/api/switches/interface/vlan/35/272/1/",
                "vlan": 1097
            },
            ...
            {
                "description": "TESTING",
                "duplex": "Unknown",
                "ethernet_addresses": [],
                "id": "3",
                "manageable": true,
                "mode": "Tagged",
                "name": "GigabitEthernet1/0/3",
                "neighbors": [],
                "online": false,
                "poe": {
                    "admin_status": "Disabled",
                    "detect_status": "Disabled",
                    "max_power_consumed": 0,
                    "power_available": 0,
                    "power_consumed": 0,
                    "power_consumption_supported": true
                },
                "speed": 1000,
                "state": "Enabled",
                "tagged_vlans": "592, 591",
                "url_set_description": "http://localhost:8000/api/switches/interface/description/35/272/3/",
                "url_set_poe_state": "http://localhost:8000/api/switches/interface/poe_state/35/272/3/",
                "url_set_state": "http://localhost:8000/api/switches/interface/state/35/272/3/",
                "url_set_vlan": "http://localhost:8000/api/switches/interface/vlan/35/272/3/",
                "vlan": 1099
            },
            ...
            {
                "description": "Some description",
                "duplex": "Full",
                "ethernet_addresses": [
                    {
                        "address": "0011.2233.4455",
                        "hostname": "",
                        "ipv4": "",
                        "ipv6": "",
                        "vlan": 0
                    }
                ],
                "id": "29",
                "manageable": true,
                "mode": "Access",
                "name": "GigabitEthernet1/0/29",
                "neighbors": [],
                "online": true,
                "poe": {
                    "admin_status": "Enabled",
                    "detect_status": "Delivering",
                    "max_power_consumed": 0,
                    "power_available": 0,
                    "power_consumed": 3100,
                    "power_consumption_supported": true
                },
                "speed": 100,
                "state": "Enabled",
                "url_set_description": "http://localhost:8000/api/switches/interface/description/35/272/29/",
                "url_set_poe_state": "http://localhost:8000/api/switches/interface/poe_state/35/272/29/",
                "url_set_state": "http://localhost:8000/api/switches/interface/state/35/272/29/",
                "url_set_vlan": "http://localhost:8000/api/switches/interface/vlan/35/272/29/",
                "vlan": 98
            },
            ...
           {
                "description": "GigabitEthernet1/0/45 Interface",
                "duplex": "Full",
                "ethernet_addresses": [],
                "id": "45",
                "manageable": true,
                "mode": "Tagged",
                "name": "GigabitEthernet1/0/45",
                "neighbors": [
                    {
                        "capabilities": "TBD",
                        "hostname": "",
                        "port_description": "testing \"uplink\" to test lab",
                        "port_name": "",
                        "system_description": "HPE Comware Platform Software, Software Version 7.1.070, Release 3506P11\r\nHPE 5510 48G PoE+ 4SFP+ HI 1-slot Switch JH148A\r\nCopyright (c) 2010-2021 Hewlett Packard Enterprise Development LP",
                        "system_name": "5510-lab-switch"
                    }
                ],
                "online": true,
                "poe": {
                    "admin_status": "Enabled",
                    "detect_status": "Searching",
                    "max_power_consumed": 0,
                    "power_available": 0,
                    "power_consumed": 0,
                    "power_consumption_supported": true
                },
                "speed": 1000,
                "state": "Enabled",
                "tagged_vlans": "591",
                "url_set_description": "http://localhost:8000/api/switches/interface/description/35/272/45/",
                "url_set_poe_state": "http://localhost:8000/api/switches/interface/poe_state/35/272/45/",
                "url_set_state": "http://localhost:8000/api/switches/interface/state/35/272/45/",
                "url_set_vlan": "http://localhost:8000/api/switches/interface/vlan/35/272/45/",
                "vlan": 1
            },
        ],
        "switch": {
            "change_admin_status": true,
            "change_description": true,
            "change_poe": true,
            "change_vlan": true,
            "driver": "SnmpConnectorComware",
            "edit_vlans": true,
            "group": "Test-Group",
            "group_id": 35,
            "hostname": "TEST-LAB-5130",
            "id": 272,
            "name": "TEST-LAB 5130",
            "poe": {
                "enabled": 1,
                "max_power": 370,
                "power-supplies": [
                    {
                        "id": 4,
                        "max_power": 370,
                        "power_consumed": 3,
                        "status": "On",
                        "threshold": 80
                    }
                ],
                "power_consumed": 3
            },
            "primary_ipv4": "192.168.100.100",
            "read_only": false,
            "save_config": true,
            "url_add_vlan": [
                "http://localhost:8000/api/switches/vlan/add/35/272/"
            ],
            "url_save_config": [
                "http://localhost:8000/api/switches/save/35/272/"
            ],
            "vendor": "HPE (Comware)",
        },
        "vlans": [
            {
                "access": false,
                "id": 1,
                "igmp_snooping": false,
                "name": "VLAN 0001",
                "state": "Enabled",
                "status": "Permanent"
            },
            {
                "access": true,
                "id": 61,
                "igmp_snooping": true,
                "name": "test",
                "state": "Enabled",
                "status": "Permanent"
            },
            {
                "access": true,
                "id": 98,
                "igmp_snooping": true,
                "name": "VLAN 0098",
                "state": "Enabled",
                "status": "Permanent"
            },
            ...
        ]
        }
    }
