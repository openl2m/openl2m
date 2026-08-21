.. image:: ../../_static/openl2m_logo.png

==========================
Reading ARP, ND, Neighbors
==========================

The **class SwitchDetails()** is called when reading the basic info of a device.
Like the basic view page, this also calls **switch_view()** to handle the data gathering and rendering.

**switch_view()** will process this as descibed in the previous page
(i.e. since the data may be known at this stage, it would be rendered from cache).

If the details view is requested (view == 'arp_lldp', around line 445 in view.py), a call is made to:

.. code-block:: python

   conn.get_switch_client_data()


This checks to see if the driver has a function called *get_my_client_data()* and calls it.

This *get_my_client_data()* function is responsible for reading Ethernet, ARP, IPv6 ND, and LLDP data.
It should be implemented in a device Connector() class (ie driver)

.. note::

    Ethernet/ARP/ND/LLDP data is *never cached*, so it is always the most recent data from the switch.