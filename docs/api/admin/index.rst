.. image:: ../../_static/openl2m_logo.png

======================
The Administrative API
======================

This describes the use of the REST API for Administrative purposes.
This is only available to users with 'SuperUser' rights, and is intended to create
or modify user accounts, and devices (switches).

.. warning::

   The admin API can be used to read and create several types of objects with passwords,
   that due to the nature of their use, will be sent in plain text !

   We urge you to make sure your site uses SSL encryption, per your organizations' policy.


This is a work in progress...

.. toctree::
   :maxdepth: 1
   :caption: Here is what is available at this time:

   endpoints.rst
   api_users.rst
   api_switches.rst
   api_switchgroups.rst
   api_snmp.rst
   api_credentials.rst
