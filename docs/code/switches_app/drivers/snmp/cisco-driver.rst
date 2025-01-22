
.. image:: ../../../../_static/openl2m_logo.png

==========================
Cisco SNMP Driver Overview
==========================

The driver is implemented in *openl2/switches/connect/snmp/cisco/connector.py*

This Cisco driver inherits the standard MIB methods from SnmpConnector() for interface up/down and description.

For VLAN management, the Cisco driver implements two access methods.

**The Old-Style Catalyst Way**

Older Catalyst switches use the Cisco proprietary VTP MIB for vlan management.
If VLANs are found in this MIB, the devices is assumed to use it, and *self.use_vt_mib = True* is set.

**Newer CBS switches**

Newer CBS switches use for of the standard MIB, e.g. Q-Bridge MIB for VLAN management.
    **This has only be been tested a CBS-350 switches !**

There are some things to note:

Switch ports have several mode:
    access - ie single untagged frames
    trunk - dot1q encapsulated
    general - access both untagged and tagged frames

In general mode, the untagged vlan is read from and written to the
"dot1qVlan" MIB ID (.1.3.6.1.2.1.17.7.1.4.5.1.1.<ifIndex>)

In access mode, untagged vlan is read from and written to
"dot1qVlanCurrentUntaggedPorts" MIB id (.1.3.6.1.2.1.17.7.1.4.2.1.5.<counter>.<vlan-id>)

interface GigabitEthernet1
 switchport mode general
 switchport access vlan 1150
 switchport general pvid 500

The port mode is read from the vlanPortModeState mib (.1.3.6.1.4.1.9.6.1.101.48.22.1.1.<ifindex>),
where:

    * 10 = General
    * 11 = Access
    * 12 = Trunk

