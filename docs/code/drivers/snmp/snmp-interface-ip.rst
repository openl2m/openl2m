.. image:: ../../../_static/openl2m_logo.png

===============================
Discover interface IP addresses
===============================

We call _get_my_ip_addresses() to read the device interface IP addresses *in the default routing table*.
We do this in a number of ways, as follows.


IPv4
====

There is an OLD and DEPRECATED MIB entry in the IP-MIB (RFC-4293 at time of writing, started with RFC1213): **ipAddrTable** (.1.3.6.1.2.1.4.20)

This table is still supported on many devices, but can only be used to find IPv4 addresses of interfaces.

This is parsed in *_parse_mibs_ip_addr_table()*

Specifically,

**ipAdEntIfIndex** (.1.3.6.1.2.1.4.20.1.2) can be read to get both the IPv4 address for an ifIndex (647 in the example below).

The returned OID and values look like this:

    ipAdEntIfIndex.10.163.188.2 = 647

The field **ipAdEntNetMask** (.1.3.6.1.2.1.4.20.1.3) is read to get the accompanying subnet mask value.

The returned OID and values look like this:

    ipAdEntNetMask.10.163.188.2 = 255.255.254.0


IPv6
====

Likewise, there is an OLD and DEPRECATED MIB entry in the IPV6-MIB (**ipv6MIB** or .1.3.6.1.2.1.55): **ipv6AddrPfxLength**
This returns IPv6 address and prefix length for interfaces. This tables is also still supported on some devices.

We read **ipv6AddrPfxLength** (.1.3.6.1.2.1.55.1.8.1.2) as this returns both the IPv6 address and prefix length for an ifIndex.

This is parsed in *_parse_mibs_ipv6_interface_address()*

Format is ipv6AddrPfxLength.<ifIndex>.<ipv6 in 16 decimals> = <prefix-len>

The returned OID and values look like this:

    ipv6AddrPfxLength.18.254.128.0.0.0.0.0.0.2.204.52.255.254.168.110.119 INTEGER = 64

where ifIndex=18, IPv6 address = 254.128.0.0.0.0.0.0.2.204.52.255.254.168.110.119, which is fe80::2cc:34ff:fea8:6e77 (link-local),
with prefix-length 64.



IPv6 and IPv4
=============

The 'modern' way to get interface addresses for IPv4 or IPv6 is from the newer IP-MIB **ipAddressTable** (.1.3.6.1.2.1.4.34)

The table index at **ipAddressIfIndex** (.1.3.6.1.2.1.4.34.1.3) has a field indicating protocol
and thus can be used for more multiple addresses.

We commonly see type 1(IPv4), type 2 (IPv6) and also type 4

Specifically, the field **ipAddressPrefix** contains the interface IP, the interface ifIndex, subnet ip and prefix all in one entry!

The returned OID is structured as shown here:

.. code-block:: text

    ipAddressPrefix.<address-type>.<length>.<interface-dotted-decimal-ip-address> =
            ipAddressPrefixOrigin.<ifIndex>.<add-type>.<addr-lenght>.<subnet-ip-in-dotted-decimal>.<subnet-prefix-length>

where ipAddressPrefixOrigin = ".1.3.6.1.2.1.4.32.1.5"

We parse this in *_parse_mibs_ip_address_prefix()*, and set interface IP for both v4 and v6.


.. note::

    Standard SNMP MIBs described below do not include VRF context — they typically expose only the default
    routing table data. !

The above means that if an interface is assigned to a VRF, it will not appear in the above tables by default!
**Hence we will not know the IP address for those interfaces, unless a vendor MIB implementes this data
and our driver supports it!**

However, some vendors have implemented access to VRF-specific interface data using the 'context'
field in an SNMP v3 query. Ie. set the context to the VRF name, and they will return **ipAddressTable** (newer)
or **ipAddrTable** (older) data specific to that VRF. Some drivers support this (e.g. Arista Networks).
See the vendor-specific entries for more.

