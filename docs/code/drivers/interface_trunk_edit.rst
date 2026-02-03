.. image:: ../../_static/openl2m_logo.png

====================
Interface Trunk Edit
====================

802.1Q Tagged Vlan Editing
--------------------------

If the driver has **self.can_edit_tags = True**, this indicates the driver can edit 802.1q tagged vlans on interfaces.
(Note that the base Connector() is set to False!)

At the time of writing Admin users are the only users with automatic access to this feature, if supported.

Staff users can get access if the configuration setting **STAFF_ALLOW_TAGS_EDIT = True** is set.

It enabled and access granted, this will add a clickable + icon available for untagged interfaces,
and make the 'trunk' icon (stacked dots) clickable.

This will render the 'Tags edit form' from *templates/_tpl_if_trunk_edit_form.html*

Submitting this will call *switches.views.InterfaceTagsEdit()*, which (eventually)
then call *switches.actions.perform_interface_tags_edit()*

*perform_interface_tags_edit()* gets three parameters that indicate what is requested:
interface - the Interface() object.
pvid - the (integer) requested untagged vlan (as integer).
tagged_vlans - a List() of tagged vlans requested (as integers).
allow_all - a boolean indicating of 'trunk allow all' should be set (if driver supports it)

Hence, if the *tagged_vlans* list is empty, the request is for 'Access' mode.
Otherwize, we are handling a trunked, ie 802.1Q tagged, request.

*perform_interface_tags_edit()* is also the entry point for API calls.
This in turn calls *Connector.set_interface_vlans()* to perform the work.

The base class *Connector.set_interface_vlans()* performs the book-keeping for the web gui. Drivers need to override this function,
and implement their vendor-specific functionality. Finally, that override function needs to call the base class for bookkeeping.

What to implement
-----------------

Drivers need to implement *self.set_interface_vlans()* to override the base class.
Logic would figure out how to set access mode or trunk mode configurations for this particular vendor driver.

Once completed, the driver needs to call the base class for book-keeping. Here is some skeleton code.

.. code:: python

        def set_interface_vlans(self, interface: Interface, untagged_vlan: int, tagged_vlans: List[int], , tagged_all: bool = False) -> bool:
        ...
        if not len(tagged_vlans):
            # no tagged vlan, ie "access mode", set pvid or untagged vlan.
            ... vendor code here ...

        else:
            # trunk mode, set mode and native vlan:
            ... vendor code here ...

        # if all is well, call the base Connector() for bookkeeping:
        if OK:
            super().set_interface_vlans(interface=interface, untagged_vlan=untagged_vlan, tagged_vlans=tagged_vlans, tagged_all=tagged_all)
            return True

        return False
