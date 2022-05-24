.. image:: ../_static/openl2m_logo.png

=============
Configuration
=============

All OpenL2M configuration has to be performed from an account marked as 'Admin'.
Initially, this will be the admin account created during install.

After login, go to the top right menu under the username, and choose the "Admin" option to get
into the Django admin interface.

Here is the order in which you should create the configuration items:

.. toctree::
   :maxdepth: 1

   Create SNMP and Credential profiles <profiles.rst>
   Create VLANs <vlans.rst>
   Create Commands and Command Lists (optional) <commands.rst>
   Create Command Templates (optional) <cmd_templates.rst>
   Add Switches <switches.rst>
   Create Switch Groups to add switches to <switchgroups.rst>
   Create Users and give them access to Switch Groups <users.rst>

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
