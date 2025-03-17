.. image:: ../../../_static/openl2m_logo.png

====================
SNMP Driver Overview
====================

The SNMP driver
---------------

Several vendors allow a pure Snmp connector. The base SnmpConnector() and related code is in the
*switches/connect/snmp/* directory. There are several vendor-specific snmp drivers derired from the
base snmp class.

Below are some documents that explain how we extract interface and vlan information from the
various SNMP MIBs. Most of that data is read from 'Standard' MIBs, and some vendors have vendor extensions
for additional data.

.. toctree::
   :maxdepth: 1
   :caption: The various parts of the SNMP driver:

   snmp-base.rst
   snmp-discover-vlan.rst
   snmp-discover-interface.rst
   snmp-discover-mac-arp.rst
   snmp-interface-ip.rst
   snmp-discover-vrf.rst
   snmp-transceiver-type
   snmp-vlan-add-del.rst

Additional vendor-specific SNMP drivers information is here, in alphabetical order:

.. toctree::
   :maxdepth: 1

   arista-eos-driver.rst
   aos-cx-driver.rst
   cisco-driver.rst
   hpe-comware-driver.rst
   hp-procurve-driver.rst
   juniper-driver.rst
