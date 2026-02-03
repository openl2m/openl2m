.. image:: ../../_static/openl2m_logo.png

===========
Permissions
===========

Permissions are handled in the base **Connector()._set_interfaces_permissions()** in *switches/connect/connector.py* around line 1758

*_set_interfaces_permissions()* is called from *Connector.get_basic_info()* after interfaces have been loaded (around line 358)

This function loops through all the interfaces found above. It sets permissions as needed.
And, it calls **self._can_manage_interface()** which by default returns False.

Drivers can overload **_can_manage_interface()** to implement specific use-cases to disable management on stacking interfaces, etc.
See *switches/connect/snmp/comware/connector.py* around line 387 for an example.

.. note::

    A driver should NOT override the base _set_interfaces_permissions(),
    rather it should implement *_can_manage_interface()* as needed!