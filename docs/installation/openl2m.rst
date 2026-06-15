.. image:: ../_static/openl2m_logo.png

=======================
The OpenL2M Application
=======================

This section of the documentation discusses installing and configuring the
OpenL2M application.

Dependencies
------------

Begin by installing all system packages required by OpenL2M and its dependencies.

**Note: on Ubuntu 24.04 you can install the 'system' Python (v3.12) and PostgreSql (v16).
On other distro's, install the required Python (v3.12-3.13)**

.. code-block:: bash

  # On Ubuntu 24.04:
  sudo apt install -y libxml2-dev libxslt1-dev libffi-dev libpq-dev libssl-dev zlib1g-dev
  sudo apt install -y libldap2-dev libsasl2-dev libssl-dev snmpd snmp libsnmp-dev git curl
  sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential software-properties-common

.. note::

  Make sure this installs either Python v3.12 - v3.13! Other versions are NOT supported!

:doc:`See the Alternate Python Installation section for more. <alt-python>`

**On MacOS:**

.. note::

  MacOS support is not well tested. Proceed with caution...


.. code-block:: bash

  brew install libxml2 libxslt libffi postgresql openssl zlib
  brew install openldap cyrus-sasl net-snmp git curl
  # replace @3.10 with your preferred version, we have tested on v3.10 - v3.13
  brew install python@3.10

OpenL2M Install
---------------

First, create the user environment for OpenL2M:

.. code-block:: bash

  sudo adduser --system --group openl2m


**On MacOS:**

.. code-block:: bash

  #create the user
  sudo dscl . -create /Users/openl2m
  sudo dscl . -create /Users/openl2m UserShell /usr/bin/false
  sudo dscl . -create /Users/openl2m UniqueID 600
  sudo dscl . -create /Users/openl2m PrimaryGroupID 600
  sudo dscl . -create /Users/openl2m NFSHomeDirectory /var/empty

  #create the group
  sudo dscl . -create /Groups/openl2m
  sudo dscl . -create /Groups/openl2m PrimaryGroupID 600
  sudo dscl . -append /Groups/openl2m GroupMembership openl2m

  #add openl2m to the group
  sudo dscl . -append /Groups/openl2m GroupMembership openl2m

Next, install OpenL2M. The easiest is cloning the main branch of its repository on GitHub.


**Clone the Git Repository**

Create the base directory for the OpenL2M installation. For this guide, we'll use `/opt/openl2m`:

.. code-block:: bash

  sudo mkdir -p /opt/openl2m/ && cd /opt/openl2m/


If `git` is not already installed, install it:

.. code-block:: bash

  sudo apt install -y git


Next, clone the **main** branch of the OpenL2M GitHub repository into the current directory:

.. code-block:: bash

  git clone -b main https://github.com/openl2m/openl2m.git .
  Cloning into '.'...
  ...
  Checking connectivity... done.


Required Configuration
----------------------

Move into the OpenL2M configuration directory and make a copy of `configuration.example.py` named `configuration.py`:

.. code-block:: bash

  (venv) # cd openl2m/openl2m/
  (venv) # cp configuration.example.py configuration.py

Open `configuration.py` with your preferred editor and go through all possible options.
At the minimum set the following variables:

.. code-block:: bash

  * ALLOWED_HOSTS
  * CSRF_TRUSTED_ORIGINS
  * DATABASE
  * SECRET_KEY
  * TIME_ZONE

**ALLOWED_HOSTS**

This is a list of the valid hostnames by which this server can be reached.
You must specify at least one name or IP address.

Example:

.. code-block:: bash

  ALLOWED_HOSTS = ['openl2m.example.com', '10.0.0.1']

**CSRF_TRUSTED_ORIGINS**

This is a list of URLs used to access your site. Note this **requires** the scheme for your domain,
to protect against Cross Site Request Forgery. I.e. you need to include 'https://' or 'http://' if not secured!
You can include IP address if needed...

.. code-block:: bash

  CSRF_TRUSTED_ORIGINS = ['https://openl2m.example.com', 'https://10.0.0.1']

**DATABASE**

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

**SECRET_KEY**

Generate a random secret key of at least 50 alphanumeric characters.
This key must be unique to this installation and must not be shared
outside the local system.

You may use the script located at `openl2m/generate_secret_key.py` to
generate a suitable key.

In the case of a highly available installation with multiple web servers,
`SECRET_KEY` must be identical among all servers in order to maintain a
persistent user session state.

Other variables in the configuration files are commented. Change settings as needed in your environment.

**TIME_ZONE**

Set this to the appropriate time zone name, to get logs, etc. in the local time.
E.g. set this to something like 'Asia/Tokyo', 'Europe/Amsterdam' or 'America/Los_Angeles', etc.


Next, read about additional optional settings.
