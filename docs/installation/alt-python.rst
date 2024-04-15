.. image:: ../_static/openl2m_logo.png

===============================
Using Alternate Python Versions
===============================

On Ubuntu 20.04 the stock python version are 3.8. This is the oldest version currently supported.
OpenL2M is now developed and tested on Python 3.11

Python 3.12 is NOT supported. The SNMP library used has a dependency on some functionality that was removed in v3.12
Note that in Ubuntu 24.04, the default Python is v3.12 !
Ie. you will need to use the information below to install down to v3.11

Alternate Python Installation
-----------------------------

The details of installing an alternate version of Python are left to the user. On Ubuntu, we recommend
you use Python 3.11 from the "Deadsnakes" PPA. Using this repository is well documented on many web pages.

To install an alternative Python version from package repositories,
you will need the following parts:

.. code-block:: bash

  python3.11
  python3.11-dev
  python3.11-venv

*The excercise of installing from source is left to the reader!*


OpenL2M Configuration
---------------------

Find the full path to your new Python. Here we use v3.11:

.. code-block:: bash

  which python3.11

Copy the file **altpython.sh** to the top level directory (where upgrade.sh is),
and modify it to point the PYTHON variable to this alternate python:

.. code-block:: bash

  cd /opt/openl2m
  cp scripts/altpython.sh .
  vi altpython.sh

Change this line to point to the proper python 3:

.. code-block:: bash

  PYTHON="/usr/bin/python3.11"


Verify
------

Stop the services, and run the upgrade:

.. code-block:: bash

  sudo systemctl stop openl2m
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
