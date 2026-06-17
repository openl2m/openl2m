.. image:: ../_static/openl2m_logo.png

============
The Database
============

OpenL2M requires a PostgreSQL database to store data. This can be hosted locally or on a remote server.
Please note that MySQL is not supported, as OpenL2M leverages PostgreSQL's built-in
Postgresql types_

.. _types: https://www.postgresql.org/docs/current/static/datatype-net-types.html

**The installation instructions provided here have been tested to work on the Ubuntu version we develop on.**

*As long as you install a supported version of PostgreSQL, OpenL2M should still work other on versions of
Ubuntu/CentOS/Rocky/AlmaLinux, but those distributions are no longer tested.*

The particular commands needed to install dependencies on other distributions may vary significantly.
Unfortunately, this is outside the control of the OpenL2M maintainers.
Please consult your distribution's documentation for assistance with any errors.

**Installation - Ubuntu**

.. code-block:: bash

  sudo apt install -y postgresql
  sudo systemctl start postgresql
  sudo systemctl enable postgresql

**Installation - MacOS**

.. code-block:: bash

  brew install postgresql
  brew services start postgresql

NOTE: DO NOT USE SUDO TO BREW INSTALL, IT WILL CAUSE PERMISSION ISSUES. If you experience this please refer here_,
or the brew documentation_.

.. _here: https://stackoverflow.com/questions/67688802/brew-postgresql-starts-but-process-is-not-running
.. _documentation: https://docs.brew.sh/Installation

**Verify Version**

Verify you are running a supported version of PostgreSQl:

.. code-block:: bash

  psql -V


**Database Creation**

Now that we have the database server installed, at a minimum, we need to create a database
for OpenL2M and assign it a username and password for authentication.

NOTE: DO NOT USE THE PASSWORD FROM THE EXAMPLE:

.. code-block:: bash

  sudo -u postgres psql
  psql (16.4 ...)
  Type "help" for help.
  postgres=# CREATE DATABASE openl2m;
  CREATE DATABASE
  postgres=# CREATE USER openl2m WITH PASSWORD 'xxxxxxxxxxxx';
  CREATE ROLE
  postgres=# GRANT ALL PRIVILEGES ON DATABASE openl2m TO openl2m;
  GRANT
  postgres=# \q


*MacOS*

.. code-block:: bash

  psql postgres
  psql (16.4 ...)
  Type "help" for help.
  postgres=# CREATE DATABASE openl2m;
  CREATE DATABASE
  postgres=# CREATE USER openl2m WITH PASSWORD 'xxxxxxxxxxxx';
  CREATE ROLE
  postgres=# GRANT ALL PRIVILEGES ON DATABASE openl2m TO openl2m;
  GRANT
  postgres=# \q


You can verify that authentication works issuing the following command and providing the configured password.
(Replace `localhost` with your database server if using a remote database.):

.. code-block:: bash

  psql -U openl2m -W -h localhost openl2m
  <output>
  openl2m=> \connfinfo
  You are connected to database "openl2m" as user "openl2m" on host "localhost"
  <more output>
  \q


If successful, you will enter a `openl2m` prompt. Type `\\q` to exit.

If all is well, you are now ready to install the :doc:`OpenL2M application components <openl2m>`
