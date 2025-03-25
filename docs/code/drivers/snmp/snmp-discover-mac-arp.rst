.. image:: ../../../_static/openl2m_logo.png

==============================
Mac, ARP and IPv6 ND Discovery
==============================

.. note::

    The process of discovering vlans, interfaces, (switch) ports, ethernet addresses and IPv4 address is explained well
    in this StackExchange posting:

    https://networkengineering.stackexchange.com/questions/2900/using-snmp-to-retrieve-the-arp-and-mac-address-tables-from-a-switch


Ethernet addresses
==================

The function *def _get_known_ethernet_addresses(self)* is used to find ethernet addresses known to the device.
We pull the Dot1Q Bridge MIB entry for *dot1qTpFdbPort*

.. note::

    This is similar to running a command like **show mac-addresses** on a switch.

This is parsed in *_parse_mibs_q_bridge_eth()*.
Returned OID and value format is:

    **dot1qTpFdbPort**.<fdb_index>.<ethernet-as-dotted-decimal> = <port-id>

Where fdb_index can be the VLAN-ID where the ethernet address is heard.

**Note: port-id is not the same as ifIndex !!!** Port-ID is the "switch port number",
tied to a physical interface that has an ifIndex. There are also virtual interfaces with ifIndexes *without* port-id!
E.g. loopbacks, vlan interfaces. etc.

**dot1dBasePortIfIndex** maps the ifIndex to a portId.
See snmp/connector.py, function _parse_mibs_vlan_related(), around line 1280

We use the _get_if_index_from_port_id() function to find the ifIndex for a given port-id.
From that ifIndex, we find the Interface(). Then we can add the ethernet data as an EthernetAddress() object
to the *Interface().eth* dictionary

Older style:
------------

If no entries are found in the Dot-1Q Q-Bridge, we check the older Dot-1d bridge mib at **dot1dTpFdbPort**.
Returned OID and values are:

    **dot1dTpFdbPort**.<ethernet-as-dotted-decimal> = <port-id>

We parse this in *_parse_mibs_dot1d_bridge_eth()* around snmp/connector.py line 1753.

Note: here we have a port-id only, but no information about the vlan! We use the same mapping to find the ifIndex.


ARP - Old Style
===============

In *def _get_arp_data(self)*, we read ARP and IPv6 ND entries.

For ARP entries (ie. IPv4 to Ethernet address mapping), we read the *older ipNetToMedia tables* for **ipNetToMediaPhysAddress**.
Parser is *self._parse_mibs_net_to_media()*

This OID returns values like:

.. code-block:: text

    ipNetToMediaPhysAddress.<ifIndex>.<IPv4 in dotted decimal> = <ethernet as 6 bytes>

Note that ifIndex is the interface for the ARP resolution, not the switch port where an ethernet is learned.
On a router that also switches, e.g. "interface Vlan 100", this will show the ethernet address on that
virtual interface ifIndex.

OpenL2M shows ethernet addresses on the physical port, e.g. Ethernet1/0/1. So, with each ethernet found here,
we first check all interfaces for knowledge of this ethernet address from the switch tables above. We update
the IPv4 address if found.

If not found, we then add a new ethernet address entry, with IPv4, on the ifIndex from this entry.

ARP and ND - New Style
======================

IPv6 has the concept of Neighbor Discovery, aka IPv6 ND. This is how IPv6 addresses map to ethernet addresses.
(aka ND is "like the ARP tables for IPv4")

The newer ipNetToPhysical tables from IP-MIB are intended to handle IPv4, IPv6 and other protocols'
address resolution in the same table, as these tables contain a field indicating *protocol*!

.. note::

    The ipNetToPhysical tables are use for both IPv4 ARP and IPv6 ND information!


In ipNetToPhysical, we read the **ipNetToPhysicalPhysAddress** entry, see *self._parse_mibs_net_to_physical()*
Each entry contains a "protocol" field, followed by IP address,
and returns the value of the Ethernet/MAC address (in byte format).

The returned OID format is:

.. code-block:: text

    ipNetToPhysicalPhysAddress.<if-index>.<address-type>.<length>.<ip address in dotted-decimal format> = <mac address as 6 bytes>

The protocol field will indicate IANA_IPV4 or IANA_IPV6, and the following ip data is formatted and parsed accordingly.

The ethernet information is returned on the routed interface, which is frequently a logical interface,
and not the physical port. (same as the ARP tables above)

OpenL2M shows ethernet addresses on the physical port, e.g. Ethernet1/0/1. So, with each IPv6 ND ethernet found here,
we first check all interfaces for knowledge of this ethernet address from the switch tables above. We update
the IPv6 address if found.

If not found, we then add a new ethernet address entry, with IPv6, on the ifIndex from this entry.
