.. image:: ../_static/openl2m_logo.png

====================
Adding SNMP switches
====================

Prerequisites
-------------

Create an SNMP Profile with the proper SNMP configuration as used on this device.
You will need to create the proper SNMP Read/Write configuration
to allow OpenL2M to work on supported devices.
:doc:`Please see the section with SNMP examples for more details.<snmp_configs>`
(All SNMP devices are managed via SNMP using the Python EasySNMP and pysnmp library.)

Please refer to your device snmp documentation for more details.

Connection Configuration
------------------------

**Connector Type**: set to **SNMP**


**SNMP Profile**: Select the proper SNMP profile to use on this device.

**Credentials Profile**: If applicable, set the proper profile that will be used
to run commands on this device. *If you want to allow 'show/display' commands, you need to add a profile here!*

The remainder of options are decribed in the generic device-add page.

.. note::

    Do not forget to click SAVE !
