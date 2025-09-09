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
        'database': {
            'api_tokens': {'label': 'API Tokens', 'value': 2},
            'command_lists': {'label': 'Command Lists', 'value': 6},
            'commands': {'label': 'Commands', 'value': 26},
            'credentials_profiles': {'label': 'Credentials Profiles', 'value': 11},
            'log_entries': {'label': 'Log Entries', 'value': 4925},
            'snmp_profiles': {'label': 'SNMP Profiles', 'value': 20},
            'switches': {'label': 'Switches', 'value': 1246},
            'switchgroups': {'label': 'Switch Groups', 'value': 33},
            'vlan_groups': {'label': 'Vlan Groups', 'value': 19},
            'vlans': {'label': 'Vlans', 'value': 295}
            },
        'usage': {
            'api_calls_last_31_days': {'label': 'API calls last 31 days', 'value': 13},
           'api_calls_last_7_days': {'label': 'API calls last 7 days', 'value': 3},
           'api_calls_today': {'label': 'API calls today', 'value': 3},
           'changes_last_31_days': {'label': 'Changes last 31 days', 'value': 11},
           'changes_last_7_days': {'label': 'Changes last 7 days', 'value': 4},
            'changes_last_hour': {'label': 'Changes in last hour', 'value': 4},
           'changes_today': {'label': 'Changes today', 'value': 4},
           'changes_total': {'label': 'Total Changes', 'value': 39014},
           'commands_last_31_days': {'label': 'Commands last 31 days', 'value': 1},
           'commands_last_7_days': {'label': 'Commands last 7 days', 'value': 0},
           'commands_today': {'label': 'Commands today', 'value': 0},
           'commands_total': {'label': 'Total Commands', 'value': 1231},
           'devices_last_31_days': {'label': 'Devices Last 31 Days', 'value': 11},
           'devices_last_7_days': {'label': 'Devices last 7 days', 'value': 1},
           'devices_last_hour': {'label': 'Devices in last hour', 'value': 1},
           'devices_today': {'label': 'Devices today', 'value': 1},
           'users_last_31_days': {'label': 'Users last 31 days', 'value': 5},
           'users_last_7_days': {'label': 'Users last 7 days', 'value': 5},
           'users_last_hour': {'label': 'Users in last hour', 'value': 2},
           'users_today': {'label': 'Users today', 'value': 2}
        }
    }