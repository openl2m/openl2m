.. image:: ../../../_static/openl2m_logo.png

==============
VLAN Discovery
==============

We start with VLAN discovery. *This is executed by calling _get_vlan_data()*

Switching capabilities are described by what is called the **MIB-2 Q-Bridge MIB**. The Q-Bridge defines the switch ports
and vlans on a device. Note that in this context, a port is NOT the same as an interface as described above.
A (switch) port is typically a physical port on the device, and as such has a port-id. Interfaces can be virtual
(eg. "interface Vlan 100"). Virtual interfaces have interface-id's but *not port-id's.*

The often confusing part is that on many (but not all) devices, the interface-id and port-id are the same number.
However, this is not a given, so we need to discover the mapping of (switch) port-id to interface-id,
and then can discover vlan(s) on those ports.

This mapping is done with the "dot1D-Bridge" entry **dot1dBasePortIfIndex** (.1.3.6.1.2.1.17.1.4.1.2),
which maps a physical port-id to an ifIndex.

    self.get_snmp_branch('dot1dBasePortIfIndex')

*Note: if we cannot read this, we cannot continue, and will error out! (These MIB entries are required!)*


Next we read existing vlan id's from **dot1qVlanStaticTable** (.1.3.6.1.2.1.17.7.1.4.3),

We read **dot1qVlanStaticRowStatus** (.1.3.6.1.2.1.17.7.1.4.3.1.5) to get all vlans:

    self.get_snmp_branch('dot1qVlanStaticRowStatus')


and if any vlans are found, we try to get the names from  **dot1qVlanStaticName** (.1.3.6.1.2.1.17.7.1.4.3.1.1)

    self.get_snmp_branch('dot1qVlanStaticName')


We then read the vlan status (dynamic, static, etc.) from **dot1qVlanStatus** (.1.3.6.1.2.1.17.7.1.4.2.1.6)

    self.get_snmp_branch('dot1qVlanStatus')


.. note::

    The process of discovering vlans, interfaces, (switch) ports, ethernet addresses and IP address is explained well
    in this StackExchange posting:

    https://networkengineering.stackexchange.com/questions/2900/using-snmp-to-retrieve-the-arp-and-mac-address-tables-from-a-switch


Once we know existing vlans, we move on to finding the interfaces via snmp.


.. note::

    Some devices implement the **IEEE 802.1Q Q-Bridge MIB (IEEE8021-Q-BRIDGE-MIB)**, instead of MIB-2 Q-Bridge MIB.
    Drivers for these devices will override the function *_get_vlan_data()* and read the data from that MIB.
    See eg. the Aruba AOS-CX over SNMP driver in *snmp/aruba_cx/connector.py*
