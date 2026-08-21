.. image:: ../../_static/openl2m_logo.png

=======================
Transceiver information
=======================

Interface() objects can show information about the transceivers attached.
We mainly intend this to show optical transceiver information.

We define a *Transceiver()* object in *switches/connect/classes.py*. Drivers can create an object,
set the appropriate attributes, and then attach this to the *Interface().transceiver* field.

Where It Shows
--------------

The transceiver data is shown as an icon in the template at *templates/_tpl_if_type_icons.html*
The templates shows the interface transceiver icon on the main Interfaces tab, and the Bulk Edit tab.
The icon will have a hover-info about the transceiver.