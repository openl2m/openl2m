.. image:: _static/openl2m_logo.png

===============
What is OpenL2M
===============

**What is OpenL2M?**

OpenL2M, or Open Layer 2 Management, is an open source network device management
application. OpenL2M is designed to allow users with minimal training to perform a set of basic
mostly Layer 2 configuration changes on those devices via a consistent web interface,
 *independent of the underlying device vendor*. OpenL2M can distribute
the management of network devices to various users and device groups. The
permissions approach taken by OpenL2M is based on vlans and device
groups. While primary intended to manage network switches, OpenL2M can handle any device
that has some sort of network API (e.g. SSH, Netconf, REST, etc.)

OpenL2M can use various device communication methods. As of v2.0, there is an
extensible API that allows for custom drivers to communicate with devices. Using this API,
drivers can be developed that support Netconf, REST and other ways to communicate with switches.
At present, SNMP and SSH (via Netmiko) are supported. Napalm support is implemented as an example of the new API.

OpenL2M is written in the Django framework, using Python 3.

**Features**

:doc:`Click here for OpenL2M screenshots <screenshots>`, showing most features.

OpenL2M can manage interfaces on switches, including:

* **enabling / disabling** of interfaces  (i.e. admin-shutdown/enable).
* **change vlan** of the interface.
* **edit** the interface **description** (a.k.a interface "alias").
* **change PoE** (Power-over-Ethernet) state (on/off/toggle).
* show power drawn on interface.
* show **Ethernet addresses** on the interfaces (i.e. MAC address, or the layer 2 switch tables).
* show **LLDP neighbor** information on interfaces.
* **bulk edit** of vlan, interface state, Power-over-Ethernet state, and description on multiple interfaces at once.
* **scheduling of bulk edits**.
* using SSH/Netmiko under the hood, we can configure **any switch CLI 'show' command** to be runnable by users from the web interface,
  shown with 'friendly' names in a drop-down menu.
* using command templates and validated fields and pick lists, commands to run on the device can be defined with some amount of user input.
* switch **device import via csv files**, or fully programmable import via Python scripts.
* switches can be Read-Only.
* support for Cisco, HP-Procurve, HP-Comware and generic switches.
* *show recent log entries* for properly configured Cisco switches.
* configurable links on the switch, or interfaces to external tools such as an NMS.
* configurable menus.
* easily extended snmp driver architecture to support other vendors that require custom snmp variables (mibs).
* **API to extend architecture** to support any device using any method supportable by Python.
* local and LDAP-based user accounts, including automatic LDAP-based group membership.


**What OpenL2M Is Not**

OpenL2M is not meant to be a network management or monitoring system (aka NMS). OpenL2M does not store data;
does not have trending and alerting capabilities; and does not have any other features typically found in
network monitoring or management systems. An admin can configure various additive web links (clickable icons)
on interfaces or devices to link OpenL2M to other enterprise network management systems
such as LibreNMS_, Observium_, Nagios_, Akips_ and others.

**How OpenL2M Works**

The distributed management approach taken by OpenL2M is based on Vlans and switch groups. Simply put, for the
switches in a group, users in that group can only access interfaces (switch ports) on vlans in a white list.
Users, and switches, can be in multiple groups, for ultimate flexibility.

In more detail, users are members of one or more Switch Groups. Each group contains one or more Vlans or Vlan Groups,
and one or more Switches. Switch Groups can be read-only, as can be switches and users.
Users will then have access to those interfaces (switch ports) on the switch that
match the Vlans in the switch group. This allows for 'multi tenant' switches,
where each 'distributed admin user' can only modify ports on the vlans in their
business unit. Users can still see the status of the others ports,
as well as see LLDP and MAC-address details, and run show-commands (if configured)

Users can be a member of multiple groups, and so can switches.
Users, switch groups, and switch group membership can be auto-generated through LDAP logins
(switches and vlans still need to be assigned manually, or via script import.)

Several pattern matches can be configured to 'remove' interfaces from view,
regardless of vlan or group membership. E.g. all ports with descriptions
matching "Trunk", or with port speeds above 9.5Gbps can be matched to be off-limits.

**Getting Started**

OpenL2M uses the Django_ framework with a PostgreSQL_ database.
It uses the Python_ v3 programming language. Most common switches are supported via SNMP v3 or v2c, and SSH.

.. _Django: https://www.djangoproject.com/
.. _PostgreSQL: http://www.postgresql.org/
.. _Python: http://www.python.org/
.. _Observium: https://www.observium.org
.. _LibreNMS: https:/www.librenms.org
.. _Akips: https:/www.akips.com
.. _Nagios: https://www.nagios.org

See the installation section for help with getting OpenL2M up and running quickly.

Next, see the configuration guide to learn how to configure the OpenL2M environment.

Finally, login to your web site and start using OpenL2M. Enjoy!

**Warranty and License**

This software is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation; either version 3 of the License, or (at your option) any later
version.

This software is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public License in LICENSE.TXT_
for more details.

.. _LICENSE.TXT: https://www.gnu.org/licenses/gpl-3.0.txt

**Influences and Credits**

OpenL2M is influenced by the Netbox_ open source tool.
OpenL2M sprouted from curiosity to figure out how Netbox works and uses the Django framework.

.. _Netbox: https://github.com/netbox-community/netbox
