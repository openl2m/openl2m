.. image:: ../../../_static/openl2m_logo.png

==================================
Napalm (read-only) Driver Overview
==================================

The Napalm driver is a '*read-only*' drivers, and supports all devices supported by the Napalm Python package.

The NapalmConnector() class is implemented in *switches/connect/napalm/connector.py*

The base class for Napalm connectors is the NapalmConnector() class,
defined in switches/connect/napalm/connector.py

Looking at this code, it is simply an implementation of the Connector() API using Napalm calls.
We connect via Napalm, run various commands, parse the output, and store the data in the
Connector() object and supporting data structures.

This driver may be useful for non-common devices, however it is mostly intended to be an example of
how to write drivers.

If device connections are made via Napalm, *get_connection_object()* in **connect.py** returns a
NapalmConnector() sub-class to get for the device.

This currently supports the common Napalm supported vendor drivers.

**Napalm support is only provided for demonstrative purposes** to show how to implement new drivers.
The NapalmConnector() interface supports a few vendors (Arista, Cisco, Dell, HP, Juniper),
but only in read-only mode.

.. note::

   The Napalm library does not properly support trunked or 802.1q tagged interfaces.
   We try to 'catch' this, but the untagged vlan is likely incorrect on trunked/tagged interfaces
   due to this library shortcoming.

Napalm also does not have an API to deal with Power-Over-Ethernet (PoE).


