.. image:: ../../../_static/openl2m_logo.png

===============================
Discover interface IP addresses
===============================

IPv4
====

There is an OLD and DEPRECATED MIB entry in the IP-MIB (RFC-4293 at time of writing): ipAddrTable

This table is still supported on many devices, but can only be used to find IPv4 addresses of interfaces.


IPv6
====

Likewise, there is an OLD and DEPRECATED MIB entry in the IPV6-MIB: ipv6AddrPfxLength
This returns IPv6 address and prefix length for interfaces. This tables is still supported on some devices.


IPv6 and IPv4
=============

The 'modern' way to get interface addresses for IPv4 or IPv6 is from the newer IP-MIB ipAddressTable
entry *ipAddressIfIndex* This table index has a field indicating protocol,
and can be used for more then IP addresses.

  