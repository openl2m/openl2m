.. image:: ../../../_static/openl2m_logo.png

================
Drivers Overview
================

The switches/connect/ directory contains the drivers for the various devices supported by OpenL2M.

All drivers are derived from a base Connector() class.
We currently provide several sub-connectors (sub-classes):

* several based on SNMP (Cisco, Juniper, Aruba/HP, Aruba/AOS-CX, generic).
* a Juniper PyEz-NC API based driver.
* a REST-API based connector for the Aruba AOS-CX line of devices.
* a read-only driver based on the Napalm automation framework.

A simple Netmiko-based class is used for SSH connectivity to devices.

.. toctree::
   :maxdepth: 1
   :caption: Here is more information about the Connector() and each driver:

   connector.rst
   snmp.rst
   aos-cx-driver.rst
   junos-driver.rst
   new-drivers.rst
   netmiko.rst
   napalm.rst
