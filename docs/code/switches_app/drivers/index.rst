.. image:: ../../../_static/openl2m_logo.png

================
Drivers Overview
================

The switches/connect/ directory contains the drivers for the various devices supported by OpenL2M.

All drivers are derived from a base Connector() class.
We currently provide several sub-connectors (sub-classes):

* several based on SNMP (generic, Arista, Aruba/HP-Procurve, Aruba/AOS-CX, Cisco, Juniper).
* a Juniper PyEz-NC API based driver.
* a REST-API based connector for the Aruba AOS-CX line of devices.
* a read-only driver based on the Napalm automation framework.

A simple Netmiko-based class is used for SSH connectivity to devices.

.. toctree::
   :maxdepth: 1
   :caption: Here is information about the Connector() class:

   connector.rst
   ethernet_info.rst
   lldp_info.rst
   vrf_info.rst
   vlan-add-del_info.rst

.. toctree::
   :maxdepth: 1
   :caption: And here are more details about each driver:

   snmp/index.rst
   aos_cx_api/index.rst
   junos_pyez/index.rst
   napalm/index.rst
   netmiko/index.rst
   new-drivers.rst
