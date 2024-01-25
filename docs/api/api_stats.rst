.. image:: ../_static/openl2m_logo.png

==============
API Statistics
==============

The "Stats" endpoint returns some information about the OpenL2M application.

.. code-block:: bash

     http --form POST https://<your-domain>/api/stats/ 'Authorization: Token <your-token-string-here>'

The equivalent *curl* example would be:

.. code-block:: bash

    curl https://<your-doimain>/api/stats/ -H 'Authorization: Token <your-token-string-here>'

Output
------

At the time of this writing, the output will look something like this. In the future, additional information may be added.

.. code-block:: bash

    HTTP/1.1 200 OK
    Allow: GET, HEAD, OPTIONS
    ...
    {
        "api-version": 1,
        "distro": "Ubuntu 22.04.3",
        "django-version": "4.2.9",
        "hostname": "dev-server",
        "openl2m-version": "3.0.1",
        "os": "Linux (5.15.0-91-generic)",
        "python-version": "3.11.7"
    }
