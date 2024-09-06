.. image:: ../../_static/openl2m_logo.png

================
The switches app
================

The switches/ directory contains the main app where nearly all the
functionality is implemented. Most of the rest of this document describes
various aspects of this app.

**urls.py**

In standard Django fashion, here we map the various urls of our app.

**models.py**

We define a number of classes/objects here.

**Choices**

Several models, ie Django objects defined in models.py, have a list of "choices"
defined in the class definition. These choices are visible in the admin interface,
e.g. when you create a new SNMP Profile.

If you want to refer to these choices from a template (ie on the web page),
you can use the format model.get_*fieldname*_display,
where *fieldname* is the name of the field in the model that has choice.
Eg. the Log() object defined in models.py, has attributes called
'type' and 'action'. These fields have a list of choices
that show several fields ("View", "Change", "Error", "Warning").

To show these values in the log view template, see   templates/_tab_logs.html,
we use the format  {{ l.get_type_display }}  and   {{ l.get_action_display }}

See https://docs.djangoproject.com/en/dev/ref/models/fields/#field-choices
This statuses  "For each model field that has choices set, Django will add a
method to retrieve the human-readable name for the field’s current value.
See get_FOO_display() in the database API documentation."


**views.py**

As is typical in a Django framework application, this is where most of the
work to handle urls is done. It is also where Connector() objects are created to connect to devices.

All URLs are mapped to functions in views.py

In general, all view functions follow these high level steps.

1 - Create the Connector() object:

.. code-block:: python

  conn = get_connection_object(request, group, switch)


2 - Next, get the basic switch information. This reads Interface, Vlan, and Power-over-Ethernet data::

.. code-block:: python

   conn.get_switch_basic_info()

This information could be cached for the session, if this is the second time something is done on this switch.
E.g. you read the basic layout, then disable an interface, and go back to the main switch page.
That second time around, the cached data will be used.


3 - Then, depending on which view, another function may be called:

If **Ethernet/LLDP** data is requested, we call:

.. code-block:: python

   conn.get_switch_client_data()

This calls the following:

.. code-block:: python

    self._get_known_ethernet_addresses()
      This calls  _get_branch_by_name('dot1dTpFdbPort')

    self._get_lldp_data()
      This calls several lldp mib counters.

    self._get_arp_data()
      This calls   _get_branch_by_name('ipNetToMediaPhysAddress')


This Ethernet/LLDP data is *never cached*, so it is always the most recent data from the switch.

Admins have an additional option for some more **Hardware Details** from the switch:

.. code-block:: python

   conn.get_switch_hardware_details()

This calls two functions that need to be implemented in vendor-specific snmp classes:

.. code-block:: python

   self._get_vendor_data()

   self._get_syslog_msgs()

and then it reads the standard Entity MIB hardware info:

.. code-block:: python

   retval = self._get_entity_data()

With the SNMP driver, this reads a number of entityPhysical MIB entries. Other driver can fill in data as desired.


**Netmiko for CLI**

We use the Netmiko framework to establish SSH CLI sessions, and execute CLI commands.

See :doc:`Netmiko Connector <drivers/netmiko/index>` for more.


**Connections**

Connections to the switch are derived from a base Connector() class.
We currently provide several vendor-specific drivers. Each is a sub-class of the Connector() object:

* several based on SNMP.
* a Juniper PyEz-NC based driver.
* a Aruba AOS-CX REST-API based drivers.
* read-only demonstration driver based on the Napalm automation framework.

See :doc:`Connections and Drivers <drivers/index>` for more.

**Caching**

In order to "speed up" rendering after the initial read of a device, (nearly) all data is cached in the WebUI session.
(Note: this implies also that the REST API does NOT use caching; it is truly RESTful!)

This caching is done via functions in *switches/connect/connector.py*,
see *save_cache()*, *load_cache()*, *set_do_not_cache_attribute()*, *set_cache_variable()*, *clear_cache()*

Session Caching in Django 5 uses the JSONSerializer. The most important thing to know here is that **if you add
Dictionary variables to the session cache, the keys of this Dict will be saved as strings** (Python str() class), regardless of the actual type!

I.e. if you have a dictionay with integer keys, upon storing and re-loading from the Session,
you will have a dictionary with str() keys! **This could have unexpected results when referencing this dictionary!**

Note: In general, drivers do not need to implement caching, as this is done in the base Connector() class.

