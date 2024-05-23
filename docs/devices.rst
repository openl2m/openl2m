.. image:: _static/openl2m_logo.png

=================
Supported Devices
=================

**Switches Tested**

The following devices (in alphabetical order), are supported by OpenL2M. While an attempt has been made to verify all functionality,
we strongly encourage you to test your devices before using them "in production" with OpenL2M.

For SNMP supported device, an attempt has been made to make OpenL2M adhere to 'standard' SNMP.
However, we recognize there is no such thing as completely 'standard' SNMP.


We have tested OpenL2M on the following hardware, with the listed limitations.

**Cisco**

* *Catalyst 2960* series; single and stacked units.
* *Catalyst 4500-E* series, with Sup6L-E and Sup7L-E.

**HP/Aruba (ProCurve/ArubaOS)**

* *HP 2520* series; single units.
* *HP 2530* series; single units.
* *HP 2540* series; single units.
* *HP 2810* series, single units.
* *HP 4200* series, specifically 4204vl (J8770A).
* *Aruba 2930F/M* series; single units.
* *Aruba 5400* series; chassis based, regular, zl, and zl2.

**Aruba AOS-CX**

* *Aruba CX 6000* series; single units. (R/W support via the REST API v10.08)
* *Aruba CX 6100* series; single units. (R/W support via the REST API v10.08)
* *Aruba CX 6300* series; single units. (R/W support via the REST API v10.08)

**HP Enterprise (HPE)**

* *HPE 1950* series switches, running Comware 7; single and IRF-stacked units.
* HPE J3400CL-24G (J4905A)
* *HPE 5130* series switches, running Comware 7; single and IRF-Stacked units.
* *HPE 5140* series switches, running Comware 7; single and IRF-Stacked units.
* *HPE 5500* series switches, running Comware 5; single units.
* *HPE 5510* series switches, running Comware 7; single units.
* *HPE 5900AF* series switches, running Comware 7; single and IRF-Stacked units.
* *HPE 5930* series switches, running Comware 7; single and IRF-Stacked units.
* *HPE 5940* series switches, running Comware 7; single and IRF-Stacked units.
* *HPE 5945* series switches, running Comware 7; single and IRF-Stacked units.
* *HPE 5950* series switches, running Comware 7; single and IRF-Stacked units.

**Juniper Networks**

Full with Junos PyEZ, R/O support with SNMP.

* *EX2300* series switch, running JUNOS 18.2R3-S2.9; single unit.
* *QFX5120* series switch, running JUNOS 20.4R3-S3.4; single unit.
* *SRX* series firewalls, with "Commands-Only" configurations to run command-templates.

**Generic**

Several generic snmp implementations on 'home wireless routers' and 'commodity' switches have been tested,
with varying results, depending on the level of SNMP support in the devices.

**Napalm devices**

Any device supported by the python Napalm library, in read-only mode. Note this was implemented primarily as
an example of the Connector() API. See source code for more.

**SSH/Command-Only devices**

Any device supported by the python Netmiko library. Devices configured as such do NOT poll interfaces, but only allow
for commands to be executed on the device.
