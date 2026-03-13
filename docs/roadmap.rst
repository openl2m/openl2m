.. image:: _static/openl2m_logo.png

===============
Roadmap / To Do
===============

Planned Drivers:
----------------

* ArubaOS switches via the REST API.
* HPE Comware via NetConf API.
* :strike:`Arista devices via the eApi`

Planned Improvements:
---------------------

*In no particular order:*

* add reading of VSF interfaces (from ArubaWired-VSFv2 mib) to the Aruba AOS-CX SNMP driver.
* add reading of VSF interfaces to the Aruba AOS-CX API driver.
* :strike:`add VRF interface membership to Arista SNMP driver (uses private Mib)`
* :strike:`add Top-N reports for user and device activities.`
* move to Caddy as the WSGI/Web server.
* improve developer documentation on the various drivers (ongoing :-) ).
* :strike:`parse the newer SNMP 'ipAddressTable' mib entries for device interface address information.`
* :strike:`parse the newer SNMP 'ipNetToPhysicalTable' mib entries for ARP info.`
* :strike:`automatically set SSH connection type for drivers that should know this.`
* :strike:`update to Django 5.1 / 5.2`
* :strike:`add Python 3.12 and 3.13 compability: requires reworking of 'pysnmp' code.`
* :strike:`IPv6 support, both for switch snmp access, and other informational tables.`
* :strike:`test support for AES-192 and up. This will require Net-SNMP v5.8`
* :strike:`add MPLS L3VPN info and interface members on Juniper routers in the Junos PyEZ driver.`

Features Being Considered
-------------------------

Here are some other features we are considering implementing (*in no particular order!*)

* Single-Sign-On (SSO) via SAML, and possibly OAUTH for authorization (switch group membership)
  We plan to provide this via "overlaying" with Caddy.

* Make WebUI responsive, so pages do not have to reload. Requires back-end changes, and front-end AJAX web implementation.

* change user model, from standard user mode with separate profile table, to a new user class that has it all :-)

* Tagged/Trunked ports tagged vlan management - *in progress, now implemented for API drivers!*
  Note: this is complex for snmp devices, as this is frequently handled in a vendor-specific MIB.

* :strike:`hide change/submit buttons until form has changes (vlan, ifalias, etc.)
  This is a big undertaking changing the UI framework used.``

* make driver support dynamic (i.e. discover at runtime what vendor drivers are implemented)

* support running production in a Docker container (work in progress!)
