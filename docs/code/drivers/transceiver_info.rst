.. image:: ../../_static/openl2m_logo.png

=======================
Transceiver information
=======================

Interface() objects can show information about the transceivers attached. We mainly intend this to show optical transceiver information.

We define a *Transceiver()* object in *switches/connect/classes.py*. Drivers can create an object,
set the appropriate attributes, and then attach this to the *Interface().transceiver* field.

Where it shows
--------------

The templates will then show the interface transceiver icon on the main Interfaces tab, and the Bulk Edit tab.
The icon will have a hover-info about the transceiver. This template is in *templates/_tpl_if_type_icons.html*