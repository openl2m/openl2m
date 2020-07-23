.. image:: ../_static/openl2m_logo.png

===============================
Using Alternate Python Versions
===============================

On CentOS 8, the stock python is version 3.6 While we have only tested minimally,
you can use other versions of Python, e.g. v3.7

Follow these steps:

Python Installation
-------------------

Install the alternate version of Python. The details are left to the user,
but in general, this will be something like:

#. install required development packages for your OS.
#. download latest python source (e.g. v3.7.8 or v3.8.5 at the time of this writing).
#. compile it.
#. install as 'alternate' version, so as to not overwrite the system python 3.

OpenL2M Configuration
---------------------

Find the full path to your new Python:

.. code-block:: bash

  which python3.7

Modify the *upgrade.sh* file to point to this alternate python:

.. code-block:: bash

  cd /opt/openl2m
  vi upgrade.sh

and change this line to point to the proper python 3:

.. code-block:: bash

  PYTHON="/usr/local/bin/python3.7"


Verify
------

Stop the services, and run the upgrade:

.. code-block:: bash

  sudo systemctl stop openl2m
  sudo systemctl stop celery
  ./upgrade.sh

This will recreate the virtual environment, and should not show any errors.

Now verify the version of python in the virtual environment:

.. code-block:: bash

  source venv/bin/activate
  which python3
  python3 -V

This will activate the virtual environment, show the path to python
(should be */opt/openl2m/venv/bin/python3*), and the version (whatever you installed).

If this is all correct, you can restart the services, and should be good to go!

.. code-block:: bash

  sudo systemctl start openl2m
  sudo systemctl start celery

**NOTE** if you use an alternate python version, make sure you check the
*upgrade.sh* after every code update, as it may have changed and
overwritten your modification!
