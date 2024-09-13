.. image:: ../../../../_static/openl2m_logo.png

==========================
How we discover Interfaces
==========================

*This is implemented in _get_interface-data()*

We read the "Interface MIBs" data from the device. This is really stored in two location,
the original MIB-II "ifTable" branch, and the more modern IF-MIB branch.

For performance reasons, we are reading only specific entries from these MIBs:

**'ifIndex'** gets us the ID of an interface. We start with this,
and then fill in the rest of the interface data from the others.

**'ifType'** tells us what kind of interface this is, e.g Ethernet, virtual, serial, etc.

**'ifAdminStatus'** gets the status of the interface, admin up/down

**'ifOperStatus'** tells us the link status of an interface that is Admin-UP.

**'ifName'** is what is says :-) This value comes from the newer IF-MIB. If this is *not* found,
we then look to get the name from the older MIB-II **'ifDescr'** entry, which is actually *not* what is says!

**'ifAlias'** is actually the the interface description!

The new IF-MIB has interface speed in **'ifHighSpeed'**, in Mbps, to handle higher speed interface 10g, 100g, 400g, etc.

If that does not exist, we read the older MIB-II **'ifSpeed'**, which reports as is (eg. 1000 is 1kbps)

Finally, **'dot3StatsDuplexStatus'** from the ETHERLIKE-MIB gives us information
about half- or full-duplex status of an interface.

We now have the interface-id, aka ifIndex, and most information about the interfaces.


Get VLAN Membership
-------------------

We already should have vlan information at this time. We now call *SNmpConnector()._get_port_vlan_membership()*

The Q-Bridge "dot1qPvid" entry maps every switch port (ie port-id) to the untagged vlan on that port.

    self.get_snmp_branch('dot1qPvid')

So here is the first time we need the mapping from port-id to interface-id (see above) to set the untagged vlan
on an interface.

Some devices may not implement the above dot1qPvid" mib, so we can also look at the "CurrentVlan"
branch of the Q-Bridge MIB.

        # THIS IS LIKELY NOT PROPERLY HANDLED !!!
        # read the current vlan untagged port mappings
        # retval = self.get_snmp_branch(dot1qVlanCurrentUntaggedPorts)
        # if retval < 0:
        #    self.add_warning(f"Error getting 'Q-Bridge-Vlan-Untagged-Interfaces' ({dot1qVlanCurrentUntaggedPorts})")
        #    return retval

        # read the current vlan egress port mappings, tagged and untagged
        retval = self.get_snmp_branch('dot1qVlanCurrentEgressPorts')
