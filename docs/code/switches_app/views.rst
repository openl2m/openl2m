.. image:: ../../_static/openl2m_logo.png

##### The switches app

**views.py**

All URLs are mapped to functions in views.py

In general, all view functions follow these high level steps.

1 - Create the (snmp) connection object:

.. code-block:: bash

  conn = get_connection_object(request, group, switch)


2 - Next, get the basic switch information. This reads Interface, Vlan, and Power-over-Ethernet data::

  conn.get_switch_basic_info()


This information could be cached for the session, if this is the second time something is done on this switch.
E.g. you read the basic layout, then disable an interface, and go back to the main switch page.
That second time around, the cached data will be used.


3 - Then, depending on which view, another function may be called:

If **Ethernet/LLDP** data is requested, we call:

.. code-block:: bash

  conn.get_switch_client_data()

  This calls the following:

    self._get_known_ethernet_addresses()
      This calls  _get_branch_by_name('dot1dTpFdbPort')

    self._get_lldp_data()
      This calls several lldp mib counters.

    self._get_arp_data()
      This calls   _get_branch_by_name('ipNetToMediaPhysAddress')


This data is never cached, so it is always the most recent data from the switch.

Admins have an additional option for some more **Hardware Details** from the switch:

.. code-block:: bash

   conn.get_switch_hardware_details()

   This calls two functions that need to be implemented in vendor-specific snmp classes:
      self._get_vendor_data()

      self._get_syslog_msgs()

    and then it reads the standard Entity MIB hardware info:

      retval = self._get_entity_data()
        This reads a number of entityPhysical MIB entries.
