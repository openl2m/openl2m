.. image:: ../_static/openl2m_logo.png

=======
Backups
=======

**Backing up the OpenL2M database**

Here is one way you can backup the database.
Note this does NOT backup the log objects!:

.. code-block:: bash

  pg_dump -W -U openl2m -h localhost --exclude-table-data=switches_log openl2m > openl2m.sql

**Restore your backup file**

.. code-block:: bash

  # sudo -u postgres psql openl2m < openl2m.sql

**Automating backups**

For automatic backups, you need to create some user cron file. First, create a file ~/.pgpass in the user's home directory, and enter your password data:

.. code-block:: bash

  vi ~/.pgpass

Now enter the following lines, and replace the database password:

.. code-block:: bash

  # format used by pgdump is
  # hostname:port:database:username:password
  #
  *:*:openl2m:openl2m:<password>

Next set this to be accesible only by the user that will run the cron job:

.. code-block:: bash

  chmod 600 ~/.pgpass

And finally, create a shell script that will create a backup file. Note that this
example create a backup without the log files, and adds a datastamp to the backup filename.

.. code-block:: bash

  mkdir /opt/openl2m/backups
  vi backup.sh

and add this:

.. code-block:: bash

  # backup OpenL2M database

  DATETIME=`date +%F-%T`
  FILE=/opt/openl2m/backups/openl2m_no_log.$DATETIME.sql

  #here we go:
  pg_dump -U openl2m -h localhost --exclude-table-data=switches_log openl2m > $FILE


Finally, make this backup.sh executable and add to your cron jobs (this is left to the reader!)


**Start Fresh with a new database**

**DANGEROUS - This will DELETE ALL YOUR DATA!!!**

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
