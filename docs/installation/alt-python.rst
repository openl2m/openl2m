.. image:: ../_static/openl2m_logo.png

===============================
Using Alternate Python Versions
===============================

On CentOS 8, the stock python is version 3.6 This version will not be supported past 2021.
While at this time we have only tested minimally,
you can use newer versions of Python, e.g. v3.8

Follow these steps:

Python Installation
-------------------

Install the alternate version of Python. The details are left to the user,
but in general, this will be something like:

#. install required development packages for your OS. Probably something like:

.. code-block:: bash
  sudo dnf groupinstall 'development tools'

#. download latest python source from https://www.python.org/downloads/
   (e.g. v3.8.7 at the time of this writing).
   E.g

.. code-block:: bash
  cd <your src installation directory>
  VER=3.8.7
  wget https://www.python.org/ftp/python/${VER}/Python-${VER}.tgz
  tar -zxvf Python-${VER}.tgz
  cd Python-${VER}

#. compile it, by following instructions in Readme.1st

.. code-block:: bash
  ./configure --enable-optimizations
  make
  make test

#. install as 'alternate' version, so as to not overwrite the system python 3.

.. code-block:: bash
  sudo make altinstall

#. or, if you know what you are doing, change your system's python version to be v3.8
   In this case you can ignore the following step!

OpenL2M Configuration
---------------------

Find the full path to your new Python:

.. code-block:: bash

  which python3.8

Copy the file **altpython.sh** to the top level directory (where upgrade.sh is),
and modify it to point the PYTHON variable to this alternate python:

.. code-block:: bash

  cd /opt/openl2m
  cp scripts/altpython.sh .
  vi altpython.sh

Change this line to point to the proper python 3:

.. code-block:: bash

  PYTHON="/usr/local/bin/python3.8"


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
