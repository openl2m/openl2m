.. image:: ../_static/openl2m_logo.png

=========
Upgrading
=========

**Before upgrading, make sure you have a backup of the database!!!**

Stop the backend OpenL2M python process first. Also stop Celery if using scheduled tasks:

.. code-block:: bash

  # systemctl stop openl2m
  # systemctl stop celery

You can now upgrade by going to the latest version of the `main` branch of the git repo::

  # cd /opt/openl2m
  # git checkout main
  # git pull origin main
  # git status

Next, you need to run the upgrade script. This is needed to install new
python modules (if any), run database upgrades (if any), and copy
new static files (bootstrap, images, etc...):

.. code-block:: bash

  ./upgrade.sh

**Restart the backend OpenL2M services**

Run:

.. code-block:: bash

  # systemctl start openl2m
  # systemctl start celery
  # systemctl status openl2m
  # systemctl status celery

You should not need to restart the Nginx web server.
