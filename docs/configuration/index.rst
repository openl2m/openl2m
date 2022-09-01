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

Here is the order in which you should create the configuration items:

.. toctree::
   :maxdepth: 1

   Create SNMP profiles <snmp_profiles.rst>
   Create Credential profiles <credential_profiles.rst>
   Create VLANs <vlans.rst>
   Add SNMP Switches <snmp_switches.rst>
   Add Aruba AOS-CX Switches <aos_cx_switches.rst>
   Add Junos Switches <junos_switches.rst>
   Create Switch Groups to add switches to <switchgroups.rst>
   Create Users and give them access to Switch Groups <users.rst>
   Create Commands and Command Lists (optional) <commands.rst>
   Create Command Templates (optional) <cmd_templates.rst>

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
