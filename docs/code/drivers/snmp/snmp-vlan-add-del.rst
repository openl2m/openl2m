.. image:: ../../../_static/openl2m_logo.png

========================
Managing VLANs with SNMP
========================

This section describes how we attempt to rename, add or delete vlans on devices using SNMP.

"Generic" SNMP
--------------

In the *SnmpConnector()* object, defined in *switches/connect/snmp/connector.py*,
we implement Vlan Adding and Editing for SNMP-managed devices.
See *def vlan_create(), vlan_edit() and vlan_delete()*

This functionality implements the most common way of doing this on SNMP devices, using atomic (set-multiple) writes to two OIDs.

In *def vlan_create(self, vlan_id, vlan_name)* , we write to *dot1qVlanStaticRowStatus.<vlan id>* and set it to *createAndGo(4)*.
This should work on most devices that implement the Q-Bridge MIB. However, some devices may need to set *createAndWait(5)*.
If your device needs a different sequency, please override this function in your device driver!

*def vlan_delete()* calls on *dot1qVlanStaticRowStatus.<vlan id>* and sets it to *destroy(6)*, to remove a vlan.


Cisco Specific
--------------

For Cisco Catalyst devices, we follow the steps outlined here:

https://www.cisco.com/c/en/us/support/docs/ip/simple-network-management-protocol-snmp/45080-vlans.html#topic1

