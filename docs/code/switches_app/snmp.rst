.. image:: ../../_static/openl2m_logo.png

================
SNMP Connections
================

**switches/connect/snmp/connector.py**

This file defines the base SnmpConnector() class that implements all generic snmp functions to talk to switches,
according to the Connector() class API.

If device connections are made via SNMP, get_connection_object() in **connect.py** figures out what
specific SnmpConnector() sub-class to get for the device.

Since we mostly want lots of data at once (ie all interfaces, all vlans, etc.) we use the SNMP GetBulk operation
for most data collection. This is implemented in the **SnmpConnector.get_snmp_branch()** function. This needs the mandatory
snmp branch you want to walk (eg. interfaces branch).

Optionally, you can pass in *non_repeaters* and *max_repetitions*. *non_repeaters* is the number of
'single' OIDs you want to 'get'. This is normally a list of single OIDs passed to GetBulk, such as sysUptime,
so you can get time along with interface values. Since we don't use this, we set it to 0.
*max_repetitions* is the number of instances of the branch you expect to get.

E.g. if there are 48 interfaces on switch, you would need at least that much to retrieve them efficiently.
We set this to a default of 25, which can be handled by most devices. This means it will take 3 bulk-reads for most 48 port switches
(with some stacking and loopback interfaces). The underlying library will take care of multiple calls if there are more ports in eg. a stack.


**get_snmp_branch()** calls  easy_snmp.bulkwalk() to get the mib data.

In the parsing loop, the return data is parsed via the default **SnmpConnector._parse_oid()** or a specific parser function requested in the call.


EasySnmp Library use
--------------------

We use the Session() interface from the Python "Easy SNMP" library.
This calls the net-snmp package of the OS.
Use of the native library gives significant performance improvements over the pure Python *pysnmp* library.
The EasySNMP documentation has helpful examples.

Vlan manipulation via snmp requires dealing with bitmap field that are represented in OctetString snmp data types.
EasySNMP has a hard time dealing with this due to how it internally translates everything to/from Unicode strings.
So we use the *pysnmp* library to handle these special cases only.


Vendor-specific SNMP implementations
------------------------------------

Most switches supported use inherit the base SnmpConnector() class and override the vendor-specific functions.
The vendor-specific derived classes are:

* **SnmpConnectorCisco()** - switches/connect/snmp/cisco/connector.py - most Cisco switches
* **SnmpConnectorComware()** - switches/connect/snmp/comware/connector.py - HPE Comware OS switches (ie. the FlexFabric line)
* **SnmpConnectorDell()** - switches/connect/snmp/dell/connector.py - Dell switches (untested at this time)
* **SnmpConnectorJuniper()** - switches/connect/snmp/juniper/connector.py - Juniper switches in 'read-only' mode
* **SnmpConnectorProcurve()** - switches/connect/snmp/procurve/connector.py - supports the HP/Procurve 'Provision' switches


See here how to add new vendors that require non-standard connector classes.
See :doc:`Vendor implementations <vendor_specific>`
