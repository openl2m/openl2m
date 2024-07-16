.. image:: ../_static/openl2m_logo.png

==================
Submitting Tickets
==================

To submit a ticket for an unsupported device, or feature request, please follow these steps.

* **For Unsupported Devices**

If the device is an SNMP manageable device, please provide the output of a
numeric snmp walk, starting at "ISO" aka ".1" You can use a command-line similar to below:

.. code-block:: bash

    snmpwalk -On -c <your_community> <switch_ip> .1 > snmp-data.txt

If your device uses SNMP v3, please adjust your snmpwalk command accordingly.

Once you have this file, please upload this as part of the github.com ticket or "issue".

* **For Bugs or Feature Requests**

Please submit as much details about the device, including vendor and model, screenshots of errors,
error log entries, etc. in the 'issue' on github.com

If the device is not explicity on the list of :doc:`supported devices<../devices>`,
see the above about unsupported devices.
