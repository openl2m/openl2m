.. image:: ../_static/openl2m_logo.png

=======================
The OpenL2M Application
=======================

This section of the documentation discusses installing and configuring the
OpenL2M application.

Dependencies
------------

Begin by installing all system packages required by OpenL2M and its dependencies.

**Ubuntu 20.04 LTS**

.. code-block:: bash

  sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential libxml2-dev libxslt1-dev libffi-dev libpq-dev libssl-dev zlib1g-dev
  sudo apt install -y libldap2-dev libsasl2-dev libssl-dev snmpd snmp libsnmp-dev

**CentOS 8**

.. code-block:: bash

  # dnf install -y gcc make net-snmp net-snmp-utils net-snmp-devel openssl-devel openldap-devel python36-devel


**CentOS 7**


.. code-block:: bash

  # yum install -y gcc make net-snmp net-snmp-utils net-snmp-devel openssl-devel openldap-devel epel-release

You then need the following Python v3 packages:

.. code-block:: bash

  # yum install -y python36 python36-devel python36-setuptools
  # easy_install-3.6 pip
  # ln -s /usr/bin/python36 /usr/bin/python3


OpenL2M Install
---------------

First, create the user environment for OpenL2M:

.. code-block:: bash

  sudo adduser --system --group openl2m


Next, install OpenL2M. The easiest is cloning the main branch of its repository on GitHub.

**Clone the Git Repository**

Create the base directory for the OpenL2M installation. For this guide, we'll use `/opt/openl2m`:

.. code-block:: bash

  sudo mkdir -p /opt/openl2m/ && cd /opt/openl2m/


If `git` is not already installed, install it:

**CentOS 8**

.. code-block:: bash

  # dnf install -y git

**CentOS 7**

.. code-block:: bash

  # yum install -y git


Next, clone the **main** branch of the OpenL2M GitHub repository into the current directory:

.. code-block:: bash

  # git clone -b main https://github.com/openl2m/openl2m.git .
  Cloning into '.'...
  ...
  Checking connectivity... done.

**Configuration**

Move into the OpenL2M configuration directory and make a copy of `configuration.example.py` named `configuration.py`:

.. code-block:: bash

  (venv) # cd openl2m/openl2m/
  (venv) # cp configuration.example.py configuration.py

Open `configuration.py` with your preferred editor and go through all possible options.
At the minimum set the following variables:

.. code-block:: bash

  * ALLOWED_HOSTS
  * DATABASE
  * SECRET_KEY
  * TIME_ZONE

*ALLOWED_HOSTS*

This is a list of the valid hostnames by which this server can be reached.
You must specify at least one name or IP address.

Example:

.. code-block:: bash

  ALLOWED_HOSTS = ['openl2m.example.com', '192.168.1.100']

*DATABASE*

This parameter holds the database configuration details. You must define the
username and password used when you configured PostgreSQL. If the service is
running on a remote host, replace `localhost` with its address.

Example:

.. code-block:: bash

  DATABASE = {
      'NAME': 'openl2m',              # Database name
      'USER': 'openl2m',              # PostgreSQL username
      'PASSWORD': 'xxxxxxxxxxxxxxxx', # PostgreSQL password
      'HOST': 'localhost',            # Database server
      'PORT': '',                     # Database port (leave blank for default)
  }

*SECRET_KEY*

Generate a random secret key of at least 50 alphanumeric characters.
This key must be unique to this installation and must not be shared
outside the local system.

You may use the script located at `openl2m/generate_secret_key.py` to
generate a suitable key.

In the case of a highly available installation with multiple web servers,
`SECRET_KEY` must be identical among all servers in order to maintain a
persistent user session state.

Other variables in the configuration files are commented. Change settings as needed in your environment.

*TIME_ZONE*

Set this to the appropriate time, to get logs, etc. in the local time. Note that if you enable
tasks, you need to set this appropriately, as using UTC will result in tasks running at unexpected times!



**Run Upgrade**

The upgrade.sh script will install all required packages in a Python Virtual Environment.
(This means we do not interfere with the system-wide python packages.)
If you encounter any compilation errors during this last step, ensure that
you've installed all of the system dependencies listed above! :

.. code-block:: bash

  # pip3 install --upgrade pip
  # cd /opt/openl2m
  # ./upgrade.sh

If you encounter errors while installing the required packages, check that
you're running a recent version of pip with the command `pip3 -V`.



**Run Database Migrations**

Before OpenL2M can run, we need to install the database schema.
This is done by running `python3 manage.py migrate` from the
`OpenL2M` directory (`/opt/openl2m/openl2m/` in our example):

.. code-block:: bash

  (venv) # cd /opt/openl2m/openl2m/
  (venv) # python3 manage.py migrate
  Operations to perform:
    Apply all migrations: ...
  Running migrations:
    Rendering model states... DONE
    Applying ... OK
    ...

If this step results in a PostgreSQL authentication error, ensure that the
username and password created in the database match what has been
specified in `configuration.py`

**Create a Super User**

OpenL2M does not come with any predefined user accounts. You'll need to
create a super user to be able to log into OpenL2M:

.. code-block:: bash

  $ source venv/bin/activate
  (venv) $ python3 manage.py createsuperuser
  Username: admin
  Email address: admin@example.com
  Password:
  Password (again):
  Superuser created successfully.


**Load Initial Data (Optional)**

OpenL2M does not ship with any initial data. Optionally, you can import a
variety of data using the Django *manage.py import_csv*  admin command,
:doc:`see this document <../configuration/importing>`.

This will speed up loading the data with the proper SNMP profiles, VLANs, Switches, etc.
Additionally, the script directory has an example.py file showing how to program
the Django objects outside the context of the application.
Please create your own import script as needed.

It's perfectly fine to start using OpenL2M without using this initial data
if you'd rather create everything from scratch in the admin interface.


**Test the Application**

At this point, OpenL2M should be able to run. We can verify this by starting
a development instance:

.. code-block:: bash

  (venv) # python3 manage.py runserver 0:8000 --insecure
  Performing system checks...

  System check identified no issues (0 silenced).
  February 10, 2020 - 19:21:07
  Django version 2.2.10, using settings 'openl2m.settings'
  Starting development server at http://0:8000/
  Quit the server with CONTROL-C.

Next, connect to the name or IP of the server (as defined in `ALLOWED_HOSTS`) on port 8000;
for example, <http://127.0.0.1:8000/>. You should be greeted with the OpenL2M home page.
Note that this built-in web service is for development and testing purposes only.
**It is not suited for production use.**

If the test service does not run, or you cannot reach the OpenL2M home page, something has gone wrong.
Do not proceed with the rest of this guide until the installation has been corrected.

Note that you may need to open the proper firewall port,
or disable the firewalld process temporarily:

.. code-block:: bash

  # firewall-cmd --zone=public --permanent --add-port=8000/tcp
  # firewall-cmd --reload

or:

.. code-block:: bash

  # systemctl stop firewalld

Make sure you restart or undo the configuration changes when done testing!

If all is well, you are now ready to install the :doc:`webserver <nginx>`.
