.. image:: ../../../_static/openl2m_logo.png

==========================
How we discover Interfaces
==========================

*This is implemented in _get_interface-data()*

We read the "Interface MIBs" data from the device. This is really stored in two locations,
the original MIB-II "ifTable" branch, and the more modern IF-MIB branch.

For performance reasons, we are reading only specific entries from these MIBs:

**ifIndex** (.1.3.6.1.2.1.2.2.1.1) gets us the ID of an interface. We start with this,
and then fill in the rest of the interface data from the others.

**ifType** (.1.3.6.1.2.1.2.2.1.3) tells us what kind of interface this is, e.g Ethernet, virtual, serial, etc.

**ifAdminStatus** (.1.3.6.1.2.1.2.2.1.7) gets the status of the interface, admin up/down

**ifOperStatus** (.1.3.6.1.2.1.2.2.1.8) tells us the link status of an interface that is Admin-UP.

**ifName** (.1.3.6.1.2.1.31.1.1.1.1) is what is says :-) This value comes from the newer IF-MIB. If this is *not* found,
we then look to get the name from the older MIB-II **ifDescr** entry (.1.3.6.1.2.1.2.2.1.2), which is actually *not* what is says!

**ifAlias** in IF-MIB (.1.3.6.1.2.1.31.1.1.1.18) is actually the interface description!

The new IF-MIB has interface speed in **ifHighSpeed** (.1.3.6.1.2.1.31.1.1.1.15), in Mbps,
to handle higher speed interface 10g, 100g, 400g, etc.

If that does not exist, we read the older MIB-II **ifSpeed** (.1.3.6.1.2.1.2.2.1.5), which reports as is (eg. 1000 is 1kbps)

Finally, **dot3StatsDuplexStatus** (.1.3.6.1.2.1.10.7.2.1.19) from the ETHERLIKE-MIB gives us information
about half- or full-duplex status of an interface.

We now have the interface-id, aka ifIndex, and most information about the interfaces.


