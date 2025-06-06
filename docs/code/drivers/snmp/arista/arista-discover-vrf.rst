
.. image:: ../../../../_static/openl2m_logo.png

Arista VRF information
----------------------

Arista has a vendor MIB for VRF information: *ARISTA-VRF-MIB*, shown at https://www.arista.com/assets/data/docs/MIBS/ARISTA-VRF-MIB.txt

Hence we implement *get_my_vrfs()*

Here we read the table for *aristaVrfEntry*, and get VRF information.
This is parsed in *_parse_mib_arista_vrf_entries()*

We then read *aristaVrfIfMembership* for VRF member interfaces,
and parse this in *_parse_mib_arista_vrf_members()*

