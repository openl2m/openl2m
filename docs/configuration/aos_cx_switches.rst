.. image:: ../_static/openl2m_logo.png

===========================
Adding Aruba AOS-CX Devices
===========================

Prerequisites
-------------

Create a Credential Profile with the proper username / password that will be used to manage this device.
As needed, create Commands and Command Groups to assign to this device.

Switch Configuration
--------------------

AOS-CX switches are managed via the device REST API v10.08.  You will need to configure the switch to allow this access.
Something like this is needed

.. code-block:: bash

    switch(config)# https-server vrf default
    OR:
    switch(config)# https-server vrf mgmt

    and then set an admin username and password.

Please refere to your Aruba AOX-CX documentation for more.


OpenL2M Configuration
---------------------

From the top-right Admin menu, go to Administration, and then click on Switches, or click the "+ Add" option

Configure the name to show in the menu (does not need to be the switch hostname),
and add a description if so desired.

Add the IP v4 address or resolvable DNS name used to connect to the device.


**In the Connection Configuration section, set:**


**Connector Type:** to

* **Aruba AOS-CX**: for Aruba switches supported via the AOS-CX REST API. Also set the proper Credentials Profile!


**SNMP Profile:** this is a don't care field for AOS-CX switches.


**Credentials Profile:**

Select the proper profile that stores the REST API credentials. Note that these same credentials used for any Commands applied to this device.


**Group Membership section:**

For this device to be visible to users (including Admin) in their menu, you need to add it to at least one Group!


Optional settings
-----------------

In the Commands Configuration section, set:

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

