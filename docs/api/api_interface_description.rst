.. image:: ../_static/openl2m_logo.png

=====================
Interface Description
=====================

The "Interface Description" endpoint allows you to change the description of an interface (if your token allows it).
You need to POST the proper *description* parameter.

Here is an example of a call to the "Interface Description" endpoint:

.. code-block:: python

    http --form POST http://localhost:8000/api/switches/35/272/interface/3/description/ 'Authorization: Token ***34b' description="new API description"

It returns an *HTTP 200 OK* with a *result* field, or an *HTTP 4xx* error code with a *reason*.


Example output
--------------

On success:

.. code-block:: python

    HTTP/1.1 200 OK
    ...
    {
        "result": "Interface GigabitEthernet1/0/3 description was changed!"
    }


and on failure:

.. code-block:: python

    HTTP/1.1 403 Forbidden
    ...
    {
        "reason": "You can not manage this interface!"
    }
