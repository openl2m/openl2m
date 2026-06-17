.. image:: ../_static/openl2m_logo.png

===========================
OpenL2M Final Install Steps
===========================

Now that you've tailored your configuration.py, it is time to finalize the OpenL2M install.

**Run Upgrade**

.. note::

  If you are using an alternate Python version, do not forget to create the altpython.sh
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



If all is well, you are now ready to install Gunicorn.