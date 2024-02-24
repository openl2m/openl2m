.. image:: ../../../_static/openl2m_logo.png

========================
Implementing New Drivers
========================

Supporting a new vendor device - SNMP
=====================================

**Create Vendor Sub-directory**

In openl2m/switches/connect/snmp/, create a vendor sub-directory.

In this folder you need a __init__.py (copy from somewhere else :-)), and a minimum file called connector.py, and likely constants.py

In connector.py, create your new driver class that inherits from the SnmpConnector() class. Call the class SnmpConnector*VendorName*

Override whatever function are needed (see the samples in vendor/cisco, vendor/procurve and vendor/comware)


**Use The New Driver Class***

Driver classes are loaded from openl2m/switches/connect/connect.py

* Include your driver to connect.py around line 40. E.g.:

.. code-block:: bash

    from switches.connect.snmp.vendors.procurve.constants import *
    from switches.connect.snmp.vendors.procurve.snmp import SnmpConnectorProcurve

* Now reference your drive in the get_connection_object() function  around line 90,
  add code to call the new vendor class when that vendor is detected. E.g.:

.. code-block:: bash

    if enterprise == ENTERPRISE_ID_HP:
      return SnmpConnectorProcurve(request, group, switch)


Supporting a new vendor device - Custom
=======================================

You can also extend OpenL2M for vendors that support their own API's, such as REST. An example of this Aruba AOS-CX
devices. To add a customer driver, follow these steps:

**Add  Connector Type**

in /openl2m/switches/constants, add lines similar to the following to the connector type definition:

.. code-block:: bash

  CONNECTOR_TYPE_AOSCX = 2
  CONNECTOR_TYPE_CHOICES = [
      ..
      [CONNECTOR_TYPE_AOSCX, 'Aruba AOS-CX'],
  ]

After this, you will need to create a new Django "migration" to handle this data field update:

.. code-block:: bash

  python3 manage.py makemigrations


**Create the Custom Driver**

In openl2m/switches/connect/, create a sub-directory representing your connector type. Eg. "aruba_aoscx".
Use all lower case, and underscores only.

In this folder you need a __init__.py (copy from somewhere else :-)),
and a minimum file called connector.py, and likely constants.py

In connector.py, create your new driver class that inherits from the base Connector() class.
Call the class *YourTypeName*Connector()*. Eg. AosCxConnector()

Implement the functions needed to support this device class. At a minimum, you need to create

def get_my_basic_info(self) - loads interfaces, etc.
def get_my_client_data(self) - loads ethernet and lldp neighbor data.


**Call the Customer Driver**

Driver classes are loaded from openl2m/switches/connect/connect.py

* Include your driver to connect.py around line 40. E.g.:

.. code-block:: bash

    from switches.connect.aruba_aoscx.constants import *
    from switches.connect.aruba_aoscx.connector import AosCxConnector

* Now reference your drive in the get_connection_object() function around line 110:

.. code-block:: bash

  elif switch.connector_type == CONNECTOR_TYPE_ARUBA_AOSCX:
    connection = AosCxConnector(request, group, switch)




Customizing the Information Tab
===============================

In your vendor implementation, you can add custom data to the Information tab by implementing
the *_get_vendor_data()* method in your class. Collect your data, then call
"add_vendor_data(category_name, item_name, item_value)" to add data. You can read whatever
specific MIB counters you like, or any other data you can get your hands on via e.g. SSH/Netmiko

Here is a hard-coded example. See *snmp/procurve* and *snmp/comware* for additional examples:

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
