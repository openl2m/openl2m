.. image:: ../_static/openl2m_logo.png

===================
Sample SNMP Configs
===================

Below are example SNMP configurations for several switch vendors. Please note these are examples only,
and by no means are the most secure. **You should make sure that you implement SNMP access according to your
organizations' security policies and configuration standards!**

**We recommend v3, as it is most secure.** The below examples of v3 configs use the "AuthPriv" mode, with SHA1/AES128
as the authentication and privacy protocols. Presently, more then AES-128 is NOT supported!

None of the examples use an access-list to protect snmp queries. We strongly recommend you implement that additional measure!

Cisco
=====

There are many "flavors" of Cisco IOS, but something along the lines below may work.
Note that this has not been tested on IOS-XR or Nexus devices.

* Version 3 (recommended!):

.. code-block:: bash

  snmp-server location DEVICE LOCATION
  snmp-server contact YOUR CONTACT INFO
  snmp-server view READ_ALL_VIEW iso included
  snmp-server view WRITE_ALL_VIEW iso included
  snmp-server group WRITE_GROUP v3 auth read READ_ALL_VIEW write WRITE_ALL_VIEW
  # this next one is only needed on routers with VRF's defined:
  snmp-server group WRITE_GROUP v3 auth context vlan- match prefix
  snmp-server user WRITE_USER WRITE_GROUP v3 auth sha AUTH_PASSWORD priv aes 128 PRIV_PASSWORD
  # this last one is not absolutely needed, but keeps logs synched between device reboots
  snmp-server ifindex persist

* Version 2c:

.. code-block:: bash

  snmp-server location DEVICE LOCATION
  snmp-server contact YOUR CONTACT INFO
  snmp-server community V2C_WRITE_COMMUNITY RW
  # this last one is not absolutely needed, but keeps logs synched between device reboots
  snmp-server ifindex persist

Aruba / Procurve
================

* Version 3 (recommended!):

.. code-block:: bash

  snmp-server location "DEVICE LOCATION"
  snmp-server contact "YOUR CONTACT INFO"
  # enabling will create user ‘initial’
  snmpv3 enable
  no snmpv3 user initial
  snmpv3 only
  snmpv3 restricted-access
  snmpv3 user WRITE_USER auth sha AUTH_PASSWORD priv aes PRIV_PASSWORD
  snmpv3 group operatorauth user WRITE_USER sec-model ver3
  snmpv3 group managerpriv user WRITE_USER sec-model ver3

* Version 2c:

.. code-block:: bash

  snmp-server location "DEVICE LOCATION"
  snmp-server contact "YOUR CONTACT INFO"
  snmp-server community "V2C_WRITE_COMMUNITY" Unrestricted

HPE Comware
===========

* Version 3 (recommended!):

.. code-block:: bash

   snmp-agent
   snmp-agent log all
   snmp-agent sys-info version v3
   snmp-agent sys-info location DEVICE LOCATION
   snmp-agent sys-info contact YOUR CONTACT INFO
   snmp-agent mib-view included WRITE_ALL_VIEW iso
   snmp-agent group v3 WRITE_GROUP write-view WRITE_ALL_VIEW
   snmp-agent usm-user v3 WRITE_USER WRITE_GROUP simple authentication-mode sha AUTH_PASSWORD privacy-mode aes128 PRIV_PASSWORD

* Version 2c:

.. code-block:: bash

   snmp-agent
   snmp-agent log all
   snmp-agent sys-info version v2c
   snmp-agent sys-info location DEVICE LOCATION
   snmp-agent sys-info contact YOUR CONTACT INFO
   snmp-agent mib-view included WRITE_ALL_VIEW iso
   snmp-agent community write V2C_WRITE_COMMUNITY mib-view WRITE_ALL_VIEW
