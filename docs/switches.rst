.. image:: _static/openl2m_logo.png

===================
Switch Requirements
===================

OpenL2M uses standard SNMP to find the information about interfaces on switches. It supports Snmp v2c and v3.
Snmp v1 is not supported. We recommend all devices are configured with v3.

**Standard MIBs**

OpenL2M requires the following MIBs to be available on the switches it manages:

* MIB-II, RFC 1213, https://tools.ietf.org/html/rfc1213
  This gives the 'regular' data about interfaces, names, etc.

* Interfaces Group MIB, RFC 2863, https://tools.ietf.org/html/rfc2863
  Used to read modern interface data, such as name, description, high speed interface data, and more

* Q-Bridge MIB, RFC 2674, https://tools.ietf.org/html/rfc2674
  This is used for the VLAN information.

* Power Ethernet MIB, RFC 3621, <https://tools.ietf.org/html/rfc3621
  Used to read PoE data for interfaces.

* ipNetToMediaTable entries of SMIv2 MIB in RFC2011, https://tools.ietf.org/html/rfc2011
  or ipNetToPhysicalTable in the newer RFC4293, https://tools.ietf.org/html/rfc4293.
  This is used to get mac address and ARP information.

* IEEE LLDP, LLDP-EXT-DOT1 and LLDP-EXT-DOT3 MIBs, http://www.ieee802.org/1/files/public/MIBs/
  Used to read device neighbors information.

* IEEE MLAG MIB at http://www.ieee802.org/1/files/public/MIBs/IEEE8023-LAG-MIB-201610120000Z.txt
  Used to find Link Aggregation (LACP) interface information.


**Vendor Specific MIBs**

Several vendor specific MIB are supported at this time.

* Cisco VTP MIB
  Used for VLAN information on Cisco Switches

* Cisco Extended PoE MIB
  Get enhanced PoE info on the switches that support it.

* Cisco Stacking MIB
  For stack member info, if supported.

* Cisco L2L3-INTERFACE-CONFIG MIB
  Used to see if interface is in switching or routing mode on Cisco devices

* HP Aruba/Procure HP-ICF-POE-MIB
  Get enhanced PoE info on the Aruba/Procurve switches that support it.

* HP HP-ENTITY-POWER MIB
  Old power mib, supported by some Aruba/Procurve switches to get enhanced PoE info.

* HP HPN-ICF-IF-EXT MIB
  Interface extension to get switching or routing mode on HP devices

* HPE HH3C-PoE MIB
  Get enhanced PoE info on the Comware switches that support it.

* HPE HH3C-LswINF MIB
  Used for additional layer 2 interface information in HPE Comware switches.

* HPE HH3C-LswVLAN MIB
  Used for additional VLAN data in HPE Comware switches.

* HPE HH3C-IF-EXT MIB
  Used for additional information about interfaces in HPE Comware switches (route mode, PoE capable).

* HPE HH3C-Config-Man MIB
  Used to save running configuration on HPE Comware switches.

**Switches Tested**

While an attempt has been made to make OpenL2M adhere to 'standard' SNMP, we recognize there is no such thing as
completely 'standard' SNMP. We have tested OpenL2M on the following hardware, with the listed limitations.

**Cisco**

* *Catalyst 2960* series; single and stacked units.
* *Catalyst 4500-E* series, with Sup6L-E and Sup7L-E

**HP/Aruba**

* *HP 2520G* series; single units
* *HP 4200vl* series, specifically 4204vl (J8770A)
* *Aruba 2930F* series; single units

**HP Enterprise (HPE)**

* *HPE 1950* series switches, running Comware 7; single and IRF-stacked units.
* *HPE 5130* series switches, running Comware 7; single and IRF-Stacked units.
* *HPE 5500* series switches, running Comware 5; single units.
* *HPE 5900AF* series switches, running Comware 7; single units.

**Generic**

Several generic snmp implementations on 'home wireless routers' and 'commodity' switches have been tested,
with varying results, depending on the level of SNMP support in the devices.
