.. image:: ../../../_static/openl2m_logo.png

==============
Managing VLANs
==============

This section describes how drivers should implement adding, editing or deleting VLANs.

In the *Connector()* object, defined in *switches/connect/connector.py*,
we implement the placeholder bookkeeping functions for Vlan Adding and Editing. 

See *def vlan_create(), vlan_edit() and vlan_delete()*

Drivers need to implement these functions to provide these features.

