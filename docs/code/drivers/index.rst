.. image:: ../../_static/openl2m_logo.png

================
Drivers Overview
================

Connector() Class
-----------------

The *switches/connect/* directory contains the drivers for the various devices supported by OpenL2M.

All drivers are derived from a base Connector() class. This implements basic attributes and functions
used by all drivers. It is also the programatic interface used by the HTML templates in */templates/*,
mostly through the *conn* object passed into the templates.

The following pages attempt to document the Connector() class, and how to use it to store various pieces
of information about a device. Below that are (some) details about some of the specific drivers,
which use the Connector() class.

.. toctree::
   :maxdepth: 1
   :caption: Information about the Connector() class:

   connector.rst
   vlan_info.rst
   interface_info.rst
   ethernet_info.rst
   lldp_info.rst
   vrf_info.rst
   vlan-add-del_info.rst

Vendor Drivers
--------------

Here are some details about some of the drivers we have implemented.
We currently provide several sub-connectors (sub-classes):

* several based on SNMP (generic, Arista, Aruba/HP-Procurve, Aruba/AOS-CX, Cisco, Juniper, Netgear).
* a Juniper PyEz-NC API based driver.
* a REST-API based connector for the Aruba AOS-CX line of devices.
* a read-only driver based on the Napalm automation framework.

Note that the SNMP driver can support several vendors that implemented their own SNMP data.
See that driver for more details

A simple Netmiko-based class is used for SSH connectivity to devices, used to run CLI commands.

Finally, we provide an overview of how to implement a new driver.

.. toctree::
   :maxdepth: 1
   :caption: Details about (some of) the drivers:

   snmp/index.rst
   aos_cx_api/index.rst
   junos_pyez/index.rst
   napalm/index.rst
   netmiko/index.rst
   new-drivers.rst
