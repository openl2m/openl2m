.. image:: _static/openl2m_logo.png

=============
What's New...
=============

:doc:`Please read the release notes for more details on each release. <releases/index>`

* v3.3 adds support for Arista devices via SNMP. Also read MPLS VRF info via SNMP on devices
  and interfaces that support it.

* v3.2 adds a Dark theme, and uses the Bootstrap 5.3 framework for improved web accesibility.
  Also adds a basic admin rest api. Device info tab now shows last access and change dates and use counts.

* v3.1 upgrades the Django framework to v5.0 It also adds bug fixes and improved code readability.
  Also adds a docker-compose config for quickly testing OpenL2M in a container.

* v3.0 introduces a REST API. This allows for remotely making changes to devices without needing to know the underlying vendor.
  Read the API section of the documentation for more details.

* v2.4 upgrades the Django framework to v4.2 LTS

* v2.3 adds support for Juniper Junos devices.

* v2.2 adds support for Aruba AOS-CX switches.

* v2.1 implements command templates, a controlled method to give users variable input on commands.
  This gives tremendous flexibility in giving users in a controlled fashion more visibility into the device.
  See the Configuration section for more.

* v2.0 implements a new plug-in API for add-on device drivers.
  This makes is easy to add support for any kind of network device,
  whether the interface is SSH, REST, NetConf, or other methods.
  See more in the development section below.
