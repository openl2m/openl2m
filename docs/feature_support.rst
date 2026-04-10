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
     - Yes :sup:`1`
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

   * - Cisco (snmp) :sup:`4`
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - NO
     - NO
     - Yes
     - Yes

   * - Cisco-SB (snmp) :sup:`5`
     - Yes
     - Yes
     - NO
     - Yes
     - Yes
     - Yes
     - NO
     - NO
     - Yes
     - Yes

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
     - Yes
     - Yes
     - untested

   * - Juniper (snmp r/o) :sup:`6`
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

   * - MikroTik (snmp) :sup:`6`
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

  Editing 802.1q tagged interfaces (aka trunk ports by some vendors) is performed using the standard Q-Bridge MIB.
  We set the "dot1qpvid" entry for the untagged interface, and modify using the "dot1qVlanStaticEgressPorts" VLAN
  port membership bitmap to add or remove tagged interfaces. This is currently only tested in Procurve and
  Aruba AOS-S switches.

  :sup:`2` Arista PoE support is untested, as no PoE-capable devices are available to develop and test.

  :sup:`3` AOS-CX SNMP minimal versions:
  VLAN edit/change - v10.12 (no name supported), Description edit - v10.09

  :sup:`4` The Cisco SNMP implementation should support most 'regular' Catalyst style switches. This has been
  tested on Catalyst-2960 and Catalyst-4500 series devices.

  :sup:`5` Cisco Small Business devices are tested on a single CBS350 (non-PoE) switch.
  All features (except for PoE) are supported.

  :sup:`6` Juniper's SNMP implementation on devices is Read-Only!

  :sup:`7` The MikroTik driver has limited functionality. MikroTik does not support VLANs over SNMP.
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

   * - Aruba AOS-S (api) :sup:`1`
     - Yes
     - Yes
     - Yes
     - Yes
     - No
     - Yes
     - Yes
     - Yes
     - Yes
     - n/a

   * - HPE Comware (api) :sup:`2`
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

   * - Junos (PyEZ) :sup:`3`
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


  :sup:`1` The AOS-S REST api driver requires firmware v16.x. This has been tested using firmware v16.11.0029, and REST api v4,
  on the following single devices: 2530(PoE), 2940(PoE), 2930M, and 2930F(PoE). It should function on the 2530, 2540, 2920,
  2930F, 2930M, 3810 and 5400R line of devices with the proper software levels.


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