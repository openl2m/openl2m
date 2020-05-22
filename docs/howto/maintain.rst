.. image:: ../_static/openl2m_logo.png

========
How To's
========

**Backing up the OpenL2M database**

Here is one way you can backup the database.
Note this does NOT backup the log objects!:

.. code-block:: bash

  pg_dump -W -U openl2m -h localhost --exclude-table-data=switches_log openl2m > openl2m.sql

**Restore your backup file**

.. code-block:: bash

  # sudo -u postgres psql openl2m < openl2m.sql

**Start Fresh with a new database**

**DANGEROUS - This will **DELETE ALL YOUR DATA!!!*

.. code-block:: bash

  ##############################
  # Clear-out OpenL2M Database #
  ##############################

  # stop service, so database is not actively used, else the drop below fails!
  systemctl stop openl2m

  # restore the database:
  echo "Drop Database"
  sudo -u postgres psql -c 'drop database openl2m'

  echo "Recreate Database"
  sudo -u postgres psql -c 'create database openl2m'

  #restart the service
  systemctl restart openl2m
