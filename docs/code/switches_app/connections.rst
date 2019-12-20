.. image:: ../../_static/openl2m_logo.png


===========
Connections
===========

Switch connections are via SNMP. All functions for connections is in the
"switches/connect/" directory.


**connect.py**

get_connection_object() figures out what specific SnmpConnector() class to get for the device.
It returns the proper object.

**snmp.py**
The primary class is the SnmpConnector() class, defined in switches/connect/snmp.py
This is the base class that implements all high-level functions to talk to switches.

Since we mostly want lots of data at once (ie all interfaces, all vlans, etc.) we use the SNMP GetBulk operation
for most data collection. This is implemented in the _get_branch_by_name() function. This needs the mandatory
snmp branch you want to walk (eg. interfaces branch).

Optionally, you can pass in non-repeaters and max-max_repetitions. Non-repeaters is the number of
'single' OIDs you want to 'get'. This is normally a list of single OIDs passed to GetBulk, such as sysUptime,
so you can get time along with interface values. Since we don't use this, we set it to 0
max-max_repetitions is the number of instances of the branch you expect to get.

E.g. if there are 48 interfaces on switch, you would need at least that much to retrieve them efficiently.
We set this to a default of 60, which should cover most 48 port switches (with some stacking and loopback interfaces).
The underlying library will take care of multiple calls if there are more ports in eg. a stack.



**_get_branch_by_name()** calls  easy_snmp.bulkwalk() to get the mib data.

In the parsing loop, the return data is parsed via   **_parse_oid_and_cache()**

This in turn calls **_parse_oid()** and if the return is valid (i.e. parsed),
adds the data to the **oid_cache[]** to store in the local cache (which is kept in the HTTP session)
Subsequent actions to the switch (i.e. new instatiations of the connection object) will load data from this cache,
instead of re-reading the switch.

**Data Caching**

Initially, the HTTP session cache is empty. After the SnmpConnector() object is instantiated, switch data is read with
get_basic_switch_info(). SNMP reads store data in the HTTP session.

On subsequent page renders, __init__() reads the http session data with _get_http_session_cache().

_get_http_session_cache() in turn uses _parse_oid_cache() to parse data from the cache.

_parse_oid_cache() loops through cached items, and rebuilds interfaces and permissions.

Finally, pages can go on with their work.


EasySnmp Library use
--------------------

We use the Session() interface from the Python "Easy SNMP" library.
This calls the net-snmp package of the OS.
This gives significant performance improvements over *pysnmp*
(a snmp library written in native Python). The EasySNMP documentation has helpful examples.

Vlan manipulation via snmp requires dealing with bitmap field that are represented in OctetString snmp data types.
EasySNMP has a hard time dealing with this due to how it internally translates everything to/from Unicode strings.
So we use the pysnmp library to handle these special cases only.



Netmiko functionality
---------------------

When we need to SSH to execute commands on the switch, we call a Netmiko
wrapper class defined in switches/connect/netmiko/netmiko.py
