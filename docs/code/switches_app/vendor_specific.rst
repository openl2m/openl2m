.. image:: ../../_static/openl2m_logo.png

==============================
Vendor Specific Customizations
==============================

Supporting a new vendor device
==============================

In openl2m/switches/connect/vendor/, you can create you own vendor subdirectory.
This folder needs to contain a python file that inherits from the main SnmpConnector() class.
Suggested name is *snmp.py*  Call the class SnmpConnector*VendorName*

Override whatever function are needed (see the samples in vendor/cisco, vendor/procurve and vendor/comware)
Then add your code as follows:

* add it to the connect/connect.py includes. E.g.:

.. code-block:: bash

    from switches.connect.vendors.procurve.constants import *
    from switches.connect.vendors.procurve.snmp import SnmpConnectorProcurve

* in the get_connection_object() function in the same connect/connect.py,
  add code to call the new vendor class when that vendor is detected. E.g.:

.. code-block:: bash

    if enterprise == ENTERPRISE_ID_HP:
      return SnmpConnectorProcurve(request, group, switch)


**Customizing the Information tab**


In your vendor implementation, you can add custom data to the Information tab by implementing
the *_get_vendor_data()* method in your class. Collect your data, then call
"add_vendor_data(category_name, item_name, item_value)" to add data. You can read whatever
specific MIB counters you like, or any other data you can get your hands on via e.g. SSH/Netmiko

Here is a hard-coded example. See *vendor/procurve* and *vendor/comware* for additional examples:

.. code-block:: bash

  def _get_vendor_data(self):
      """
      Implement vendor-specific data, add whatever you want here.
      This shows in the "Information" tab
      """
      self.add_vendor_data('Cat 1', 'Item 1', "some data")
      self.add_vendor_data('Cat 1', 'CPU Temp', "75.4 C")
      self.add_vendor_data('Cat 1', 'Fan Speed', "1400rpm")
      self.add_vendor_data('Memory Stats', 'Item 1', "some data")
      self.add_vendor_data('Memory Stats', 'CPU Temp', "75.4 C")
      self.add_vendor_data('Memory Stats', 'Fan Speed', "1400rpm")
