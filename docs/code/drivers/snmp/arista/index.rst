.. image:: ../../../../_static/openl2m_logo.png

===============================
Arista EOS SNMP Driver Overview
===============================

The driver is implemented in *openl2/switches/connect/snmp/arista_eos/connector.py*

The Arista SNMP capabilities mostly follow the standard SNMP mibs.
The supported mibs are documented at:

https://www.arista.com/en/support/product-documentation/arista-snmp-mibs

Below are the parts that deviate from the standard SNMP driver implemented in *SnmpConnector()*.

.. toctree::
   :maxdepth: 1
   :caption: The various parts of the Arista EOS SNMP driver:

   arista-interface-ip.rst
   arista-discover-vrf.rst
