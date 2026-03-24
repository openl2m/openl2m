.. image:: _static/openl2m_logo.png

Features Supported
==================

**Features Supported by Drivers**

**SNMP DEVICES**
----------------

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

   * - Procurve/AOS-S (snmp)
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


**Other API's**
---------------

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

   * - Aruba AOS-S (api r/o) :sup:`1`
     - Yes
     - Yes
     - NO
     - Yes
     - No
     - Yes
     - Yes
     - Yes
     - Yes
     - n/a

   * - HPE Comware (api)  :sup:`2`
     - Yes
     - Yes
     - Yes :sup:`2`
     - Yes :sup:`2`
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes

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
     - Yes

   * - SSH :sup:`4`
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

   * - Napalm (r/o) :sup:`5`
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

  :sup:`1` The AOS-S REST api driver requires firmware v16.x. This has been tested on a single 2930M,
  using firmware v16.11.x, and REST api v4. It is currently Read-Only.
  Due to lack of test hardware, PoE support has not been implemented.

  :sup:`2` The Comware REST API is in development. Most features are supported.

  - Some older devices only return PoE info for ports with active PoE power drawn.
    Other interfaces will show as 'n/s' (not supported), even though they may support PoE.
  - Interface descriptions can be set, but NOT cleared at this time.

  :sup:`3` The Junos PyEZ driver expects a **device with "ELS" software**, ie running Enhanced Layer2 Software,
  that unifies the configuration of Ethernet interfaces access the product line. **Many MX routers do
  not support this, and have not been tested!**

  :sup:`4` SSH support is via the Netmiko library. Most devices supported by that library should work, but
  your mileage may vary!

  :sup:`5` Napalm support has been tested on a limited set of devices. Your mileage may vary!