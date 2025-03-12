.. image:: ../../../_static/openl2m_logo.png

=======================
Discover VRFs with SNMP
=======================

VRF info
========

This section describes how we discover L3VPN aka. "VRF" info.

This is implemented in the *switches.connect.snmp.connector.SnmpConnector().get_my_vrfs()* function, 
which is called from *switches.connect.connector.Connector().get_hardware_details()*

VRF information on a device is added to the *Connector().vrfs{}* dictionary, indexed by VRF name.

"Generic" SNMP
--------------

The Standard MIB "MPLS-L3VPN-STD-MIB" implements VRF data. (aka L3VPN). This is defined in https://www.rfc-editor.org/rfc/rfc4382.html
A good reference is also https://mibs.observium.org/mib/MPLS-L3VPN-STD-MIB/

The parsing is implemented in *switches.connect.snmp.connector._parse_mib_mpls_l3vpn()*

The mib entry *mplsL3VpnVrfEntry* is a table with a series of rows below it.
Each row is "indexed" by the VRF NAME encoded as an OID string. This is best explained with an example:

mplsL3VpnVrfName = ".1.3.6.1.2.1.10.166.11.1.2.2.1.1"

So the returned OID *".1.3.6.1.2.1.10.166.11.1.2.2.1.1.8.86.82.70.45.78.97.109.101"* is 
*mplsL3VpnVrfName.8.86.82.70.45.78.97.109.101*. 

This tells us the VRF name is a string of length 8, with the value "VRF-Name".
V is ascii code 86, R is 82, etc.

The other table row entries then give us the details about the VRF. Another example:

*mplsL3VpnVrfDescription.8.86.82.70.45.78.97.109.101* = STRING "The description of the VRF"
*mplsL3VpnVrfRD.8.86.82.70.45.78.97.109.101* = STRING "64000:100"

Ie. here we have a description and the VRF "RD" value for the above VRF named "VRF-Name"


Arista Specific
---------------

Arista uses a vendor mib "ARISTA-VRF-MIB", see https://www.arista.com/assets/data/docs/MIBS/ARISTA-VRF-MIB.txt

Similar to the standard mib, the VRF name is "OID encoded". All entries below "aristaVrfEntry" use this 'encoding'.

So, e.g. *aristaVrfName.4.78.97.109.101*  encodes a string of length 4 with value "Name"

Likewize for *aristaVrfRouteDistinguisher*, *aristaVrfRoutingStatus* , etc. where the returned value is
the meaning of the MIB counter )(ie the RD, and IPv4/v6 status)

Parsing in handled in *switches.connect.snmp.arista_eos.connector._parse_mib_arista_vrf_entries()*



Interface VRF membership
========================

On layer 3 devices, we may be able to find what VRF a specific interface is a member of.
This is stored in the *Interface().vrf* attribute, as a string with the name of the VRF.
Note this can be used as an index into the *Connector().vrfs{}* dictionary for more information.

"Generic" SNMP
--------------

See the standard MIB here: https://www.rfc-editor.org/rfc/rfc4382.html#page-4

The MPLS mib table *mplsL3VpnIfConfEntry* has a number of rows with information about VRF interfaces.
Each entry has the VRF name as OID encoded, followed by the ifIndex. The value of that entry is indicative of the entry data.

This parsing is implemented in *switches.connect.snmp.connector._parse_mib_mpls_vrf_members()*

Again an example:

mplsL3VpnIfVpnClassification = ".1.3.6.1.2.1.10.166.11.1.2.1.1.2"

This entry specifies the type of VRF on an interface (carrier, enterprise or internet-provider).
The value is not interesting to us, but the full OID is. It looks like:

    mplsL3VpnIfVpnClassification.<vrf-name-as-oid-encoded>.<if_index> = value.

So the sub-oid gives us a VRF name, and an interface tied to it. We parse this for the vrf name, 
and lookup the interface from the index. Then we assign that interface to the Vrf() object, and
set the Interface.vrf to point to that Vrf() object.

The same goes for the other table entries. Since we don't care (mostly) about the returned values,
we try one more entry (mplsL3VpnIfVpnRouteDistProtocol) if the device does not implement mplsL3VpnIfVpnClassification.



Arista Specific
---------------

Arista has a private MIB table *aristaVrfIfTable* that contains VRF Interface information.

In that table, the element *aristaVrfIfMembership* has what we need. An example:

    aristaVrfIfMembership.999001 = STRING: "Management"

This means that the interface with ifIndex 099001 is member of VRF "Management".
So this is somewhat easier then the standard mib!

