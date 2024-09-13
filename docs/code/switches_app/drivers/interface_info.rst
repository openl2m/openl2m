.. image:: ../../../_static/openl2m_logo.png

=====================
Interface Information
=====================

Below is documented how a driver should set information about device interfaces, and where it shows.

This typically is loaded when the driver's *get_my_basic_info()* function is called. 
I.e. This is when a driver is called from the *view.py* URL handling functions.

The *Interface()* class is used to store interface information.
See the definition in openl2m/switches/connect/classes.py


Storing Interface Objects
-------------------------

To be written


Disable / Enable
----------------

To be written


PoE
---

To be written


Description
-----------

To be written


Vlan
----

To be written


Where It Shows
--------------

This shows under the 'Interfaces', 'Bulk Edit' and 'Arp/LLDP' tabs, and are rendered in the file 
*templates/_tab_if_basics.html*, *templates/_tab_if_bulkedit.html* and *templates/_tab_if_arp_lldp.html*

These templates include a few other templates to standardize the viewing of several attributes of an Interface:

*templates/_tab_if_name* shows the interface name, with color for Up / Down state. This file includes
*templates/_tpl_if_type_icons.html*, which adds several icons indicating Trunked mode, VRF member, and more.

Finally, the link column is displayed using *templates/_tab_if_linkspeed*, 
which defines the HMTL used to show link speed (if up), or maximum interface speed if down.

