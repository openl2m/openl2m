.. image:: ../_static/openl2m_logo.png

=========================
API Interface (Vlan) Tags
=========================

The "Interface Tags" endpoint allows you change the untagged (ie. access) vlan, and 802.1q tagged vlans of an interface
(if your token allows it). You need to POST the proper parameter: untagged_vlan (integer), tagged_vlans (list of 0 or more integers), allow_all (bool)

Note: *you token needs to allow access to the interface and to the new vlans!*

Here is an example of a call to the "Interface Tags" endpoint, disabling the interface:

.. code-block:: python

    http --form POST http://localhost:8000/api/switches/35/272/interface/3/tags/ 'Authorization: Token ***34b' untagged_vlan:=500 tagged_vlans=1,2,3,4,5 allow_all=no


It returns an *HTTP 200 OK* with a *result* field, or an *HTTP 4xx* error code with a *reason*.


Example output
--------------

On success:

.. code-block:: python

    HTTP/1.1 200 OK
    ...
    {
        "result": "Interface GigabitEthernet1/0/3 vlans changed"
    }


and on failure:

.. code-block:: python

    HTTP/1.1 403 Forbidden
    ...
    {
        "reason": "You can not manage this interface!"
    }
