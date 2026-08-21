.. image:: ../../_static/openl2m_logo.png

====================
Interface PoE Change
====================

View
----

In views.py, (see also urls.py) this is handled in the class *class InterfacePoeChange()*.

This class calls the *self._dispatch_action()* with the appropriate action function name.

Connector
---------

In the *Connector()* object, we implement the placeholder bookkeeping function *Connector().set_interface_poe_status()*

Drivers need to set the appropriate *can_xxxx* flags in **__init__()**.
Next, they need to implement this function to provide these features.

Upon successfull completion of the action (implementation), drivers should call the equivalent
function in the base Connector() class for bookkeeping and updating what is rendered in the view.