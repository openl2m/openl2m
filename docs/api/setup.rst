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


Once you have succesfully tested access, you can start accessing :doc:`the various API endpoints available.<endpoints>`

Saving Changes
--------------

If the device requires a command to save the current configuration to the startup config (aka. "write mem"),
your API code is responsible for calling the "save" API !

**Note that devices that require saving have that specific flag set to *True* in their API info.**
