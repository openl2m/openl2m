.. image:: ../_static/openl2m_logo.png

============
The Database
============

NOTE: this is a copy of the NetBox PostgreSQL installation document.

OpenL2M requires a PostgreSQL database to store data. This can be hosted locally or on a remote server.
Please note that MySQL is not supported, as OpenL2M leverages PostgreSQL's built-in
Postgresql types_

.. _types: https://www.postgresql.org/docs/current/static/datatype-net-types.html

The installation instructions provided here have been tested to work on CentOS 7.x & 8.x.
The particular commands needed to install dependencies on other distributions may vary significantly.
Unfortunately, this is outside the control of the OpenL2M maintainers.
Please consult your distribution's documentation for assistance with any errors.

OpenL2M v2 requires PostgreSQL 9.5 or higher.

**Installation - Ubuntu 20.04 LTS**

.. code-block:: bash

  sudo apt install -y postgresql
  sudo systemctl start postgresql
  sudo systemctl enable postgresql


**Installation - CentOS 8**

CentOS 8 ships with a relatively recent version of PostgreSQL,
so you can easily install it:

.. code-block:: bash

  # dnf install postgresql-server

Initialize the server:

.. code-block:: bash

  # postgresql-setup --initdb --unit postgresql

CentOS users should modify the PostgreSQL configuration to accept password-based authentication
by replacing `ident` with `md5` for all host entries within `/var/lib/pgsql/data/pg_hba.conf`.

For example:

.. code-block:: bash

  host    all             all             127.0.0.1/32            md5
  host    all             all             ::1/128                 md5

And then start it and set to auto-start on boot:

.. code-block:: bash

  # systemctl start postgresql
  # systemctl enable postgresql

If this is a remote database server, see this page for details on how to configure this:
https://linuxconfig.org/how-to-install-postgres-on-redhat-8

**Installation - CentOS 7**

CentOS 7.x does not ship with a recent enough version of PostgreSQL,
so it will need to be installed from an external repository.
The instructions below show the installation of PostgreSQL 9.6:

.. code-block:: bash

  # yum install https://download.postgresql.org/pub/repos/yum/9.6/redhat/rhel-7-x86_64/pgdg-centos96-9.6-3.noarch.rpm
  # yum install postgresql96 postgresql96-server postgresql96-devel
  # /usr/pgsql-9.6/bin/postgresql96-setup initdb


CentOS users should modify the PostgreSQL configuration to accept password-based authentication
by replacing `ident` with `md5` for all host entries within `/var/lib/pgsql/9.6/data/pg_hba.conf`.

For example:

.. code-block:: bash

  host    all             all             127.0.0.1/32            md5
  host    all             all             ::1/128                 md5

Then, start the service and enable it to run at boot:

.. code-block:: bash

  # systemctl start postgresql-9.6
  # systemctl enable postgresql-9.6



**Database Creation**

Now that we have the database server installed, at a minimum, we need to create a database for OpenL2M and assign it a username and password for
authentication.

NOTE: DO NOT USE THE PASSWORD FROM THE EXAMPLE:

.. code-block:: bash

  # sudo -u postgres psql
  psql (12.8)
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

  # psql -U openl2m -W -h localhost openl2m
  <output>
  openl2m=> \connfinfo
  You are connected to database "openl2m" as user "openl2m" on host "localhost"
  <more output>
  \q


If successful, you will enter a `openl2m` prompt. Type `\q` to exit.

If all is well, you are now ready to install the :doc:`OpenL2M application components <openl2m>`
