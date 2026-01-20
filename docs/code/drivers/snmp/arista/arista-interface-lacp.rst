
.. image:: ../../../../_static/openl2m_logo.png

Arista LACP Interfaces
----------------------

Arista appears to have implemented the LACP mib incorrectly (or at least different from other device vendors).
Hence we have to override the base *SnmpConnector()._get_lacp_data()* function.

See *switches/connect/snmp/arista_eos/connector.py* around line 101

The learning of the LACP Port-Channel interfaces by reading **dot3adAggActorAdminKey** is correct.
We parse this with the standard base *SnmpConnector()._parse_mibs_lacp_admin_key()*

Next, reading **dot3adAggPortActorAdminKey** is supposed to return the *member interface ifIndex*,
pointing to the *ifIndex of the LACP Port-Channel interface* in the returned value (val).

However, this returns the port-channel number in '*val*'! Hence we parse this separately in
*SnmpConnectorAristaEOS()._parse_mibs_lacp_member_port_arista* to find the proper
*Port-Channel<val>* that a member interface belongs to.

E.g.:

The read data is "dot3adAggPortActorAdminKey.<1001> = 9"
This means that interface with ifIndex 1001 is a member of Port-Channel9
