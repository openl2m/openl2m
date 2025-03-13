
.. image:: ../../../_static/openl2m_logo.png

===============================
Arista EOS SNMP Driver Overview
===============================

The driver is implemented in *openl2/switches/connect/snmp/arista_eos/connector.py*

The Arista SNMP capabilities mostly follow the standard SNMP mibs.
The supported mibs are documented at:

https://www.arista.com/en/support/product-documentation/arista-snmp-mibs


VRF information
---------------

Arista has a vendor MIB for VRF information: *ARISTA-VRF-MIB*, shown at https://www.arista.com/assets/data/docs/MIBS/ARISTA-VRF-MIB.txt

Hence we implement *get_my_vrfs()*

Here we read the table for *aristaVrfEntry*, and get VRF information.
This is parsed in *_parse_mib_arista_vrf_entries()*

We then read *aristaVrfIfMembership* for VRF member interfaces,
and parse this in *_parse_mib_arista_vrf_members()*

