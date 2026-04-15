.. image:: _static/openl2m_logo.png

Features Supported
==================

**Features Supported by Drivers**

Note: All driver features are automatically supported by the OpenL2M client REST API! (except for SSH commands)

*untested* means the feature likely works, but is (clearly) untested.


**SNMP Devices**
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
     - Save Config
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
     - NO
     - Yes
     - Yes

   * - Arista :sup:`2`
     - Yes
     - Yes
     - untested
     - Yes
     - Yes
     - Yes
     - NO
     - NO
     - NO
     - Yes
     - Yes

   * - Aruba AOS-CX :sup:`3`
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
     - untested

   * - Cisco :sup:`4`
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
     - Yes

   * - Cisco-SB :sup:`5`
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
     - Yes

   * - HPE Comware :sup:`6`
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
     - Yes

   * - Procurve/AOS-S :sup:`7`
     - Yes
     - Yes
     - Yes
     - Yes
     - untested
     - Yes
     - Yes
     - Yes
     - Automatic
     - Yes
     - untested

   * - Juniper (r/o) :sup:`8`
     -
     -
     - (r/o)
     - (r/o)
     - Yes
     - Yes
     - (r/o)
     - (r/o)
     - (r/o)
     - Yes
     - Yes

   * - MikroTik :sup:`9`
     - Yes
     -
     - R/O
     - Yes
     - untested
     -
     -
     - NO
     - NO
     - untested
     -

   * - Netgear :sup:`10`
     - Yes
     - Yes
     - Yes
     - Yes
     - untested
     - Yes
     - Yes
     - NO
     - NO
     - untested
     - untested


.. admonition::  SNMP Driver Notes

  :sup:`1` The generic SNMP driver supports standard MIBs only! PoE may not function for 'standard' devices,
  as many vendors provide incorrect mapping of PoE switch-ports ID to interface index in their MIBs. This driver
  can NOT save the config.

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

  :sup:`6` HPE Comware devices are fully supported for all functionality.

  :sup:`7` Aruba AOS-S, and older Procurve switches, do NOT require a 'write mem' after succesful snmp changes.

  :sup:`8` Juniper's SNMP implementation on devices is Read-Only. Therefor we can only read, and not make changes!

  :sup:`9` The MikroTik driver has limited functionality. MikroTik does not support VLANs over SNMP.
  This driver has only been tested on a single HexS (RB760iGS) device.

  :sup:`10` The Netgear driver has limited functionality. Basic features work. Vlan tagging appears non-functional,
  even though the standard snmp calls to the Q-Bridge MIB do not return errors. So this functionality is disabled.


**Other API's**
---------------

Devices supported via REST api's and more...

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
     - Save Config
     - SSH
     - VRF

   * - Arista eAPI :sup:`1`
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
     - Yes

   * - Aruba AOS-CX :sup:`2`
     - Yes
     - Yes
     - Yes
     - Yes
     - TBD
     - Yes
     - Yes
     - Yes
     - NO
     - Yes
     - Yes

   * - Aruba AOS-S :sup:`3`
     - Yes
     - Yes
     - Yes
     - Yes
     - No
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - n/a

   * - HPE Comware :sup:`4`
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
     - Yes

   * - Junos :sup:`5`
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Yes
     - Automatic
     - Yes
     - Yes

   * - SSH :sup:`6`
     -
     -
     -
     -
     - n/a
     -
     -
     -
     - n/a
     - Yes
     - n/a

   * - Napalm (r/o) :sup:`7`
     -
     -
     -
     - (r/o)
     - No
     - Yes
     -
     - (r/o)
     - n/a
     - Yes
     - Yes


.. admonition::  API Driver Notes

  :sup:`1` The Arista eAPI driver does not PoE due to lack of testing hardware. It is tested on 7050 and 7280cr3 hardware.

  :sup:`2` The Aruba AOS-CX REST api driver supports most features, and is tested in 6100 and 6300 hardware.

  :sup:`3` The Aruba AOS-S REST api driver requires firmware v16.x. This has been tested using firmware v16.11.0029, and REST api v4,
  on the following single devices: 2530(PoE), 2940(PoE), 2930M, and 2930F(PoE). It should function on the 2530, 2540, 2920,
  2930F, 2930M, 3810 and 5400R line of devices with the proper software levels.

  :sup:`4` The Comware REST api driver supports all features. Tested on a variety of devices.

  - Some older devices only return PoE info for ports with active PoE power drawn.
    Other interfaces will show as 'n/s' (not supported), even though they may support PoE.
  - Interface descriptions can be set, but NOT cleared at this time.

  :sup:`5` The Junos PyEZ driver expects a **device with "ELS" software**, ie running Enhanced Layer2 Software,
  that unifies the configuration of Ethernet interfaces access the product line. **Many MX routers do
  not support this, and have not been tested!**

  :sup:`6` SSH support is via the Netmiko library. Most devices supported by that library should work, but
  your mileage may vary!

  :sup:`7` Napalm support has been tested on a limited set of devices. It requires SSH access. Your mileage may vary!