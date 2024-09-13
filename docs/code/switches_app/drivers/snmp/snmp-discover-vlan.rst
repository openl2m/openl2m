.. image:: ../../../../_static/openl2m_logo.png

==============
VLAN Discovery
==============

*This is executed by calling _get_vlan_data()*

Switching capabilities are described by what is called the **Q-Bridge MIB**. The Q-Bridge defines the switch ports
and vlans on a device. Note that in this context, a port is NOT the same as an interface as described above.
A (switch) port is typically a physical port on the device, and as such has a port-id. Interfaces can be virtual
(eg. "interface Vlan 100"), and have interface-id's but *not port-id's.*

The often confusing part is that on many (but not all) devices, the interface-id and port-id are the same number.
However, this is not a given, so we need to discover the mapping of (switch) port-id to interface-id,
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
