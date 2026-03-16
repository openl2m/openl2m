.. image:: ../_static/openl2m_logo.png

==============================
Adding HPE Comware API Devices
==============================

This documents how to add devices using the HPE Comware REST API.

Prerequisites
-------------

Create a Credential Profile with the proper username / password that will be used to access this device via the REST API.
As needed, create Commands and Command Groups to assign to this device.

.. note::

    These credentials will also be used for running SSH commands, and for saving the current configuration to startup config.


Switch Configuration
--------------------

HPE Comware devices using the Comware REST API driver are managed via the REST protocol.
You will need to configure the device to allow this access. Something like the below example is needed,
depending on your specific Comare device:


.. code-block:: bash

    restful https enable
    https acl <your-access-acl-number>      # not supported on all devices!

    local-user <your_api_user> class manage
    password simple <your password here>
    service-type https ssh
    authorization-attribute acl <your-access-acl-number>
    authorization-attribute user-role network-admin


**Please consult your device documentation for specific configurations.** *Make sure you adhere to your company's
security policy and secure API access as needed.*

.. note::

    Detailed device configuration information can be found in the HPE **"Configurations Fundamentals Guide"**
    for your specific switch, in the *"Configuring RESTful access"* section.


Notes On Functionality
----------------------

- Some older devices only return PoE info for ports with active PoE power drawn.
  Other interfaces will show as 'n/s' (not supported), even though they may support PoE.
- Interface descriptions can be set, but NOT cleared at this time.
- OpenL2M only supports https connections, not plain http!

OpenL2M Configuration
---------------------

From the top-right Admin menu, go to Administration, and then click on Switches, or click the "+ Add" option

Configure the name to show in the menu (does not need to be the switch hostname),
and add a description if so desired.

Add the IP v4 address or resolvable DNS name used to connect to the device.


**In the Connection Configuration section, set:**


**Connector Type:** to

* **HPE Comware REST**: for HPE Comware devices supported via the REST protocol. Also set the proper Credentials Profile!


**SNMP Profile:** this is a don't care field for the HPE Comware NetConf driver.


**Credentials Profile:**

Select the proper profile that stores the API credentials. Note that these same credentials are used for any Commands applied to this device.
Make sure you do not verify SSL/SSH if your device has a self-signed certificate.


**Group Membership section:**

For this device to be visible to users (including Admin) in their menu, you need to add it to at least one Group!


Optional Settings
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
