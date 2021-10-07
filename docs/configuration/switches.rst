.. image:: ../_static/openl2m_logo.png

========
Switches
========

Adding switches
===============

From Admin, click on Switches, or click the "+ Add" option

Configure the name to show in the menu (does not need to be the switch hostname),
and add a description if so desired.

In the Connection Type, choose:
- SNMP: for fully snmp manageable devices (Cisco, HP/Procurce, HPE)
- Commands-Only: if you want to add a device where users can only run pre-defined commands. This device will not show the interface and BulkEdit tabs.
- Napalm: add a device that is not supported bvia SNMP. The Napalm library supports lots of devices, to some extent or another.
  *This is a Read-Only driver!* For Napalm, the following field sets the Napalm device type.

Add the IP v4 address or resolvable DNS name, and the SNMP profile as a minimum.
If you want to allow 'show/display' commands, you need to add a Netmiko (SSH)
profile as well.

Note: switches will only show in the list if their status is active,
and for SNMP devices, they have an SNMP Profile applied! Likewise, if a switch does not have
a Netmiko profile, interface commands and global commands options will not show.

If a switch is marked Read-Only, no user (not even admin), can change settings
on the switch. However, if commands are configured, they can be executed.
This is useful for e.g. routers.

The Default View setting defines the opening tab when a user clicks on the
switch. Setting this to Details is useful for routers, so that ARP and
LLDP information shows immediately. Note that it then take a little longer
to render the page, due to the extra SNMP data that needs to be read
from the device.

The Bulk Edit setting is enabled by default. If disabled (un-checked),
this switch will not allow multiple interfaces to be edited at once.

You can add any switch many times, with the same IP address but a
different name. However, the combination of the name and ip address
needs to be unique.
