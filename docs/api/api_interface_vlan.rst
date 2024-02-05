.. image:: ../_static/openl2m_logo.png

==================
API Interface Vlan
==================

The "Interface Vlan" endpoint allows you change the untagged (ie. access) vlan of an interface (if your token allows it).
You need to POST the proper *vlan* parameter.

Note: *you token needs to allow access to the interface and to the new vlan!*

Here is an example of a call to the "Interface Vlan" endpoint, disabling the interface:

.. code-block:: python

    http --form POST http://localhost:8000/api/switches/35/272/interface/3/vlan/ 'Authorization: Token ***34b' vlan=500


It returns an *HTTP 200 OK* with a *result* field, or an *HTTP 4xx* error code with a *reason*.


Example output
--------------

On success:

.. code-block:: python

    HTTP/1.1 200 OK
    ...
    {
        "result": "Interface GigabitEthernet1/0/3 changed to vlan 500"
    }


and on failure:

.. code-block:: python

    HTTP/1.1 403 Forbidden
    ...
    {
        "reason": "You can not manage this interface!"
    }
