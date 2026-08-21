.. image:: ../../_static/openl2m_logo.png

==============================
Interface VLAN and Description
==============================

This is called when both the interface untagged vlan and description are changed with a single click (submit).

View
----

In views.py, (see also urls.py) this is handled in the class *class InterfacePvidAndDescrChange()*.

This class calls two separate device actions from the *DeviceActions()* object to implement the untagged vlan,
and description changes.

Connector
---------

In the *Connector()* object, we implement the placeholder bookkeeping functions
*Connector().set_interface_description()* and *Connector().set_interface_untagged_vlan()*

Calls to *actions.interface_description_change()* and *actions.interface_pvid_change()* will automatically call
the bookkeeping functions in Connector() class to updating what is rendered in the view.
