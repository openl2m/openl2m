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

   * - Arista eAPI (R/O)
     -
     -
     -
     -
     - Yes
     -
     - Yes
     - Yes
     - Yes

   * - Aruba AOS-CX (SNMP) :sup:`1`
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - untested
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
     - untested
     - untested

   * - Juniper (SNMP R/O) :sup:`2`
     -
     -
     - (r/o)
     - (r/o)
     - Yes
     -
     - Yes
     - Yes
     - Yes

   * - SNMP (Generic) :sup:`3`
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

   * - Junos (PyEZ)  :sup:`4`
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes

   * - MikroTik (SNMP)  :sup:`5`
     - Yes
     -
     - R/O
     - Yes
     -
     -
     - untested
     -
     - untested

   * - Napalm (R/O) :sup:`6`
     -
     -
     -
     - (r/o)
     - Yes
     -
     - Yes
     - Yes
     - No

   * - SSH :sup:`7`
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

  All driver features are automatically supported by the OpenL2M REST API! (except for SSH commands)

  *untested* means the feature likely works, but is (clearly) untested.

  :sup:`1` AOS-CX SNMP minimal versions:
  VLAN edit/change - v10.12 (no name supported), Description edit - v10.09

  :sup:`2` Juniper's SNMP implementation on devices is Read-Only!

  :sup:`3` The generic SNMP driver supports standard MIBs only!

  :sup:`4` The Junos PyEZ driver expects a **device with "ELS" software**, ie running Enhanced Layer2 Software,
  that unifies the configuration of Ethernet interfaces access the product line. **Many MX routers do
  not support this, and have not been tested!**

  :sup:`5` The MikroTik driver has limited functionality. MikroTik does not support VLANs over SNMP.
  This driver has only been tested on a single HexS (RB760iGS) device.

  :sup:`6` Napalm support has been tested on a limited set of devices. You mileage may vary!

  :sup:`7` SSH support is via the Netmiko library. Most devices supported by that library should work, but
  your mileage may vary!