.. image:: ../_static/openl2m_logo.png

===================
API Vlan Management
===================

The "Vlan Management" endpoints allow you to create, delete or rename vlans on the device (if permitted).

.. note::

    Not all devices can manage vlans, or if they can, can set names on vlans.
    Please look at the appropriate fields returned by the device info (*change_vlan* and *change_vlan_name*)


Create or Add
-------------

.. code-block:: bash
    
    http --form POST https://<your-domain>/api/switches/vlan_add/35/272/ 'Authorization: Token <your-token-string-here>' vlan_id=777 vlan_name="seven-times-3"

Rename
------

With this API call, we can change the name of an already existing vlan.

.. code-block:: bash
    
    http --form POST https://<your-domain>/api/switches/vlan_edit/35/272/ 'Authorization: Toke <your-token-string-here>' vlan_id=777 vlan_name="seven-seven-seven"
 
Delete
------

And finally, this allows us to delete an existing vlan.

.. code-block:: bash

    http --form POST https://<your-domain>/api/switches/vlan_delete/35/272/ 'Authorization: Token <your-token-string-here>' vlan_id=777
