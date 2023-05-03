.. image:: ../_static/openl2m_logo.png

===============
Log Maintenance
===============

Removing logs
-------------

In order to keep your database size from growing unlimited, in the configuration, you set the MAX_LOG_AGE value (in days).
To delete log entries beyond this age, you need to run the following Django commands from a command line.

Note: this needs to run with the Python Virtual Environment enabled. You can do this by calling the full path to python as shown below.

.. code-block:: bash

   cd /opt/openl2m/openl2m/
   # if you want more verbose output, add "-v 2" to end of line:
   /opt/openl2m/venv/bin/python3 manage.py removelogs

This is already created as a script file in *scripts/remove_logs.sh*

**Automating removal**

You should also be able to run this script as a cron job, to automatically remove logs eg. every day at 6AM:

.. code-block:: bash

    0 6 * * * /opt/openl2m/scripts/remove_logs.sh > /tmp/remove_logs.sh.out 2>&1

E-mailing logs
--------------

You can email selected OpenL2M logs to a user with the Django command '**maillogs**'.

.. note::

   This requires the EMAIL related settings to be properly configured in the *configuration.py* file!

The '*maillogs*' command gives you the ability to e.g. email detected errors on a daily basis to your ticket system;
or save the logs before you delete them with the *removelogs* command above.

By default, this command will mail '*error*' log entries for the past 1 hour, with the logs in the email body as lines.
You can also send this as an Excel spreadsheet attachment.

Here is an example that emails errors logs for the past 10 days in an attachment, but ignores a few specific errors.

Note: the log error numbers to ignore can be found in the source code at *switches/constants.py*,
look at the numerical LOG action numbers.


.. code-block:: bash

   cd /opt/openl2m/
   # activate the python virtual environment for the django app:
   source venv/bin/activate
   # if you want more verbose output, add "-v 2" to end of line:
   (venv): python3 openl2m/manage.py maillogs --to user@host.edu --hours 240 --attach --ignore 112,258
   Ignoring action 112: Execute Command
   Ignoring action 258: SNMP Error
   Sending most recent 240 hours of log entries for 'error' to 'user@host.edu'
   18 log records found.
   Finished.


Like with the *removelogs* command, you can also automate *maillogs* with a crontab to run e.g. daily.
You can use entry similar to shown below, which runs at 7AM.

Of course, you can also create shell script that has all this and add that as a cron entry. Ask you favorite sys-admin for assistance!

.. code-block:: bash

    0 7 * * * /opt/openl2m/venv/bin/python /opt/openl2m/openl2m/manage.py maillogs --hours 24 --attach --to user@host.edu > /tmp/openl2m_maillogs.out 2>&1


Here are all the relevant options of the *maillogs* command:

.. code-block:: bash

   python3 openl2m/manage.py maillogs --help
   usage: manage.py maillogs [-h] [--type TYPE] [--hours HOURS] [--to TO] [--ignore IGNORE] [--subject SUBJECT] [--attach] [--filename FILENAME] [--version] [-v {0,1,2,3}] [--settings SETTINGS] [--pythonpath PYTHONPATH] [--traceback] [--no-color]
                          [--force-color] [--skip-checks]

   E-mail OpenL2M logs

   optional arguments:
   -h, --help            show this help message and exit
   --type TYPE           the type of log entries. Default is "error".
   --hours HOURS         send the most recent number of hours of log entries. Default is 1 hour.
   --to TO               the email address to send the report to. (no default)
   --ignore IGNORE       comma-separated list of integers representing log actions to ignore in the output. See switches/constants.py for the numerical LOG_ action numbers.
   --subject SUBJECT     the subject of the email. Default is "OpenL2M log report"
   --attach              Create Excel spreadsheet as attachment.
   --filename FILENAME   Log entries attachment filename. Default is "openl2m_logs.xlsx."
