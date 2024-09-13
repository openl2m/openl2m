.. image:: ../../../_static/openl2m_logo.png

================
Vlan Information
================

Below is documented how a driver should set information about device vlans, and where it shows.

This typically is loaded when the driver's *get_my_basic_info()* function is called. 
I.e. This is when a driver is called from the *view.py* URL handling functions.

The *Vlan()* class is used to store interface information.
See the definition in openl2m/switches/connect/classes.py


Storing Vlan Objects
--------------------

*Connector().vlans* is a dictionary that stores the Vlans on a device. The key (index) is an *integer (int)*
representing the numeric vlan ID. Items are Vlan() class instances.

The most important attributes of a Vlan() are the vlan.id, and vlan.name 


Where It Shows
--------------

Vlans are used in a number of places:

This shows under the 'Interfaces', 'Bulk Edit' and 'Arp/LLDP' tabs, and are rendered in the file 
*templates/_tab_if_basics.html*, *templates/_tab_if_bulkedit.html* and *templates/_tab_if_arp_lldp.html*

Those 3 pages each have loops for the interfaces, and for each interface the vlan ID is used to get the "vlan.name" entry.


And on the *Device Info* tab, in the Vlan card. This is rendered in *templates/_tab_info_vlans.html*

