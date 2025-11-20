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

   * - Arista (SNMP)
     - Yes
     - Yes
     -
     - Yes
     - Yes
     -
     - Yes
     - Yes
     - Yes

   * - Aruba AOS-CX (SNMP)
     - Yes
     - Yes  (>= v10.12, access ports)
     - Yes
     - Yes (>=v10.09)
     - Yes
     - Yes (>=v10.12, no name)
     - Yes
     - Yes (untested)
     - Yes

   * - Comware (SNMP)
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes

   * - Procurve (SNMP)
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes (untested)
     - ?

   * - Juniper (SNMP) :sup:`1`
     -
     -
     - (r/o)
     - (r/o)
     - Yes
     -
     - Yes
     - Yes
     - Yes

   * - SNMP (Generic) :sup:`2`
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

   * - Junos (PyEZ)  :sup:`3`
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes

   * - MikroTik (SNMP)  :sup:`4`
     - Yes
     -
     - Read-Only
     - Yes
     -
     -
     - untested
     -
     - untested

   * - Napalm (R/O) :sup:`5`
     -
     -
     -
     - (r/o)
     - Yes
     -
     - Yes
     - Yes
     - No

   * - SSH :sup:`6`
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

  :sup:`1` Juniper's SNMP implementation is Read-Only!

  :sup:`2` The generic SNMP driver supports standard MIBs only!

  :sup:`3` The Junos PyEZ driver expects a **device with "ELS" software**, ie running Enhanced Layer2 Software,
  that unifies the configuration of Ethernet interfaces access the product line. **Many MX routers do
  not support this, and have not been tested!**

  :sup:`4` The MikroTik driver has limited functionality. MikroTik does not support VLANs over SNMP.
  This driver has only been tested on a single HexS (RB760iGS) device.

  :sup:`5` Napalm support has been tested on a limited set of devices. You mileage may vary!

  :sup:`6` SSH support is via the Netmiko library. Most devices supported by that library should work, but
  your mileage may vary!