.. image:: ../../../_static/openl2m_logo.png

====================
SNMP Driver Overview
====================

**switches/connect/snmp/connector.py**

This file defines the base SnmpConnector() class that implements all generic snmp functions to talk to switches,
according to the Connector() class API.

If device connections are made via SNMP, get_connection_object() in **connect.py** figures out what
specific SnmpConnector() sub-class to get for the device. We do this by reading the *enterprises* MIB entry,
which returns the OID string representing the device. This string include a vendor indentifier.

Since we mostly want lots of data at once (ie all interfaces, all vlans, etc.) we use the SNMP GetBulk operation
for most data collection. This is implemented in the **SnmpConnector.get_snmp_branch()** function. This needs the mandatory
snmp branch you want to walk (eg. interfaces branch), and the function that will parse the returned data (see below).

Optionally, you can pass in *non_repeaters* and *max_repetitions*. *non_repeaters* is the number of
'single' OIDs you want to 'get'. This is normally a list of single OIDs passed to GetBulk, such as sysUptime,
so you can get time along with interface values. Since we don't use this, we set it to 0.
*max_repetitions* is the number of instances of the branch you expect to get.

E.g. if there are 48 interfaces on switch, you would need at least that much to retrieve them efficiently.
We set this to a default of 25, which can be handled by most devices. This means it will take 3 bulk-reads for most 48 port switches
(with some stacking and loopback interfaces). The underlying library will take care of multiple calls if there are more ports in eg. a stack.


**get_snmp_branch()** calls used the *ezsnmp* library to do the work, and calls *ezsnmp.bulkwalk()* to read the mib data.

In the parsing loop, the return data is passed to the parser function specified in the *get_snmp_branch()* call.


EzSnmp Library use
--------------------

We use the Session() interface from the Python "EzSnmp" library. This calls the net-snmp package of the OS.
Use of the native library gives significant performance improvements over the pure Python *pysnmp* library.
The EzSNMP documentation has helpful examples. This session is stored in *SnmpConnector()._snmp_session*

Vlan manipulation via snmp requires dealing with bitmap fields that are represented in OctetString snmp data types.
EzSNMP has a hard time dealing with this due to how it internally translates everything to/from Python Unicode strings.
So we use the *pysnmp* library to handle these special cases only. See more below.

*Note: EzSNMP is the maintained successor of the original "Easy SNMP" library, which now is stale. (Summer 2024)*

PySNMP notes
------------

We use the new "pysnmp" library primarily for help with OctetString / BitMap values.
This is implemented in the pysnmpHelper() object. This class is used to perform SNMP "set" functions for
things like active ports on Vlans. EzSNMP cannot handle this cleanly, especially for uneven byte counts,
due to how it maps everything to a Python Unicode string internally!

We use v3 of the new pysnmp HLAPI. This uses asyncio, instead of the old version that used synchronous io.
This requires the use of some cool programming techniques, shown in the class, and documented at
https://docs.lextudio.com/pysnmp/v7.1/


**IMPORTANT DATA TYPES:**

There are several Python dictionaries used to store data. Several of these have specific key data typem requirements.

They are:

* self.vlans: the key (index) is an *integer (int)* representing the numeric vlan ID. Items are Vlan() class instances.

* self.interfaces: this key (index) is a *string (str)*, representing a driver-specific key (frequently the name or snmp interface index)
  Items are Interface() class instances.

* interface.port_id: this is an *integer (int)* representing the switch port ID. This comes into play with SNMP drivers,
  as the interface index and the switchport ID can be different.

*More details on the SNMP drivers, and specific MIB entries used, will be written as time allows...*


Vendor-specific SNMP implementations
------------------------------------

Most switches supported use inherit the base SnmpConnector() class and override the vendor-specific functions.
The vendor-specific derived classes are:

* **SnmpConnectorArista()** - switches/connect/snmp/arista_eos/connector.py - supports all Arista devices.
* **SnmpConnectorArubaCx()** - switches/connect/snmp/aruba_cx/connector.py - supports the HP/Aruba AOS-CX switches,
  which implement partial SNMP support.(They prefer the AOS-CX API)
* **SnmpConnectorCisco()** - switches/connect/snmp/cisco/connector.py - most Cisco switches
* **SnmpConnectorComware()** - switches/connect/snmp/comware/connector.py - HPE Comware OS switches (ie. the FlexFabric line)
* **SnmpConnectorDell()** - switches/connect/snmp/dell/connector.py - Dell switches (untested at this time)
* **SnmpConnectorJuniper()** - switches/connect/snmp/juniper/connector.py - Juniper switches in 'read-only' mode
* **SnmpConnectorProcurve()** - switches/connect/snmp/procurve/connector.py - supports the HP/Procurve 'Provision' switches
