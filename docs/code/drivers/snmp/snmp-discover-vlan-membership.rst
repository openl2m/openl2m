.. image:: ../../../_static/openl2m_logo.png

============================
How we discover Vlan Memship
============================

**We already should have existing vlan information at this time.**

We call *SnmpConnector()._get_port_vlan_membership()*


We use the **Q-Bridge MIB** for port vlan information. See https://mibs.observium.org/mib/Q-BRIDGE-MIB/


Untagged vlan
-------------

The Q-Bridge "dot1qPvid" entry maps every switch port (i.e. port-id) to the untagged vlan on that port.

.. code-block:: python

    self.get_snmp_branch('dot1qPvid')

So here is the first time we need the mapping from port-id to interface-id (see Vlan discovery) to read or set
the untagged vlan on an interface.

Some devices may not implement the above *dot1qPvid* mib,

Tagged Vlans
------------

We look at the "Current" and "Static" vlan branch of the Q-Bridge MIB.

.. code-block:: python

    # THIS IS LIKELY NOT PROPERLY HANDLED !!!
    # read the current vlan untagged port mappings
    # retval = self.get_snmp_branch(dot1qVlanCurrentUntaggedPorts)
    # if retval < 0:
    #    self.add_warning(f"Error getting 'Q-Bridge-Vlan-Untagged-Interfaces' ({dot1qVlanCurrentUntaggedPorts})")
    #    return retval

    # read the current vlan egress port mappings, tagged and untagged
    retval = self.get_snmp_branch('dot1qVlanCurrentEgressPorts')

    # read the 'static' vlan egress port mappings, tagged and untagged
    # some devices do not add ports to "dot1qVlanCurrentEgressPorts" until the interface is in the "up" state
    # reading this will show the static vlan configs for these ports...
    retval = self.get_snmp_branch('dot1qVlanStaticEgressPorts')


**dot1qVlanCurrentEgressPorts.<vlan-id>** has a sub-oid for each vlan, where the returned value is a bitmap of all ports active
on this vlan, in either tagged on untagged mode. The port-id is the offset of the bit in the bitmap.

E.g. bit 1 in byte 1 is port-id 1. Bit 3 in byte 2 is port-id 11. Etc.

We also read **dot1qVlanStaticEgressPorts**, similarly a bitmap, but for ports that are 'statically defined'.
As the comments show, some devices do not add ports to "Current" bitmap until the interface is in the "up" state.
Reading this will show the static vlan configs for these ports...

Thus the key difference between **dot1qVlanStaticEgressPorts** and dot1qVlanCurrentEgressPorts in the Q-BRIDGE-MIB lies
in whether they represent the administratively configured VLAN membership or the actively operational VLAN membership.

In summary:

**dot1qVlanStaticEgressPorts** - This shows which ports are assigned to a VLAN by the device configuration and survives a reboot.

**dot1qVlanCurrentEgressPorts** - This shows which ports are currently, when read, transmitting traffic for the VLAN,
either tagged or untagged. This includes ports dynamically learned (e.g., via GVRP), even if not explicitly configured.

Ie. If there is NO dynamic learning and all ports are "up", the two entries should be the same!



Note: at present, we don't read **dot1qVlanCurrentUntaggedPorts.<vlan-id>**. This only returns the untagged ports,
again indexed by vlan id, and the return value is the bitmap of ports active. We should have already gotten this data from **dot1qPvid**


IEEE Q-Bridge MIB
-----------------

This MIB defines a similar structure to the Q-Bridge MIB. Some devices implement this MIB (or both). See https://mibs.observium.org/mib/IEEE8021-Q-BRIDGE-MIB/

As mentioned in the vlan discovery section, you can learn Vlans, static or dynamic, from **ieee8021QBridgeVlanStatus.<vlan-id>**

Then you can get names from **ieee8021QBridgeVlanStaticName.<vlan-id>**

Like Q-Bridge, you can read tagged and untaggeded ports in vlan from **ieee8021QBridgeVlanCurrentEgressPorts.<vlan-id>**
and **ieee8021QBridgeVlanStaticEgressPorts**

And get the list of untagged ports from **ieee8021QBridgeVlanCurrentUntaggedPorts.<vlan-id>** and **ieee8021QBridgeVlanStaticUntaggedPorts**


Note that all these entries also return bitmap values that have the bit set for the corresponding Port-ID,
i.e. not the ifIndex! You have map the port-id back to the proper interface ifIndex!