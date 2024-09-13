.. image:: ../../../_static/openl2m_logo.png

===============
VRF information
===============

We can show MPLS L3VPN information for devices and interface membership. 
Below is documented how a driver should set this information, and where it shows.

VRF info
--------

We define a *Vrf()* object in *switches/connect/classes.py*.

VRF information on a device is added to the *Connector().vrfs{}* dictionary,
indexed by VRF name. Each entry stores a Vrf() object.

If found, this data is shown on the Device Information tab.


Interface VRF membership
------------------------

On layer 3 devices, we may be able to find what VRF a specific interface is a member of.
This is stored in the *Interface().vrf* attribute, as a string with the name of the VRF.

Note this can be used as an index into the *Connector().vrfs{}* dictionary for more information.


Where it shows
--------------

The list of Vrf() objects is shown on the *Device Info* tab, from the file *templates/tab_info_vrfs.html*

For interfaces with a VRF memmber (Interface.vrf is set), this is shown as an icon behind the interface name 
on the Interfaces and Bulk-Edit tabs. This comes from the file *templates/_tpl_if_type_icons.html*