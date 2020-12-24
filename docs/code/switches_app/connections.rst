.. image:: ../../_static/openl2m_logo.png


===========
Connections
===========

Switch connections are made via the **Connector() class**. The Django "views" in switches/views.py instantiate an object
derived from the Connector() class. See this image:

.. image:: ../../_static/openl2m-architecture.png

**The Connector() API**

The API is defined in "switches/connect/connector.py". This *Connector()* base class
is inherited by all device- or vendor-specific connectors.


**connect.py**

**get_connection_object()** figures out what specific Connector() class to get for the device.
It returns the proper object. It is called by all 'view' functions to get an object for the current device/switch.

It should be called as:

.. code-block:: bash

  try:
        conn = get_connection_object(request, group, switch)
    except Exception:
        # handle exception as needed

**Data Collection**

Collecting data from the device/switch is done from two primary functions:

conn.get_my_basic_info() and conn.get_my_client_data()

*get_my_basic_info()* is called when a switch is selected from the menu, and is called from the corresponding Django view.
This function should load the necessary information about interfaces to produce the basic switch view.

More especially, this should load:
-the conn.vlans{} dictionary with Vlan() objects
-the conn.interfaces{} dictionary with Interface() objects, each one representing an
interface on the device.

Note that these support classes/objects are defined in switches/connect/classes.py

A good example is in switches/connect/snmp/connector.py, where get_my_basic_info() uses snmp to get information on
interfaces, vlans, lacp info, PoE, and more.

*get_my_client_data()* is called when the user click the related button when the device is shown. Is it called to load
information about the know ethernet addresses, arp tables, lldp neighbors, and more. It should load additional data
 structures of the Connection() object, such as

 A good example is in switches/connect/snmp/connector.py, where get_my_client_data() uses snmp to get information on
 switch tables (ethernet addresses), arp tables and neighbor devices via lldp.


**Data Caching**

The current device is cached in the HTTP session cache. After the Connector() object is instantiated, switch data is read with
get_basic_switch_info(). Various list, dictionaries and regular variables are stored in the Connection() object, and are cached
at the end of processing of the Django 'view' call with **Connector().save_cache()**

On subsequent page view, there is a check for the current device in the get_connection_object() call. If still the same, any
existing cache is read by calling Connector().load_cache().

**save_cache()** and **load_cache()** use the HTTP request object session to store and read the cached data. This defaults to storing in the database, but
can be configured via the standard Django session configuration.

Finally, view pages can go on with their work.


**SNMP specific implementation**

Several vendors allow a pure Snmp connector. The base SnmpConnector() and related code is in the
*switches/connect/snmp/* directory.

See :doc:`SNMP Connector <snmp>`


**Napalm framework**

We implement the needed functionality of the Connector() class in a NapalmConnector() class,
implemented in *switches/connect/napalm/connector.py*

See :doc:`Napalm Connector <napalm>`
