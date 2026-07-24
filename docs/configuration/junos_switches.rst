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

.. note::

    The Junos PyEZ driver expects a **device with "ELS" software**, ie running Enhanced Layer2 Software,
    that unifies the configuration of Ethernet interfaces access the product line. **Many MX routers do
    not support this, and have not been tested!**


Connection Configuration
------------------------

**Connector Type:** set to **Junos PyEZ** for Junos ELS devices that have Netconf enabled.

**SNMP Profile:**: this is a don't care field.

**Credentials Profile:** Select the proper profile that stores the NetConf credentials.
Note these credentials are also used to allow 'show/display' commands!


The remainder of options are decribed in the generic device-add page.

.. note::

    Do not forget to click SAVE !
