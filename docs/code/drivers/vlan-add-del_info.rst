.. image:: ../../_static/openl2m_logo.png

==============
Managing VLANs
==============

This section describes how drivers should implement adding, editing or deleting VLANs.

View
----

In views.py, (see also urls.py) these are handled in the classes *SwitchVlanCreate()*, *SwitchVlanUpdate()* and *SwitchVlanDelete*

These classes call the *self._dispatch_action()* with the appropriate action function name.

Connector
---------

In the *Connector()* object, defined in *switches/connect/connector.py*,
we implement the placeholder bookkeeping functions for Vlan Adding and Editing.

See *def vlan_create(), vlan_edit() and vlan_delete()*

Drivers need to set the appropriate *can_xxxx* flags in **__init__()**.
Next, they need to implement these functions to provide these features.

Upon successfull completion of the
action (implementation), drivers should call the equivalent functions in the base Connector() class for
bookkeeping and updating what is rendered in the view.

