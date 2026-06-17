
.. image:: ../../../../_static/openl2m_logo.png

==========================
Cisco SNMP Driver Overview
==========================

The driver is implemented in *openl2/switches/connect/snmp/cisco/connector.py*

This Cisco driver inherits the standard MIB methods from SnmpConnector() for interface up/down and description.

For VLAN management, the Cisco driver implements **the Old-Style Catalyst Way**

Older Catalyst switches use the Cisco proprietary VTP MIB for vlan management.
If VLANs are found in this MIB, the devices is assumed to use it, and *self.use_vt_mib = True* is set.

More to be written...