.. image:: ../../../../_static/openl2m_logo.png

=============================
MikroTik SNMP Driver Overview
=============================

The MikroTik driver is a very basic driver. Their SNMP implementation is minimal.
We inherit from the standard SnmpConnector() drivber.

The MikroTik driver is implemented in *openl2/switches/connect/snmp/mikrotik/connector.py*

MIB support
-----------

Info about configuring SNMP is at https://help.mikrotik.com/docs/spaces/ROS/pages/8978519/SNMP
The MIB section of that document shows the limit MIB support there is.

MikroTik does NOT support the standard VLAN mibs (Q-Bridge).

Their private MIB can be found at http://www.mikrotik.com/downloads, and extends a few small things.
Primary, we use it to read PoE information. Note their PoE entries are Read-Only!

PoE Data
--------

Since there is no standard PoE support, we override *_get_poeData()* to read the MikroTik data,
and parse it in *_parse_mibs_mikrotik_poe()*

We read the entries under **mtxrPOEEntry** (.1.3.6.1.4.1.14988.1.1.15.1.1)
which is part of the **mtrxPoETable**

**mtxrPOEInterfaceIndex** maps an PoE index to the ifIndex for the interface, so we store that,
and create a *PoePort()* entry for the interface.

Next we read **mtxrPOEStatus** and **mtxrPOEPower** (according to the MIB in Watts),
and store in the interface *PoEPort()* object.

Note that all these entries are Read-Only !
