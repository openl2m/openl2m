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
       TBD...
    }
