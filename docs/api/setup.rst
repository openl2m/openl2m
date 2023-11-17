.. image:: ../_static/openl2m_logo.png

=========
API Setup
=========

In order to use the REST API, your user account will need to have at least one token assigned to it.

At the time of this writing, this has to be done by an admin,
either from the Web GUI administrative interface, or the OpenL2M command line interface, as such:

.. code-block:: bash

    python3 manage.py user_create_token <username>

Please contact you administrator for additional help.

API Testing
-----------

You can test the API from the command line on most systems, by making HTTP "GET" calls. Once you have your token,
you can do something like the example below to get the list of devices you can access:

.. code-block: bash

    http https://<your-domain>/api/switches/ 'Authorization: Token your-token-string-here'

Note: the above uses the Python HTTPIE package.


Once you have successfully tested access, you can start accessing :doc:`the various API endpoints available.<endpoints>`
