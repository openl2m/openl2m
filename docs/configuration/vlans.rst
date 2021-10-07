.. image:: ../_static/openl2m_logo.png

=====
VLANs
=====

**Create the VLANs that will be manageable**

VLANs represent the vlan ID and name as you are used to on a network.
The combination of ID and name are unique, so you can overload names for a
single ID. VLANs can be grouped in VLAN Groups, or individually selected
in a Switch Group.

**VLAN Groups**

These are groupings of vlans that you can give a name. This allows for a simple
adding of a number of vlans to a Switch Group. E.g. create a VLAN Group named
"Wifi VLANs" that has as members all the wireless client vlans in your
organization. This can then be applied in one or more Switch Groups.

**Using VLANs and VLAN Groups**

VLANs and Vlan Groups can be assigned to Switch Groups.  Any switch group member user
can then manage the ports on the devices that are on the vlans assigned.

Note that a device or switch can be in more then one Switch Group. So you can assign some vlans to one group,
and other vlans (or vlan group) to another Switch Group. Then assign users the appropriate Switch Group.
