.. image:: ../_static/openl2m_logo.png

=========
Upgrading
=========

:doc:`Before upgrading, make sure you have a backup of the database!!! <../howto/maintain>`

Stop the backend OpenL2M python process first.

.. code-block:: bash

  sudo systemctl stop openl2m

Also stop Celery if using scheduled tasks:

.. code-block:: bash

  sudo systemctl stop celery

You can now upgrade by going to the latest version of the `main` branch of the git repo::

  cd /opt/openl2m
  sudo git checkout main
  sudo git pull origin main
  sudo git status

Next, you need to run the upgrade script. This is needed to install new
python modules (if any), run database upgrades (if any), and copy
new static files (bootstrap, images, etc...):

.. code-block:: bash

  sudo ./upgrade.sh

**Restart the backend OpenL2M services**

Run:

.. code-block:: bash

  sudo systemctl start openl2m
  sudo systemctl status openl2m

As needed, retart celery:

.. code-block:: bash

  sudo systemctl start celery
  systemctl status celery

You should not need to restart the Nginx web server.
