.. image:: ../_static/openl2m_logo.png

==============================
Adding Aruba AOS-S API Devices
==============================

This documents how to add devices using the Aruba AOS-S switches REST API.

This has been tested on a single 2930M, using firmware v16.11.x, and REST api v4. Due to lack of test hardware,
PoE support has not been implemented.

Prerequisites
-------------

Create a Credential Profile with the proper username / password that will be used to access this device via the REST API.
As needed, create Commands and Command Groups to assign to this device.

.. note::

    These credentials will also be used for running SSH commands, and for saving the current configuration to startup config.


Switch Configuration
--------------------

Aruaba AOS-S devices using this driver are managed via the REST protocol.
You will need to configure the device to allow this access. Something like the below example is needed,
depending on your specific AOS-S device:

You need to enable the web management interface, in SSL / HTTPS mode, with a valid certificate
See more at https://arubanetworking.hpe.com/techdocs/AOS-S/16.11/ASG/YC/content/common%20files/sel-sig-cer.htm


.. code-block:: bash

    crypto pki enroll-self-signed certificate-name LOCAL_SSL_CERT subject common-name your-switch-name.yourdomain.com
    web-management ssl
    no web-management plaintext
    rest-interface

    # add local user for api:
    aaa authentication local-user <api-user> group Level-15 password plaintext  # hit CR and enter password.

    # if you use IP access control, you may need something like this:
    ip authorized-managers <openl2m-server-ip> 255.255.255.255 access manager access-method web


**Please consult your device documentation for specific configurations.** *Make sure you adhere to your company's
security policy and secure API access as needed.*

.. note::

    Detailed device configuration information can be found in the Aruba
    **"HPE Aruba Networking REST API for AOS-S Switch 16.11"**
    for your specific switch. At time of writing, see
    https://arubanetworking.hpe.com/techdocs/AOS-Switch/16.11/Aruba%20REST%20API%20for%20AOS-S%2016.11.pdf


Notes On Functionality
----------------------

- REST functionality requires that "Web management SSL" is enabled to process the REST requests.
- **OpenL2M only supports https connections, not plain http!**
- REST interface is not supported in FIPS mode.
- REST Interface is not supported on ArubaOS 3800 stack switches.


OpenL2M Configuration
---------------------

From the top-right Admin menu, go to Administration, and then click on Switches, or click the "+ Add" option

Configure the name to show in the menu (does not need to be the switch hostname),
and add a description if so desired.

Add the IP v4 address or resolvable DNS name used to connect to the device.


**In the Connection Configuration section, set:**


**Connector Type:** to

* **Aruba AOS-S REST**: for Aruba AOS-S devices supported via the REST protocol. Also set the proper Credentials Profile!


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
