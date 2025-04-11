.. image:: ../_static/openl2m_logo.png

=======================
The OpenL2M Application
=======================

This section of the documentation discusses installing and configuring the
OpenL2M application.

Dependencies
------------

Begin by installing all system packages required by OpenL2M and its dependencies.

**Note: on Ubuntu 24.04 or 22.04, you can install the 'system' Python (v3.12 or v3.10).**

.. code-block:: bash

  sudo apt install -y libxml2-dev libxslt1-dev libffi-dev libpq-dev libssl-dev zlib1g-dev
  sudo apt install -y libldap2-dev libsasl2-dev libssl-dev snmpd snmp libsnmp-dev git curl
  # On Ubuntu 24.04 or 22.04:
  sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential software-properties-common

.. note::

  Make sure this installs either Python v3.10, v3.11 or v3.12! Other versions are NOT supported!

*For best performance, we recommend using Python v3.12 (Ubuntu 24.04), as it has significant improvements over v3.10*
:doc:`See the Alternate Python Installation section for more. <alt-python>`

**On MacOS:**

.. code-block:: bash

  brew install libxml2 libxslt libffi postgresql openssl zlib
  brew install openldap cyrus-sasl net-snmp git curl
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


**Configuration**

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

*ALLOWED_HOSTS*

This is a list of the valid hostnames by which this server can be reached.
You must specify at least one name or IP address.

Example:

.. code-block:: bash

  ALLOWED_HOSTS = ['openl2m.example.com', '10.0.0.1']

*CSRF_TRUSTED_ORIGINS*

This is a list of URLs used to access your site. Note this **requires** the scheme for your domain,
to protect against Cross Site Request Forgery. I.e. you need to include 'https://' or 'http://' if not secured!
You can include IP address if needed...

.. code-block:: bash

  CSRF_TRUSTED_ORIGINS = ['https://openl2m.example.com', 'https://10.0.0.1']

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

Set this to the appropriate time, to get logs, etc. in the local time.


**API settings**

:doc:`API settings are discussed here.<api>`


**Run Upgrade**

.. note::

  If you are using an alternate Python version (eg. v3.11), do not forget to create the altpython.sh
  files are documented in the alt-python install steps!

The upgrade.sh script will install all required packages in a Python Virtual Environment.
(This means we do not interfere with the system-wide python packages.)
If you encounter any compilation errors during this last step, ensure that
you've installed all of the system dependencies listed above! :

.. code-block:: bash

  sudo pip3 install --upgrade pip
  cd /opt/openl2m
  ./upgrade.sh

If you encounter errors while installing the required packages, check that
you're running a recent version of pip with the command `pip3 -V`.


**Create a Super User**

OpenL2M does not come with any predefined user accounts. You'll need to
create a super user to be able to log into OpenL2M:

.. code-block:: bash

  $ source venv/bin/activate
  (venv) $ python3 openl2m/manage.py createsuperuser
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
a development instance. For this, you will need to enable Django Debug Mode:

Edit the config file at openl2m/openl2m/configuration.py, and add at the top of the file:

.. code-block:: bash

  DEBUG = True

Now start the development web server as such:

.. code-block:: bash

  (venv) # python3 openl2m/manage.py runserver 0:8000 --insecure
  Performing system checks...

  System check identified no issues (0 silenced).
  October 26, 2021 - 19:21:07
  Django version 3.2.8, using settings 'openl2m.settings'
  Starting development server at http://0:8000/
  Quit the server with CONTROL-C.

Next, connect to the name or IP of the server (as defined in `ALLOWED_HOSTS`) on port 8000;
for example, <http://127.0.0.1:8000/>. You should be greeted with the OpenL2M home page.

.. warning::

  This built-in web service is for development and testing purposes only.
  **It is not suited for production use.**

If the test service does not run, or you cannot reach the OpenL2M home page, something has gone wrong.
Do not proceed with the rest of this guide until the installation has been corrected.

Note that you may need to open the proper firewall port,
or disable the firewall process temporarily.

.. code-block:: bash

  sudo ufw alow 8000

or:

.. code-block:: bash

  sudo systemctl disable ufw


Make sure you restart or undo the configuration changes (Both DEBUG and firewall settings!) when done testing!

If all is well, you are now ready to install the :doc:`webserver <nginx>`.


.. note::

  IF ALL YOUR SNMP DEVICES FAIL, please see :doc:`the troubleshooting section <../troubleshooting>`.
