.. image:: ../_static/openl2m_logo.png

======================
Updating Ethernet OUIs
======================

**Updating the Ethernet OUI database**

OpenL2M uses the python netaddr package for many of IP and Ethernet parsing and display functionality.
This include the mapping of Ethernet OUI's to the registered vendor. This database as distributed
with the netaddr package is out of date. You can update this with a script in the ./scripts directory.

Run the following after each upgrade:

.. code-block:: bash

  cd /opt/openl2m/scripts
  ./update_oui.sh


This will download new data files from the IEEE website, and update the database files used by
the netaddr package.

You should not need to restart the OpenL2M service after this.

IMPORTANT: this script assumes the default install location of /opt/openl2m. If you have a different install path, please modify this script as needed!


**Automatically update the OUI database**

You should also be able to run this script as a cron job, to automatically update eg. at 6AM on the first of every month:

.. code-block:: bash

    0 6 1 * * /opt/openl2m/scripts/update_oui.sh > /tmp/update_oui.sh.out 2>&1
