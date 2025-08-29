.. image:: ../_static/openl2m_logo.png

==============
API Statistics
==============

The "Stats" endpoint returns some statistics and use information about the OpenL2M application.

.. code-block:: bash

     http --form POST https://<your-domain>/api/stats/ 'Authorization: Token <your-token-string-here>'

The equivalent *curl* example would be:

.. code-block:: bash

    curl https://<your-doimain>/api/stats/ -H 'Authorization: Token <your-token-string-here>'

Output
------

At the time of this writing, the output will look something like below. In the future, additional information may be added.

.. code-block:: bash

    HTTP/1.1 200 OK
    Allow: GET, HEAD, OPTIONS
    ...
    {
        "database": {
            "command_lists": 6,
            "commands": 27,
            "log_entries": 616,
            "Credentials_profiles": 9,
            "snmp_profiles": 10,
            "switch_groups": 33,
            "switches": 740,
            "vlan_groups": 18,
            "vlans": 292
        },
        "usage": {
            "api_calls_last_31_days": 43,
            "api_calls_last_7_days": 41,
            "api_calls_today": 19,
            "changes_last 31 days": 543,
            "changes_last 7 days": 141,
            "changes_today": 12,
            "commands_last_31_days": 18,
            "commands_last_7_days": 6,
            "commands_today": 1,
            "devices_last_31_days": 75,
            "devices_last_7_days": 34,
            "devices_today": 13,
            "total_changes": 29784,
            "total_commands": 1684
        }
    }
