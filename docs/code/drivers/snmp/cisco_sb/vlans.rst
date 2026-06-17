
.. image:: ../../../../_static/openl2m_logo.png

===========================
Cisco-SB SNMP VLAN Overview
===========================

CBS switches use primarily the *CISCOSB-vlan-MIB* for VLAN definition and interface vlan management.

There are some things to note:

Switch ports have several modes:

    * **Access** - ie single untagged frames
    * **Trunk** - dot1q encapsulated
    * **General** - access both untagged and tagged frames.
      We are not sure what the difference is with Trunk, which also allows both untagged and tagged frames.


The **port mode** is read from and written to the **vlanPortModeState** mib (.1.3.6.1.4.1.9.6.1.101.48.22.1.1.<ifindex>),
where:

    * 10 = General
    * 11 = Access
    * 12 = Trunk


**General mode**

The untagged vlan is read from and written to the Q-Bridge standard
"dot1qVlan" MIB id (dot1qVlan.<ifIndex> = <vlan-id>)

It appears that the general mode allowed tagged vlans are represented by the standard Q-Bridge "egress port" vlan fields.
As we don't support this mode at time of writing, this data is ignored.


**Access mode**

The untagged vlan is read from and written to
"vlanAccessPortModeVlanId" MIB id (vlanAccessPortModeVlanId.<ifIndex> = <vlan-id>)


**Trunk mode**

The untagged vlan on a trunk port is read from and written to vlanTrunkPortModeNativeVlanId.<ifIndex> = <vlan-id>

The vlanTrunkPortModeEntry branch has all vlan memberships. This is a bitmap that is indexed by interface,
and grouped by 1024 vlan numbers.

E.g.

    *vlanTrunkModeList1025to2048.14 = <bitmap>*

For the interface with ifIndex 14 (likely "GigabitEthernet14"), the bitmap has a 1 for every vlan from
1025 -> 2048 that is enabled on the trunk configuration.

Likewise for *vlanTrunkModeList1to1024.<ifIndex>*, *vlanTrunkModeList2049to3072.<ifIndex>*
and *vlanTrunkModeList3073to4094.<ifIndex>*


.. note::

    This is the opposite of the Q-Bridge VLAN bitmaps, where the index is the Vlan ID,
    and bitmap represents the switch ports that are active on that vlan!
