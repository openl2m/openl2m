.. image:: ../_static/openl2m_logo.png

==================
Submitting Tickets
==================

To contact the developers, kindly submit a ticket at https://github.com/openl2m/openl2m/issues

.. note::

    We will not entertain support requests for devices that are no longer
    supported by the manufacturer!


**For Unsupported Devices**

If the device is an SNMP manageable device, please provide the following:

* a screenshot of the "Device Information" tab, run from an Administrator account. Specifically,
  we like to see the "Timing Info" column, and the top six entries form the General Information (System) group.

* the output of a numeric snmp walk, starting at "ISO" aka ".1" You can use a command-line similar to below:

.. code-block:: bash

    snmpwalk -On -c <your_community> <switch_ip> .1 > snmp-data.txt

If your device uses SNMP v3, please adjust your snmpwalk command accordingly.

Once you have these screenshots and file, please upload this as part of the github.com ticket or "issue".


**For Bugs or Feature Requests**

* Submit a ticket per bug; i.e. only one bug per ticket, no more!

* Please submit as much details about the bug and the device, including vendor and model, screenshots of errors,
  error log entries, etc. in the 'issue' on github.com

* For errors, include a screenshot of the error page, with the 'Details' expanded.

* For errors, include the data from any related log entries generated (Menu-> Activity Logs, filter by type 'Error')

If the device is not explicity on the list of :doc:`tested devices<../devices>`,
see the above about unsupported devices.
