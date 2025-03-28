.. image:: ../../../_static/openl2m_logo.png

==============
SNMP MIBs Used
==============

Portions of the following MIB are used in OpenL2M.

Specific entries are described in more detail in the following pages.
Definitions of the entries used can be found in the various *constants.py* under *openl2m/switches/connect/snmp*

**Standards Based:**


.. list-table::
   :header-rows: 1
   :stub-columns: 1

   * - MIB
     - OID
     - Use

   * - LLDP-MIB
     - .1.0.8802.1.1.2
     -

   * - LAG MIB
     - .1.2.840.10006.300.43
     -

   * - MIB-2
     - .1.3.6.1.2.1.1
     -

   * - IP-MIB
     - .1.3.6.1.2.1.4
     -

   * - IEEE802.3 STATS-MIB
     - .1.3.6.1.2.1.10
     -

   * - MPLS-L3VPN-STD-MIB
     - .1.3.6.1.2.1.10.166
     -

   * - BRIDGE MIB
     - .1.3.6.1.2.1.17
     -

   * - Q-BRIDGE MIB
     - .1.3.6.1.2.1.17.7
     -

   * - IF-MIB
     - .1.3.6.1.2.1.31
     -

   * - ENTITY-MIB
     - .1.3.6.1.2.1.47
     -

   * - IPV6-MIB
     - .1.3.6.1.2.1.55 - OLD, deprecated
     -

   * - POE-MIB
     - .1.3.6.1.2.1.105
     -

   * - SYSLOG-MSGS-MIB
     - .1.3.6.1.2.1.192
     -

   * - IEEE8021-Q-BRIDGE-MIB
     - .1.3.111.2.802.1.1.4
     -


**Vendor specific "Enterprise MIBs":**

.. list-table::
   :header-rows: 1
   :stub-columns: 1

   * - Vendor
     - MIB
     - OID
     - Use

   * - Arista
     - ARISTA-VRF-MIB
     - .1.3.6.1.4.1.30065.3.18
     -

   * - Aruba
     - ARUBAWIRED-POE-MIB
     - .1.3.6.1.4.1.47196.4.1.1.3.8
     -

   * - Cisco
     - OLD-CISCO-SYSTEm-MIB
     - .1.3.6.1.4.1.9.2.1
     -

   * -
     - CISCO-SYSLOG-MIB
     - .1.3.6.1.4.1.9.9.41
     -

   * -
     - CISCO-CONFIG-MAN-MIB
     - .1.3.6.1.4.1.9.9.43
     -

   * -
     - CISCO-VTP-MIB
     - .1.3.6.1.4.1.9.9.46
     -

   * -
     - CISCO-VLAN-MEMBERSHIP-MIB
     - .1.3.6.1.4.1.9.9.68
     -

   * -
     - CISCO-L2L3-INTERFACE-CONFIG-MIB
     - .1.3.6.1.4.1.9.9.151
     -

   * -
     - EXTENDED-POWER-ETHERNET-MIB
     - .1.3.6.1.4.1.9.9.402
     -

   * -
     - CISCOSB-VLAN-MIB
     - .1.3.6.1.4.1.9.6.1.101.48
     -

   * -
     - CISCO-STACK-MIB
     - .1.3.6.1.4.1.9.5
     -

   * - HPE/Comware
     - HH3C-CONFIG-MIB
     - .1.3.6.1.4.1.25506.2.4
     -

   * -
     - HH3C-POWER-ETH-EXT-MIB
     - .1.3.6.1.4.1.25506.2.14
     -
   * -
     - HH3C-IF-EXT-MIB
     - .1.3.6.1.4.1.25506.2.40
     -

   * -
     - HH3C-TRANSCEIVER-INFO-MIB
     - .1.3.6.1.4.1.25506.2.70
     -

   * -
     - HH3C-LswINF-MIB
     - .1.3.6.1.4.1.25506.8.35
     -

   * - HP/Procurve
     - HPN-ICF-CONFIG-MAN-MIB
     - .1.3.6.1.4.1.11.2.14.11.15.2.4
     -

   * -
     - HPN-ICF-IF-EXT-MIB
     - .1.3.6.1.4.1.11.2.14.11.15.2.40
     -

   * -
     - HP-ICF-POE-MIB
     - .1.3.6.1.4.1.11.2.14.11.1.9
     -

   * -
     - hpSwitchStatistics
     - .1.3.6.1.4.1.11.2.14.11.5.1.9
     -

   * -
     - HP-ENTITY-POWER-MIB
     - .1.3.6.1.4.1.11.2.14.11.5.1.71
     -

   * -
     - HP-ICF-TRANSCEIVER-MIB
     - .1.3.6.1.4.1.11.2.14.11.5.1.82
     -

   * - Juniper (*R/O!*)
     - JUNIPER-IF-MIB
     - .1.3.6.1.4.1.2636.3.3
     -

   * -
     - JUNIPER-VLAN-MIB
     - .1.3.6.1.4.1.2636.3.40.1.5
     -

   * -
     - JUNIPER-L2ALD-MIB
     - .1.3.6.1.4.1.2636.3.48
     -

   * - Netgear
     - NETGEAR-SWITCHING-MIB
     - .1.3.6.1.4.1.4526.10
     -

   * -
     - NG700-SWITCHING-MIB
     - .1.3.6.1.4.1.4526.11
     -

   * -
     - NETGEAR-POWER-ETHERNET-MIB
     - .1.3.6.1.4.1.4526.10.15
     -
