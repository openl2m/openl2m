.. image:: ../_static/openl2m_logo.png

=============
Interface PoE
=============

The "Interface PoE" endpoint allows you to enable or disable the PoE setting on an interface (if your token allows it).
You need to POST the proper *poe_state* parameter.

Here is an example of a call to the "Interface PoE" endpoint:

.. code-block:: python

    http --form POST http://localhost:8000/api/switches/interface/poe_state/35/272/3/ 'Authorization: Token ***34b' poe_state=On

Valid values for "on" are: on, enable, enabled, 1, y, yes  (case insensitive!) *Any other value is considered Off!*

It returns an *HTTP 200 OK* with a *result* field, or an *HTTP 4xx* error code with a *reason*.


Example output
--------------

On success:

.. code-block:: python

    HTTP/1.1 200 OK
    ...
    {
        "result": "Interface GigabitEthernet1/0/3 PoE is now Enabled"
    }


and on failure:

.. code-block:: python

    HTTP/1.1 403 Forbidden
    ...
    {
        "reason": "You can not manage this interface!"
    }
