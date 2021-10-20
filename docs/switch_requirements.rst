.. image:: _static/openl2m_logo.png

===================
Switch Requirements
===================

For the device that use standard SNMP OpenL2M supports v2c and v3.
SNMP v1 is not supported. We recommend all devices are configured with v3.

OpenL2M uses the following standard and vendor MIBs to learn and be able to manage the interfaces of a device:

**Standard MIBs**

* MIB-II, RFC 1213, https://tools.ietf.org/html/rfc1213
  This gives the 'regular' data about interfaces, names, etc.

* Interfaces Group MIB, RFC 2863, https://tools.ietf.org/html/rfc2863
  Used to read modern interface data, such as name, description, high speed interface data, and more.

* Q-Bridge MIB, RFC 2674, https://tools.ietf.org/html/rfc2674
  This is used for VLAN and Ethernet address information.

* Power Ethernet MIB, RFC 3621, <https://tools.ietf.org/html/rfc3621
  Used to read PoE data for interfaces.

* ipNetToMediaTable entries of SMIv2 MIB in RFC2011, https://tools.ietf.org/html/rfc2011
  or ipNetToPhysicalTable in the newer RFC4293, https://tools.ietf.org/html/rfc4293.
  This is used to get Ethernet address and ARP information.

* IEEE LLDP, LLDP-EXT-DOT1 and LLDP-EXT-DOT3 MIBs, http://www.ieee802.org/1/files/public/MIBs/
  Used to read device neighbors information.

* IEEE MLAG MIB at http://www.ieee802.org/1/files/public/MIBs/IEEE8023-LAG-MIB-201610120000Z.txt
  Used to find Link Aggregation (LACP) interface information.


**Vendor Specific MIBs**

Several vendor specific MIB are supported at this time.

* Cisco VTP MIB
  Used for VLAN information on Cisco Switches.

* Cisco Extended PoE MIB
  Get enhanced PoE info on the switches that support it.

* Cisco Stacking MIB
  For stack member info, if supported.

* Cisco L2L3-INTERFACE-CONFIG MIB
  Used to see if interface is in switching or routing mode on Cisco devices.

* Cisco Syslog-Mib
  Used to read log messages from Cisco devices (if configured).

* HP Aruba/Procure HP-ICF-POE-MIB
  Get enhanced PoE info on the Aruba/Procurve switches that support it.

* HP HP-ENTITY-POWER MIB
  Old power mib, supported by some Aruba/Procurve switches to get enhanced PoE info.

* HP HPN-ICF-IF-EXT MIB
  Interface extension to get switching or routing mode on HP devices.

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

* Juniper Networks L2ALD MIB
  Used for vendor-specific vlan information.
