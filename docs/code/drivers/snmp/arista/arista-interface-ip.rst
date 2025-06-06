
.. image:: ../../../../_static/openl2m_logo.png

=============================
Arista Interface IP addresses
=============================

In short, Arista implements the default routing table Interface IP addresses normally, ie. without context.
See details at :doc:`SNMP Interface IP Discovery.<../snmp-interface-ip>`

Interfaces in a VRF are discovered by calling the same MIB variables, but with a SNMP v3 'context' set to the VRF name.

In *_get_my_vrfs()*, if VRFs are found, we loop through those VRFs, set the SNMPv3 context,
and make the call to *_get_my_ip_addresses()* (from SnmpConnector()) again for each VRF.


EOS 'context' or VRF specific MIB data
--------------------------------------

As of EOS v4.33.2F, the 'context' (ie. VRF) SNMP data returns entries from the following MIB counters:

Command run:
    snmpwalk -n <VRF_NAME> -On -v 3 -l <your_auth_method> <auth-options-as-needed> <ip-address> .1


ipForwarding = .1.3.6.1.2.1.4.1

ipAddrEntry = .1.3.6.1.2.1.4.20.1

ipCidrRouteTable = .1.3.6.1.2.1.4.24.4

inetCidrRouteTable 		.1.3.6.1.2.1.4.24.7

ipAddressPrefixTable 		.1.3.6.1.2.1.4.32

ipAddressTable = '.1.3.6.1.2.1.4.34'

ipNetToPhysicalEntry = '.1.3.6.1.2.1.4.35.1'

BGP mib = .1.3.6.1.2.1.15

enterprise.arista = .1.3.6.1.4.1.30065

aristaSwIpForwardingMIB		.1.3.6.1.4.1.30065.3.1

aristaFIBStatsMIB		.1.3.6.1.4.1.30065.3.23
