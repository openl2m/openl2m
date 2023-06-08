.. image:: _static/openl2m_logo.png

:doc:`Back to user documentation' <using/index>`

====
FAQs
====

Frequenty Asked Questions
=========================

* **Why does it take a while to show the switch page?**

This is a design decision. **Everything is read in real-time from the switch as
you access it**. I.e. Every time you go (back) to a switch, it needs to
re-learn the switch information from SNMP data. That makes it somewhat
slower, but it also means **you always have the current information.**
The Ethernet/LLDP tables are updated as you refresh, which should help
with finding devices that were just connected (instead of some other tools,
which only polls that data every so often, and thus have delays.)

* **Do you support SNMP v1?**

No, SNMP v1 is an out-dated version, and does not support GetBulk calls.
GetBulk significantly improves performance, and is extensively used in OpenL2M.
(Note that GetBulk is not the same as an 'snmpwalk')

* **Do you support IP v6?**

Not at this time, as we have no real test environment.

* **What devices are supported and tested?**

Please see :doc:`this document <switches>`

* **I get an error "502 Bad Gateway", how do I fix this?**

There is a timeout somewhere, either in Nginx or in the Gunicorn Python
process. Please see :doc:`the installation documents <installation/nginx>`
on how to fix this.

* **My HP switch does not ask to save changes?**

HP Procurve/Aruba switches do an automatic save after every SNMP set() call. This is unlike CLI access,
where (some) switches require an explicit save (write mem).

For more see http://www.circitor.fr/Mibs/Html/H/HP-SWITCH-BASIC-CONFIG-MIB.php#hpSwitchImplicitConfigSave

* **My Cisco switch does not show MAC address info using SNMP v3?**

Cisco switches use the SNMP v3 Context field to "separate" data per vlan.
Your switch needs to support the "show snmp context" command, and should show something similar to::

  #show snmp context
  vlan-1
  vlan-2
  vlan-11
  vlan-12
  ...
  vlan-1002
  vlan-1003
  vlan-1004
  vlan-1005

If this looks OK, you need to issue the following command to get your snmp v3 user access to all contexts:

.. code-block:: bash

  snmp-server group <your_v3_group> v3 auth context vlan- match prefix

* **How can I import my switches from <name your NMS here>?**

The Django python API is fully supported. You can write a custom stand-alone import script using whatever NMS API
you have to read your device data and import into OpenL2M. See the ./scripts/example.py file for more details.

* **How do I debug OpenL2M?**

This is described in :doc:`Debugging <configuration/debugging>`

* **How do I configure my Cisco switch for Syslog messages over SNMP?**

Regular Cisco IOS devices need a configuration similar to the one below, which allows for the 50 most recent
syslog entries of "Informational" level and below to be available over SNMP. Note this can impact memory usage
of the device. Please refer to your particular device documentation for more specifics.

.. code-block:: bash

  logging history size 50
  logging history informational

