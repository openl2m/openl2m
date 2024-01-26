.. image:: ../_static/openl2m_logo.png

===============
API Save Config
===============

The "Save Config" endpoint allows you to save the running configuration of a device to the startup configuration.

If you make changes with an API call, and the device requires a command to save the current configuration
to the startup config (aka. "write mem"), **your API code is responsible for calling the "save" API !**

Devices that require saving have a flag set to *True* in the "switch" section of the "basic" or "details"
info API call. Look for this entry, if present and True, you need to call the "save" api endpoint after changes:

.. code-block:: python

    "switch": {
        ...
        "save_config": true,
        ...
    }


Save example
------------

To save the config, you need to POST to the */api/switches/<group>/<switch>/save/* URL, and include a POST variable "save=on".

Here is an example using Python HTTPIE to save the configuration of switch 272 in group 35:

.. code-block:: bash

     http --form POST https://<your-domain>/api/switches/35/272/save/ 'Authorization: Token <your-token-string-here>' save=1

The equivalent *curl* example would be:

.. code-block:: bash

    curl -X POST https://<your-doimain>/api/switches/35/272/save/ -H 'Authorization: Token <your-token-string-here>' \
         -H "Content-Type: application/json" -d '{"save":"1"}'


Output
------

The output will look something like this:

.. code-block:: bash

    HTTP/1.1 200 OK
    Allow: POST, OPTIONS
    Connection: keep-alive
    Content-Length: 33
    Content-Type: application/json
    Cross-Origin-Opener-Policy: same-origin
    ...
    Set-Cookie: sessionid=kpaakyu1gmeysd8t8jr6749ameb74q78; HttpOnly; Path=/; SameSite=Lax
    Vary: Accept, Cookie
    X-Content-Type-Options: nosniff
    X-Frame-Options: DENY

    {
        "result": "Configuration saved!"
    }


If you happen to call this with save=0, you may get a return like this:


.. code-block:: bash

    http --form POST  https://<your-domain>/api/switches/35/272/save/ 'Authorization: Token xxx' save=0
    HTTP/1.1 400 Bad Request
    ...
    {
        "reason": "No save requested (why did you call us?)."
    }

