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
            "Command Lists": 6,
            "Commands": 27,
            "Log Entries": 616,
            "Credentials Profiles": 9,
            "SNMP Profiles": 10,
            "Switch Groups": 33,
            "Switches": 740,
            "Vlan Groups": 18,
            "Vlans": 292
        },
        "usage": {
            "API calls last 31 days": 43,
            "API calls last 7 days": 41,
            "API calls today": 19,
            "Changes last 31 days": 543,
            "Changes last 7 days": 141,
            "Changes today": 12,
            "Commands last 31 days": 18,
            "Commands last 7 days": 6,
            "Commands today": 1,
            "Devices last 31 days": 75,
            "Devices last 7 days": 34,
            "Devices today": 13,
            "Total Changes": 29784,
            "Total Commands": 1684
        }
    }
