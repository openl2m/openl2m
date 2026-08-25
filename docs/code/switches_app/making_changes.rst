.. image:: ../../_static/openl2m_logo.png

========================
Making Interface Changes
========================

Interface changes are called from the appropriate view.py class handlers.
We implemented classes in order to inherit the default Django "HTTP" handling of unused calls
(ie. default failure on non-implemented GET, POST, etc.)

This is implemented in the *MyView()* class, in *myview.py*. Here we inherited the standard *View()* class,
and implement the unused function handler *http_method_not_allowed()*

Each URL handler class then inherits from MyView() so that all have this functionality!

All URL handler view classes call *self._dispatch_action()*, with the function name.
These are defined in *device_actions.py* and ire "mixed in" through *SwitchActionMixin*,
i.e. used through normal class multiple inheritance.

*_dispatch_action()* does some security checks, gets a *Connector()* object to the device
and then calls the function that performs the action. *In the base Connector(), this only does the book keeping*,
i.e. it sets the data such that the web interfaces shows the appropriate output (interface enabled, vlan changed, etc...)


.. code-block:: bash

    class InterfaceAdminChange()  -->  Connector.set_interface_admin_status()

    class InterfaceDescriptionChange()  -->  Connector.set_interface_description()

    class InterfacePvidChange()  --> Connector.set_interface_untagged_vlan()

    class InterfacePvidAndDescrChange()  -->  combines the above two!

    class InterfacePoeChange()  -->  Connector.set_interface_poe_status

    class InterfacePoeDownUp()  --> call the above function as needed.

    class InterfaceTagsEdit()  -->  Connector.set_interface_vlans()



.. note::

    Device drivers need to override the above functions to implement the actual functionality on their supported devices.
    When that action succeeds, they need to call the base Connector().set_xxx() function for bookkeeping! E.g.

    Super().set_interface_xyx()   or  Connector.set_interface_xyz()