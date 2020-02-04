.. image:: ../_static/openl2m_logo.png

================
Create the Users
================

**Users**

From Admin, go to Users or click the "+ Add" option
You only need to set a username, and password. You can then add the user
to Switch Groups as needed.

**LDAP Users**

If you configured :doc:`LDAP login <../installation/ldap>`,
users can be auto-created based on an ldap directory.
This allows you to manage users and rights in a central location,
e.g. an active directory domain.

**Automation**

OpenL2M supports the normal Django script interface.
(See https://django-extensions.readthedocs.io/en/latest/runscript.html)
As an example, look in the /scripts directory and check out the example.py script.
