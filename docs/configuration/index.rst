.. image:: ../_static/openl2m_logo.png

=============
Configuration
=============

All OpenL2M configuration has to be performed from an account marked as 'Admin'.
Initially, this will be the admin account created during install.

After login, go to the top right menu under the username, and choose the "Admin" option to get
into the Django admin interface.

OpenL2M uses a Profile concept. A profile is a number of configuration settings that are related to each other.
Once you have created one or more of the profiles below, they can be applied to devices as needed.

Getting Started
---------------

To get started with your first device, you will need to add at minimum the following:

* create a **SNMP Profile** first, if using SNMP managed devices.
* next, create a **Credential Profile**, if using REST driver devices, or if you want to run SSH commands.
* then create **VLANs** and look at using **Vlan Groups**.
* create at least one **Switch Group**.
* finally, add a device, aka a **Switch**, using the above entries.

As Admin, you will have access to all devices added. For more granular access for users, see below.


Detailed Configuration
----------------------

Here are more details about each configuration step, in the order in which you should create the configuration items:

.. toctree::
   :maxdepth: 1

   Create SNMP profiles<snmp_profiles.rst>
   Create Credential profiles<credential_profiles.rst>
   Create VLANs<vlans.rst>
   Create Switch Groups to add devices<switchgroups.rst>
   Adding Devices<switch_configs.rst>
   Add SNMP devices<snmp_switches.rst>
   Add Arista eAPI devices<arista-eapi.rst>
   Add Aruba AOS-CX devices<aos_cx_switches.rst>
   Add Aruba AOS-S devices<aruba_aoss_api.rst>
   Add HPE Comware API devices<hpe_comware_api.rst>
   Add Junos devices<junos_switches.rst>
   Napalm devices<napalm_devices.rst>
   Create Users and give them access to Switch Groups<users.rst>
   Create Commands and Command Lists (optional)<commands.rst>
   Create Command Templates (optional)<cmd_templates.rst>

Permissions
-----------

To understand permissions, please read:

.. toctree::
   :maxdepth: 1

   Understanding Permissions <permissions.rst>

Other Topics
------------

These are some other useful topics:

.. toctree::
   :maxdepth: 1

   Importing Switches, etc. <importing.rst>
   Writing custom scripts <scripts.rst>
   Debugging <debugging.rst>
   Sample SNMP Configurations <snmp_configs.rst>
