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

This is parsed in *_parse_mibs_q_bridge_eth()*.
Returned OID and value format is:

    **dot1qTpFdbPort**.<fdb_index>.<ethernet-as-dotted-decimal> = <port-id>

Where fdb_index can be the VLAN-ID where the ethernet address is hear.

**Note: port-id is not the same as ifIndex !!!** Port-ID is the "switch port number", tied to a physical interface that has an ifIndex.
This is mapped from the *dot1dBasePortIfIndex*, which gives the ifIndex for a portId.
See snmp/connector.py, function _parse_mibs_vlan_related(), around line 1280

We use the _get_if_index_from_port_id() function to find the ifIndex.
Then we can add this EthernetAddress() object to the *Interface().eth* dictionary

Older style:
------------

If no entries are found in the Dot-1Q Q-Bridge, we check the older Dot-1d bridge mib at **dot1dTpFdbPort**.
Returned OID and values are:

    **dot1dTpFdbPort**.<ethernet-as-dotted-decimal> = <port-id>

We parse this in *_parse_mibs_dot1d_bridge_eth()* around snmp/connector.py line 1753.

Note: here we have a port-id only, but no information about the vlan!






ARP resolution
==============

In *def _get_arp_data(self)*, we read ARP and IPv6 ND entries. For ARP entries (ie. IPv4 to Ethernet address mapping),
we read the older ipNetToMedia tables for *ipNetToMediaPhysAddress*. Parser is *self._parse_mibs_net_to_media()*


Additionally, we also read the newer ipNetToPhysical tables for *ipNetToPhysicalPhysAddress*, see *self._parse_mibs_net_to_physical()*
Each entry contains a "protocol" field, followed by IP address, and returns the value of the Ethernet/MAC address (in byte format).

The returned OID format is:

.. code-block:: text

    ipNetToPhysicalPhysAddress.<if-index>.<address-type>.<length>.<ip address in dotted-decimal format> = <mac address as 6 bytes>


.. note::

    *ipNetToPhysicalPhysAddress* also contains IPv6 to Ethernet address info.
    This is the IPv6 "ND" Neighbor Discovery table!

The protocol field will indicate IANA_IPV4 or IANA_IPV6, and the following ip data is formatted and parsed accordingly.


IPv6 ND
=======

IPv6 has the concept of Neighbor Discovery, aka IPv6 ND. This is how IPv6 addresses map to ethernet addresses.
(aka ND is "like the ARP tables for IPv4")

The *ipNetToPhysical* tables entry *ipNetToPhysicalPhysAddress* also contains IPv6 ND data. This is parsed in *self._parse_mibs_net_to_physical()*

.. note::

    *ipNetToPhysicalPhysAddress* contains both IPv4 "ARP" data, and IPv6 "ND" Neighbor Discovery information!