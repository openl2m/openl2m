.. image:: ../_static/openl2m_logo.png

==============================
Adding HPE Comware API Devices
==============================

This documents how to add devices using the HPE Comware REST API.

Prerequisites
-------------

* Create a Credential Profile with the proper username / password that will be used to access this
  device via the REST API.
* As needed, create Commands and Command Groups to assign to this device.

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


Connection Configuration
------------------------

**Connector Type:** set to **HPE Comware REST** for HPE Comware devices supported via the REST protocol.

**SNMP Profile:** this is a don't care field for the HPE Comware NetConf driver.

**Credentials Profile:** Select the proper profile that stores the API credentials.
Note that these same credentials are used for any Commands applied to this device.
Make sure you do not verify SSL/SSH if your device has a self-signed certificate.


The remainder of options are decribed in the generic device-add page.

.. note::

    Do not forget to click SAVE !
