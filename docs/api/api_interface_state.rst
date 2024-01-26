.. image:: ../_static/openl2m_logo.png

===============
Interface State
===============

The "Interface State" endpoint allows you to enable(up) or disable(down) an interface (if your token allows it).
You need to POST the proper *state* parameter.

Here is an example of a call to the "Interface State" endpoint, disabling the interface:

.. code-block:: python

    http --form POST http://localhost:8000/api/switches/35/272/interface/3/state/ 'Authorization: Token ***34b' state=0

Valid values for "on" are: on, enable, enabled, 1, y, yes  (case insensitive!) *Any other value is considered Off!*

It returns an *HTTP 200 OK* with a *result* field, or an *HTTP 4xx* error code with a *reason*.


Example output
--------------

On success:

.. code-block:: python

    HTTP/1.1 200 OK
    ...
    {
        "result": "Interface GigabitEthernet1/0/3 is now Disabled"
    }


and on failure:

.. code-block:: python

    HTTP/1.1 403 Forbidden
    ...
    {
        "reason": "You can not manage this interface!"
    }
