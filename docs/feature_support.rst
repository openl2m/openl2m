.. image:: _static/openl2m_logo.png

Features Supported
==================

**Features Supported by Drivers**

.. list-table::
   :header-rows: 1
   :stub-columns: 1

   * - Features
     - SNMP (Generic)
     - Arista (Snmp)
     - Aruba AOS-CX (Snmp)
     - Comware (Snmp)
     - Procurve (Snmp)
     - Juniper (Snmp) *
     - Aruba AOS-CX (API)
     - Junos (PyEZ) *
     - Napalm
     - SSH

   * - Port Up/Down
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     -
     - Yes
     - Yes
     -
     -

   * - Port VLAN Change
     - Yes
     - Yes
     - Yes (>= v10.12, access ports)
     - Yes
     - Yes
     -
     - Yes
     - Yes
     -
     -

   * - PoE Up/Down
     - Yes
     -
     - Yes
     - Yes
     - Yes
     -
     - Yes
     - Yes
     -
     -

   * - Description Edit
     - Yes
     - Yes
     - Yes (>= v10.09)
     - Yes
     - Yes
     -
     - Yes
     - Yes
     -
     -

   * - Ethernet/ARP/LLDP Info
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     -

   * - VLAN Edit/Create
     - Yes
     -
     - Yes (>= v10.12, no name)
     - Yes
     - Yes
     -
     - Yes
     - Yes
     -
     -

   * - SSH Commands
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes

   * - VRF Info
     - Yes
     - Partial
     - (untested)
     - Yes
     - (untested)
     - Yes
     - No
     - No
     - No
     - n/a

.. note::

  All driver features are automatically supported by the REST API! (except for SSH commands)


.. note::

  Juniper's SNMP implementation is Read-Only!

.. note::

  The Junos PyEZ driver expects a **device with "ELS" software**, ie running Enhanced Layer2 Software,
  that unifies the configuration of Ethernet interfaces access the product line. **Many MX routers do
  not support this, and have not been tested!**
