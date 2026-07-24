.. image:: ../_static/openl2m_logo.png

=====================
Adding Napalm Devices
=====================

We provide a Read-Only Napalm driver. This supports many Napalm device. This driver is NOT well tested, and only for experimental use.

Prerequisites
-------------

* Create a Credential Profile with the proper Napalm SSH username / password that will be used to read this device.


Napalm Configuration
--------------------

Napalm drivers use mostly SSH. Please read the Napalm documentation for additional configuration documentation.

Connection Configuration
------------------------

**Connector Type:** set to **Napalm**

**SNMP Profile:**: this is a don't care field.

**Credentials Profile:** Select the proper profile that stores the Napalm credentials.


The remainder of options are decribed in the generic device-add page.

.. note::

    Do not forget to click SAVE !
