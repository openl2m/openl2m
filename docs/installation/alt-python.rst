.. image:: ../_static/openl2m_logo.png

===============================
Using Alternate Python Versions
===============================

OpenL2M is developed and tested on Ubuntu 24.04 with Python v3.12

If you distribution does not by default install a supported version of Python,
you can retrieve a different version from the "Deadsnakes" PPA.
Using this repository is well documented on many web pages.

The details of installing an alternate version of Python for other distros and from other repos are left to the user.

On Ubuntu, you will need the following regular system packages:

.. code-block:: bash

  sudo apt install -y build-essential software-properties-common


To install an alternative Python version from a package repositories,
you will need the following parts (replace xx with the version you want!):

.. code-block:: bash

  # pick your repo:
  sudo add-apt-repository ppa:deadsnakes/ppa
  # install needed python 3.xx packages
  sudo apt install python3.xx python3.xx-dev python3.xx-venv


*The excercise of installing from source is left to the reader!*


OpenL2M Configuration
---------------------

Find the full path to your new Python. Here we use v3.13:

.. code-block:: bash

  which python3.13

Copy the file **altpython.sh** to the top level directory (where upgrade.sh is),
and modify it to point the PYTHON variable to this alternate python:

.. code-block:: bash

  cd /opt/openl2m
  cp scripts/altpython.sh .
  vi altpython.sh

Change this line to point to the proper python 3:

.. code-block:: bash

  PYTHON="/usr/bin/python3.13"


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


MacOS Python Versions
---------------------

You may use brew to install other versions of Python on MacOS. If you frequently switch versions,
you may be interested in `pyenv`_

.. _pyenv: https://realpython.com/intro-to-pyenv/