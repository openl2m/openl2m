.. image:: ../../../_static/openl2m_logo.png

============================
How we discover Vlan Memship
============================

**We already should have vlan information at this time.**

We call *SnmpConnector()._get_port_vlan_membership()*

Q-Bridge MIB
------------

The Q-Bridge "dot1qPvid" entry maps every switch port (i.e. port-id) to the untagged vlan on that port.

.. code-block:: python

    self.get_snmp_branch('dot1qPvid')

So here is the first time we need the mapping from port-id to interface-id (see Vlan discovery) to read or set
the untagged vlan on an interface.

Some devices may not implement the above *dot1qPvid* mib, so we can also look at the "CurrentVlan"
branch of the Q-Bridge MIB.

.. code-block:: python

    # THIS IS LIKELY NOT PROPERLY HANDLED !!!
    # read the current vlan untagged port mappings
    # retval = self.get_snmp_branch(dot1qVlanCurrentUntaggedPorts)
    # if retval < 0:
    #    self.add_warning(f"Error getting 'Q-Bridge-Vlan-Untagged-Interfaces' ({dot1qVlanCurrentUntaggedPorts})")
    #    return retval

    # read the current vlan egress port mappings, tagged and untagged
    retval = self.get_snmp_branch('dot1qVlanCurrentEgressPorts')


**dot1qVlanCurrentEgressPorts.<vlan-id>** has a sub-oid for each vlan, where the value is a bitmap of all ports active on this vlan,
in either tagged on untagged mode.

**dot1qVlanCurrentUntaggedPorts.<vlan-id>** then only returns the untagged ports, again indexed by vlan id,
and the return value is the bitmap of ports active.


IEEE Q-Bridge MIB
-----------------

This MIB defines a similar structure to the Q-Bridge MIB. Some devices implement this MIB (or both).

As mentioned in the vlan discovery section, you can learn Vlans, static or dynamic, from **ieee8021QBridgeVlanStatus.<vlan-id>**

Then you can get names from **ieee8021QBridgeVlanStaticName.<vlan-id>**

Like Q-Bridge, you can read tagged and untaggeded ports in vlan from **ieee8021QBridgeVlanCurrentEgressPorts.<vlan-id>**

And get the list of untagged ports from **ieee8021QBridgeVlanCurrentUntaggedPorts.<vlan-id>**

Note that all the 'list' entries return bitmap values that have the bit set for the corresponding Port-ID,
i.e. not the ifIndex! You have map the port-id back to the proper interface ifIndex!