.. image:: _static/openl2m_logo.png

Features Supported
==================

**Features Supported by Drivers**

.. list-table::
   :header-rows: 1
   :stub-columns: 1

   * - Features
     - Up/Down
     - Vlan Set
     - PoE
     - Descr.
     - IPv6
     - Neighbors
     - Vlan Edit
     - Trunk Edit
     - SSH
     - VRF

   * - SNMP :sup:`1`
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - NO
     - Yes
     - Yes

   * - Arista (snmp) :sup:`2`
     - Yes
     - Yes
     - untested
     - Yes
     - Yes
     - Yes
     -
     - NO
     - Yes
     - Yes

   * - Aruba AOS-CX (snmp) :sup:`3`
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - NO
     - Yes
     - untested

   * - HPE Comware (snmp)
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - NO
     - Yes
     - Yes

   * - Procurve (snmp)
     - Yes
     - Yes
     - Yes
     - Yes
     - untested
     - Yes
     - Yes
     - NO
     - Yes
     - untested

   * - Juniper (snmp r/o) :sup:`4`
     -
     -
     - (r/o)
     - (r/o)
     - Yes
     - Yes
     -
     - (r/o)
     - Yes
     - Yes

   * - MikroTik (snmp)  :sup:`5`
     - Yes
     -
     - R/O
     - Yes
     - untested
     -
     -
     - NO
     - untested
     -

   * - Arista eAPI
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

   * - Aruba AOS-CX (api)
     - Yes
     - Yes
     - Yes
     - Yes
     - TBD
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes

   * - HPE Comware (api)  :sup:`6`
     - Yes
     - Yes
     - Yes :sup:`6`
     - Yes :sup:`6`
     - Yes
     - Yes
     - No
     - Yes
     - Yes
     - Yes

   * - Junos (PyEZ)  :sup:`7`
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

   * - SSH :sup:`8`
     -
     -
     -
     -
     - n/a
     -
     -
     -
     - Yes
     - n/a

   * - Napalm (r/o) :sup:`9`
     -
     -
     -
     - (r/o)
     - No
     - Yes
     -
     - (r/o)
     - Yes
     - Yes

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

  :sup:`6` The Comware REST API is in development. Most features are supported.

  - Some older devices only return PoE info for ports with active PoE power drawn.
    Other interfaces will show as 'n/s' (not supported), even though they may support PoE.
  - Interface descriptions can be set, but NOT cleared at this time.

  :sup:`7` The Junos PyEZ driver expects a **device with "ELS" software**, ie running Enhanced Layer2 Software,
  that unifies the configuration of Ethernet interfaces access the product line. **Many MX routers do
  not support this, and have not been tested!**

  :sup:`8` SSH support is via the Netmiko library. Most devices supported by that library should work, but
  your mileage may vary!

  :sup:`9` Napalm support has been tested on a limited set of devices. Your mileage may vary!
