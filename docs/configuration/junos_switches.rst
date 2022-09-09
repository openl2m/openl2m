.. image:: ../_static/openl2m_logo.png

====================
Adding Junos Devices
====================

Prerequisites
-------------

Create a Credential Profile with the proper Netconf username / password that will be used to manage this device.
As needed, create Commands and Command Groups to assign to this device.

Junos Device Configuration
--------------------------

Junos device are managed via NetConf using the Python PyEZ library. You will need to create account on your device that allows NetConf,
and then enable NetConf service using something similar to this:

.. code-block:: bash

    [edit system services]
    user@host# set netconf ssh
    user@host# set netconf ssh port 830

Please refer to your Junos documentation for more details.


OpenL2M Configuration
---------------------

From the top-right Admin menu, go to Administration, and then click on Switches, or click the "+ Add" option

Configure the name to show in the menu (does not need to be the switch hostname),
and add a description if so desired.

Add the IP v4 address or resolvable DNS name used to connect to the device.


**In the Connection Configuration section, set:**

**Connector Type:** to

* **Junos PyEZ**: this supports Junos devices that have Netconf enabled.


**SNMP Profile:**: this is a Don't Care for Junos PyEZ devices.


**Credentials Profile:**

Select the proper profile that stored the NetConf credentions. Note these credentials are also used to allow 'show/display' commands!


**Group Membership section:**

For this device to be visible to users (including Admin) in their menu, you need to add it to at least one Group!


Optional settings
-----------------

**In the Commands Configuration section, set:**

**Command List:**

Select the command list desired, if any. `See here for more <commands>`


**In View Options section, set:**

**Indentation Level:**

If > 0, will add some spaces in the menu before the switch name; this can look nicer !

**Default View:**

The Default View setting defines the opening tab when a user clicks on the
switch. Setting this to Details is useful for routers, so that ARP and
LLDP information are loaded immediately. Note that it then take a little longer
to render the page, due to the extra data that needs to be read
from the device.


**In the Access Options section, set:**

**Status:**

*Note:* switches will only show in the list if their status is *Active*.
For SNMP devices, devices need to have an SNMP Profile applied! Likewise, if a switch does not have
a Credentials profile, interface commands and global commands options will not show.

**Read-Only:**

If a switch is marked Read-Only, no user (not even admin), can change settings
on the switch. However, if commands are configured, they can be executed.
This is useful for e.g. routers.

**Bulk-Edit:**

The Bulk Edit setting is enabled by default. If disabled (un-checked),
this switch will not allow multiple interfaces to be edited at once.

**Poe-Toggle:**

If selected, users can toggle PoE on *all* ports, including those ports on vlans they do *not* have access to.
(e.g this is useful for Wifi Access Points, VOIP Phones, etc.)

**Edit description:**

Enabled by default. If *not* selected, users cannot edit the interface descriptions
on this device (regardless of rights!)


**Group Membership section:**

Finally, at the end you can add this new device to one or more groups.
