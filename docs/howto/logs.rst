.. image:: ../_static/openl2m_logo.png

===============
Log Maintenance
===============

**Removing old logs from the OpenL2M database**

In order to keep your database size from growing unlimited, in the configuration, you set the MAX_LOG_AGE value (in days).
To delete log entries beyond this age, you need to run the following Django command line.

Note: this needs to run with the Python Virtual Environment enabled. You can do this by calling the full path to python as show below.

.. code-block:: bash

   cd /opt/openl2m/openl2m/
   # if you want more verbose output, add "-v 2" to end of line:
   /opt/openl2m/venv/bin/python3 manage.py removelogs

This is already created as a script file in scripts/remove_logs.sh

**Automating removal**

You should also be able to run this script as a cron job, to automatically remove logs eg. every day at 6AM:

.. code-block:: bash

    0 6 * * * /opt/openl2m/scripts/remove_logs.sh > /tmp/remove_logs.sh.out 2>&1
