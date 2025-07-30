.. image:: _static/openl2m_logo.png

Features Supported
==================

**Features Supported by Drivers**

.. list-table::
   :header-rows: 1
   :stub-columns: 1

   * - Features
     - Up/Down
     - VLAN Change
     - PoE
     - Descr.
     - Neighbor Info
     - VLAN Edit
     - SSH
     - VRF
     - IPv6 Info

   * - Arista (Snmp)
     - Yes
     - Yes
     -
     - Yes
     - Yes
     -
     - Yes
     - Yes
     - Yes

   * - Aruba AOS-CX (Snmp)
     - Yes
     - Yes  (>= v10.12, access ports)
     - Yes
     - Yes (>=v10.09)
     - Yes
     - Yes (>=v10.12, no name)
     - Yes
     - Yes (untested)
     - Yes

   * - Comware (Snmp)
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes

   * - Procurve (Snmp)
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes (untested)
     - ?

   * - Juniper (Snmp) *
     -
     -
     - (r/o)
     - (r/o)
     - Yes
     -
     - Yes
     - Yes
     - Yes

   * - SNMP (Generic)
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes

   * - Aruba AOS-CX (API)
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - TBD

   * - Junos (PyEZ) *
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes


   * - Napalm (R/O)
     -
     -
     -
     - (r/o)
     - Yes
     -
     - Yes
     - Yes
     - No

   * - SSH
     -
     -
     -
     -
     -
     -
     - Yes
     - n/a
     - n/a

.. note::

  All driver features are automatically supported by the REST API! (except for SSH commands)


.. note::

  Juniper's SNMP implementation is Read-Only!

.. note::

  The Junos PyEZ driver expects a **device with "ELS" software**, ie running Enhanced Layer2 Software,
  that unifies the configuration of Ethernet interfaces access the product line. **Many MX routers do
  not support this, and have not been tested!**
