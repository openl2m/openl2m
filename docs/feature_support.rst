.. image:: _static/openl2m_logo.png

Features Supported
==================

**Features Supported by Drivers**

.. list-table::
   :header-rows: 1
   :stub-columns: 1

   * - Features
     - SNMP (Generic)
     - Aruba AOS-CX (Snmp)
     - Comware (Snmp)
     - Procurve (Snmp)
     - Juniper (Snmp)
     - Aruba AOS-CX (API)
     - Junos (PyEZ)
     - Napalm
     - SSH

   * - Port Up/Down
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
     -
     - Yes
     - Yes
     - Yes
     -

   * - VLAN Edit/Create
     - Yes
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

.. note::

  All driver features are automatically supported by the REST API! (except for SSH commands)
