.. image:: ../../_static/openl2m_logo.png

================
Drivers Overview
================

Connector() Class
-----------------

The *switches/connect/* directory contains the drivers for the various devices supported by OpenL2M.

All drivers are derived from a base Connector() class. This class provides the High-Level functions
that are called by the various Django "views".

The Connector() implements basic attributes and functions used by all drivers.
It is also the programatic interface used by the HTML templates in */templates/*,
mostly through the *conn* object passed into the templates.

The following pages attempt to document the Connector() class, and how to use it to store various pieces
of information about a device. Below that are (some) details about some of the specific drivers,
which use the Connector() class.

.. toctree::
   :maxdepth: 1

   connector.rst
   vlan_info.rst
   interface_info.rst
   ethernet_info.rst
   lldp_info.rst
   vrf_info.rst
   transceiver_info.rst
   vlan-add-del_info.rst
   permissions.rst

Interface Operations
--------------------

The following sections describe how actions on the interfaces or ports of a device are
implemented and should be used in vendor drivers.

.. toctree::
   :maxdepth: 1

   interface_up_down.rst
   interface_vlan_change.rst
   interface_poe_change.rst
   interface_description.rst
   interface_trunk_edit.rst

Running Commands
----------------

.. toctree::
   :maxdepth: 1

   netmiko/index.rst


SNMP Driver
-----------

We have implemented a "generic" SNMP driver, as well as several vendor-specific derivatives,
i.e. sub-connectors (sub-classes) to support generic, Arista, Aruba/HP-Procurve, Aruba/AOS-CX, Cisco,
Juniper, Netgear and other devices.

.. toctree::
   :maxdepth: 1

   snmp/index.rst


Other Drivers
-------------

We currently provide several connector for API-based device access.

.. toctree::
   :maxdepth: 1

   arista_eapi/index.rst
   junos_pyez/index.rst
   rest_api/index.rst
   aos_cx_api/index.rst
   aos_s_api/index.rst
   hpe_cw_api/index.rst
   napalm/index.rst
   dummy/index.rst

Driver Hierarchy
----------------

Here is an overview of the current driver inheritance scheme:

.. toctree::
   :maxdepth: 1

   hierarchy.rst

