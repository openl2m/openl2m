.. image:: _static/openl2m_logo.png

===============
Roadmap / To Do
===============

Planned Improvements:
---------------------

*In no particular order:*

* simplify the Juniper PyEX driver by using pyez operation tables and views.
* add MPLS L3VPN info and interface members on Juniper routers in the Junos PyEZ driver
* add reading of VSF interfaces (from ArubaWired-VSFv3 mib) to the Aruba AOS-CX SNMP driver.
* add reading of VSF interfaces to the Aruba AOS-CX API driver.
* :strike:`add VRF interface membership to Arista SNMP driver (uses private Mib)`
* :strike:`add Top-N reports for user and device activities.`
* move to Caddy as the WSGI/Web server.
* improve developer documentation on the various drivers.


Features Being Considered
-------------------------

Here are some other features we are considering implementing (*in no particular order!*)

* Single-Sign-On (SSO) via SAML, and possibly OAUTH for authorization (switch group membership)
  We plan to provide this via "overlaying" with Caddy.

* change user model, from standard user mode with separate profile table, to a new user class that has it all :-)

* support for Arista device via the eApi.

* IPv6 support, both for switch snmp access, and other informational tables.

* Tagged/Trunked ports tagged vlan management (we can do the untagged vlan now)

* hide change/submit buttons until form has changes (vlan, ifalias, etc.) This is a big undertaking changing the UI framework used.

* make vendor support dynamic (i.e. discover at runtime what vendors are supported)

* test support for AES-192 and up. This will require Net-SNMP v5.8 (which is available on CentOS 8, Unbuntu 2020-LTS, and later)

* support running production in a Docker container (work in progress!)
