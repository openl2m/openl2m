.. image:: ../_static/openl2m_logo.png

==============================
Adding Aruba AOS-S API Devices
==============================

This documents how to add devices using the Aruba AOS-S switches REST API.

This has been tested on a single 2930M (non-PoE), single 2930F-PoE and a single 2940-PoE, using firmware v16.11.0029, and REST api v4.

Prerequisites
-------------

* Create a Credential Profile with the proper username / password that will be used to access
  this device via the REST API.
* As needed, create Commands and Command Groups to assign to this device.

Device Configuration
--------------------

Aruaba AOS-S devices using this driver are managed via the REST protocol.
You will need to configure the device to allow this access. Something like the below example is needed,
depending on your specific AOS-S device:

You need to enable the web management interface, in SSL / HTTPS mode, with a valid certificate
See more at https://arubanetworking.hpe.com/techdocs/AOS-S/16.11/ASG/YC/content/common%20files/sel-sig-cer.htm


.. code-block:: bash

    crypto pki enroll-self-signed certificate-name LOCAL_SSL_CERT subject common-name <your-switch-name.yourdomain.com>
    web-management ssl
    no web-management plaintext
    rest-interface

    # add local user for api:
    aaa authentication local-user <api-user> group Level-15 password plaintext  # hit CR and enter password.
    # or use this to create a local admin account
    password manager user-name <api-user> plaintext <api-password>

    # if you use IP access control, you may need something like this:
    ip authorized-managers <openl2m-server-ip> 255.255.255.255 access manager access-method web


**Please consult your device documentation for specific configurations.** *Make sure you adhere to your company's
security policy and secure API access as needed.*

.. note::

    Detailed device configuration information can be found in the Aruba
    **"HPE Aruba Networking REST API for AOS-S Switch 16.11"**
    for your specific switch. At time of writing, see
    https://arubanetworking.hpe.com/techdocs/AOS-Switch/16.11/Aruba%20REST%20API%20for%20AOS-S%2016.11.pdf

    Some additional information for account configuration is here:
    https://arubanetworking.hpe.com/techdocs/AOS-S/16.10/RESTAPI/content/rest%20api/set-up-aaa-res.htm


Notes On Functionality
----------------------

- REST functionality requires that "Web management SSL" is enabled to process the REST requests.
- **OpenL2M only supports https connections, not plain http!**
- REST interface is not supported in FIPS mode.
- REST Interface is not supported on ArubaOS 3800 stack switches.


Connection Configuration
------------------------

**Connector Type:** set to **Aruba AOS-S REST** for Aruba AOS-S devices supported via the REST protocol.

**SNMP Profile:** this is a don't care field.

**Credentials Profile:** Select the proper profile that stores the API credentials.
Note that these same credentials are used for any Commands applied to this device.
Make sure you do not verify SSL/SSH if your device has a self-signed certificate.


The remainder of options are decribed in the generic device-add page.

.. note::

    Do not forget to click SAVE !
