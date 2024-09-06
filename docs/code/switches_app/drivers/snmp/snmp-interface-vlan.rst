.. image:: ../../../../_static/openl2m_logo.png

========================
SNMP Discovery Explained
========================

Most of this is 'standard' SNMP. *A full discussion of SNMP Mibs is outside the scope of this document*,
but here is a small amount of details about OpenL2M uses the SNMP capabilities of devices to get
information about interfaces, vlans and the device.

The functions mentioned below are implemented in *switches/connect/snmp/connector.py*,
and most of the MIB entries are defined in *connect/constants.py* or *connect/snmp/constants.py*

All these functions are part of *get_my_basic_info()*.

How we discover Interfaces
--------------------------

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


How we discover VLANs and Interfaces using them
-----------------------------------------------

*This is executed by calling _get_vlan_data()*

Switching capabilities are described by what is called the Q-Bridge MIB. The Q-Bridge defines the ports and vlans
on a device. Note that in this context, a port is NOT the same as an interface as described above. A port is
typically a physical port on the device, and as such has a port-id. Interfaces can be virtual
(eg. "interface Vlan 100"), and have interface-id's.

The often confusing part is that on many (but not all) devices, the interface-id and port-id are be the same number.
However, this is not a given, so we need to discover the mapping of port-id to interface-id,
and then can discover vlan(s) on those ports.

This mapping is done with the "dot1D-Bridge" entry "dot1dBasePortIfIndex",
which maps a physical port-id to an ifIndex.

    self.get_snmp_branch('dot1dBasePortIfIndex')

*Note: if we cannot read this, we cannot continue, and will error out! (These MIB entries are required!)*


Next we read existing vlan id's from "dot1qVlanStaticTable"

    self.get_snmp_branch('dot1qVlanStaticRowStatus')


and if found, we try to get the names and status from  "dot1qVlanStaticName" and "dot1qVlanStatus"

    self.get_snmp_branch('dot1qVlanStaticName')
    self.get_snmp_branch('dot1qVlanStatus')

**Get VLAN Membership**

Once we have the VLAN data, we call _get_port_vlan_membership()

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
