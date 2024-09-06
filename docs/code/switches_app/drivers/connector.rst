.. image:: ../../../_static/openl2m_logo.png

======================
The Connector() Object
======================

Switch connections are made via the **Connector() class**. The Django "views" in
*switches/views.py* instantiate an object derived from this Connector() class.

.. image:: ../../../_static/openl2m-architecture.png

The Connector() API
-------------------

**connect.py**

**get_connection_object()** figures out what specific Connector() class to get
for the device. This is based on the Switch() configuration in the admin pages.
It returns the proper object. It is called by all 'views.py' functions
to get an object for the current device/switch.

It should be called as:

.. code-block:: python

  try:
        conn = get_connection_object(request, group, switch)
    except Exception:
        # handle exception as needed


**connector.py**

The Connector() API is defined in *switches/connect/connector.py*. This *Connector()* base class
is inherited by all device- or vendor-specific connectors.

**Data Collection**

Collecting data from the device/switch is done from two primary functions:

*conn.get_my_basic_info()* and *conn.get_my_client_data()*

**get_my_basic_info()** is called when a switch is selected from the menu,
and is called from the corresponding Django view.
This function should load the necessary information about interfaces
to produce the basic switch view.

More especially, this should load:

* the connector.vlans{} dictionary with Vlan() objects.
* the connector.interfaces{} dictionary with Interface() objects, each one representing an
  interface on the device.

Note that these supporting classes (objects) are defined in *switches/connect/classes.py*

A good example is in *switches/connect/snmp/connector.py*, where *get_my_basic_info()*
uses snmp to get information on interfaces, vlans, lacp info, PoE, and more.

**IMPORTANT DATA TYPES:**

There are several Python dictionaries used to store data. Several of these have specific key data type requirements.
They are:

* *self.vlans*: the key (index) is an *integer (int)* representing the numeric vlan ID. Items are Vlan() class instances.

* *self.interfaces*: this key (index) is a *string (str)*, representing a driver-specific key (frequently the name or snmp interface index, aka ifIndex)
  Items are Interface() class instances.

* *interface.port_id*: this is an *integer (int)* representing the switch port ID. This comes into play with SNMP drivers,
  as only physical interfaces have port id's, and the interface index and the switchport ID can be different.
  For more details, read the SNMP driver explanations.



**get_my_client_data()** is called when the user clicks the related button when the device is shown.
Is it called to load information about the known ethernet addresses, arp tables, lldp neighbors,
and more. It should load additional data structures of the Connection() object.

A good example is in *switches/connect/snmp/connector.py*, where *get_my_client_data()* uses snmp
to get information on switch tables (ethernet addresses), arp tables and neighbor devices via lldp.


**Data Caching**

The current device is cached in the HTTP session cache. After the Connector() object is instantiated,
switch data is read with *get_basic_switch_info()*. Various list, dictionaries and regular
variables are stored in the Connection() object, and are cached
at the end of processing of the Django 'view' call with **Connector().save_cache()**

On subsequent page views, there is a check for the current device in the *get_connection_object()*
call. If still the same, any existing cache is read by calling *Connector().load_cache()*.

**save_cache()** and **load_cache()** use the HTTP request object session to store and read the cached data.
This defaults to storing in the database, but can be configured via the standard Django session configuration.

Finally, view pages can go on with their work.


