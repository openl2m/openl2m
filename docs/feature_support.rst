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
     - Trunk Edit
     - PoE
     - Descr.
     - Neighbor Info
     - VLAN Edit
     - SSH
     - VRF
     - IPv6 Info

   * - SNMP (Generic) :sup:`1`
     - Yes
     - Yes
     - NO
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes

   * - Arista (SNMP) :sup:`2`
     - Yes
     - Yes
     - NO
     - untested
     - Yes
     - Yes
     -
     - Yes
     - Yes
     - Yes

   * - Aruba AOS-CX (SNMP) :sup:`3`
     - Yes
     - Yes
     - NO
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
     - NO
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
     - NO
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - untested
     - untested

   * - Juniper (SNMP R/O) :sup:`4`
     -
     -
     - (r/o)
     - (r/o)
     - (r/o)
     - Yes
     -
     - Yes
     - Yes
     - Yes

   * - MikroTik (SNMP)  :sup:`5`
     - Yes
     -
     - NO
     - R/O
     - Yes
     -
     -
     - untested
     -
     - untested

   * - Arista eAPI
     - Yes
     - Yes
     - Yes
     - NO
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
     - Yes
     - TBD

   * - Junos (PyEZ)  :sup:`6`
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

   * - SSH :sup:`7`
     -
     -
     -
     -
     -
     -
     -
     - Yes
     - n/a
     - n/a

   * - Napalm (R/O) :sup:`8`
     -
     -
     - (r/o)
     -
     - (r/o)
     - Yes
     -
     - Yes
     - Yes
     - No

.. note::

  All driver features are automatically supported by the OpenL2M REST API! (except for SSH commands)

  *untested* means the feature likely works, but is (clearly) untested.

  :sup:`1` The generic SNMP driver supports standard MIBs only! PoE may not function for 'standard' devices,
  as many vendors provide incorrect mapping of PoE switch-ports ID to interface index in their MIBs.

  :sup:`2` Arista PoE support is untested, as no PoE-capable devices are available to develop and test.

  :sup:`3` AOS-CX SNMP minimal versions:
  VLAN edit/change - v10.12 (no name supported), Description edit - v10.09

  :sup:`4` Juniper's SNMP implementation on devices is Read-Only!

  :sup:`5` The MikroTik driver has limited functionality. MikroTik does not support VLANs over SNMP.
  This driver has only been tested on a single HexS (RB760iGS) device.

  :sup:`6` The Junos PyEZ driver expects a **device with "ELS" software**, ie running Enhanced Layer2 Software,
  that unifies the configuration of Ethernet interfaces access the product line. **Many MX routers do
  not support this, and have not been tested!**

  :sup:`7` SSH support is via the Netmiko library. Most devices supported by that library should work, but
  your mileage may vary!

  :sup:`8` Napalm support has been tested on a limited set of devices. Your mileage may vary!
