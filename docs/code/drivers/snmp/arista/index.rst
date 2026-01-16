.. image:: ../../../../_static/openl2m_logo.png

===============================
Arista EOS SNMP Driver Overview
===============================

The driver is implemented in *openl2/switches/connect/snmp/arista_eos/connector.py*, and inherits from the base SnmpConnector() class.

:underline:`The Arista SNMP capabilities mostly follow the standard SNMP mibs.`
The supported mibs are documented at:

https://www.arista.com/en/support/product-documentation/arista-snmp-mibs

Below are the parts that deviate from the standard SNMP driver implemented in *SnmpConnector()*.
Ie. we only describe the functions that are overridden in the *SnmpConnectorAristaEOS()* class.

.. toctree::
   :maxdepth: 1
   :caption: The various non-standard parts of the Arista EOS SNMP driver:

   arista-interface-ip.rst
   arista-interface-lacp.rst
   arista-discover-vrf.rst
