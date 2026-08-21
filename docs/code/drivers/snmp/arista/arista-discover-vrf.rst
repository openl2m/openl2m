
.. image:: ../../../../_static/openl2m_logo.png

Arista VRF information
----------------------

Arista has a vendor MIB for VRF information: *ARISTA-VRF-MIB*, shown at https://www.arista.com/assets/data/docs/MIBS/ARISTA-VRF-MIB.txt

Similar to the standard mib, the VRF name is "OID encoded". All entries below "aristaVrfEntry" use this 'encoding'.

So, e.g. *aristaVrfName.4.78.97.109.101*  encodes a string of length 4 with value "Name"

Likewize for *aristaVrfRouteDistinguisher*, *aristaVrfRoutingStatus* , etc. where the returned value is
the meaning of the MIB counter )(ie the RD, and IPv4/v6 status)

Hence we override with a custom implementation of *get_my_vrfs()*

We read the table for *aristaVrfEntry*, and get VRF information.
This is parsed in *_parse_mib_arista_vrf_entries()*

We then read *aristaVrfIfMembership* for VRF member interfaces,
and parse this in *_parse_mib_arista_vrf_members()*


Arista Interface VRF Membership
-------------------------------

Arista has another private MIB table *aristaVrfIfTable* that contains VRF Interface information.

In that table, the element *aristaVrfIfMembership* has what we need. An example:

    aristaVrfIfMembership.999001 = STRING: "Management"

This means that the interface with ifIndex 999001 is a member of VRF "Management".
So this is somewhat easier then the standard mib!

