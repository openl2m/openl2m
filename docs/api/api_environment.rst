.. image:: ../_static/openl2m_logo.png

===============
API Environment
===============

The "Environment" endpoint returns some information about the OpenL2M application runtime environment.

.. code-block:: bash

     http --form POST https://<your-domain>/api/environment/ 'Authorization: Token <your-token-string-here>'

The equivalent *curl* example would be:

.. code-block:: bash

    curl https://<your-doimain>/api/environment/ -H 'Authorization: Token <your-token-string-here>'

Output
------

At the time of this writing, the output will look something like this. In the future, additional information may be added.

.. code-block:: bash

    HTTP/1.1 200 OK
    Allow: GET, HEAD, OPTIONS
    ...
    {
        'database': {'label': 'Database', 'value': 'PostgreSQL 16.10'},
        'database_name': {'label': 'Database Name', 'value': 'openl2m'},
        'database_size': {'label': 'Database Size', 'value': '14 MB'},
        'debug': {'label': 'Debug', 'value': 'Enabled'},
        'distro': {'label': 'Distro', 'value': 'Ubuntu 24.04.3'},
        'django': {'label': 'Django', 'value': '5.2.5'},
        'ezsnmp': {'label': 'EzSnmp', 'value': '1.1.0'},
        'git_commit': {'label': 'Git Commit', 'value': 'Fri, 29 Aug 2025 20:20 UTC'},
        'git_version': {'label': 'Git version', 'value': 'api_attributes (992d4b21)'},
        'hostname': {'label': 'Hostname', 'value': 'noc-dev'},
        'openl2m': {'label': 'OpenL2M', 'value': '3.4.7 (2025-08-21)'},
        'os': {'label': 'OS', 'value': 'Linux (6.8.0-79-generic)'},
        'python': {'label': 'Python', 'value': '3.12.3'}
    }
