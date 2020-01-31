.. image:: ../_static/openl2m_logo.png

=========================
Bulk-Edit Task Scheduling
=========================

To allow users to schedule Bulk Edit tasks at some time in the future,
you need to install the Redis message queue, and Celery task queuing system.

If you do *NOT* want to enable this feature, simple ignore the rest of this page!

To enable task scheduling, set the following in configuration.py

.. code-block:: bash

  TASKS_ENABLED = True

.. note::

  You also need to set the TIME_ZONE to the local time zone of your environment.
  If this is NOT set, tasks will not be scheduled properly (unless your users do the conversion
  when they submit the date and time for the task)


Next, you need to install Redis and Celery.

Install Redis:
--------------

CentOS 7:

.. code-block:: bash

  sudo yum install -y redis

CentOS 8:

.. code-block:: bash

  sudo dnf install -y redis

And then start and enable:

.. code-block:: bash

  sudo systemctl enable redis
  sudo systemctl start redis
  sudo systemctl status redis

Note: you can also use an already existing Redis setup, either on the same server or remotely.
This is left as an exercise to the reader. If you do, take a close look at the
CELERY variables in openl2m/configuration.py

Install Celery:
---------------

.. code-block:: bash

  sudo pip3 install celery[redis]

Test Celery:
------------

Test this from the ./openl2m/ directory (where manage.py lives).
Run the command below. You should see some lines indicating success:

.. code-block:: bash

  celery -A openl2m worker --loglevel info

  <...snip...>
  [2019-12-22 00:31:57,754: INFO/MainProcess] Connected to redis://localhost:6379//
  [2019-12-22 00:31:57,789: INFO/MainProcess] mingle: searching for neighbors
  [2019-12-22 00:31:58,848: INFO/MainProcess] mingle: all alone
  [2019-12-22 00:31:58,872: INFO/MainProcess] celery@your.host.name ready.

.. note::

  You should not have to configure anything in openl2m/configurations.py to use
  Celery with the default Redis setup. However, if your Redis setup is used by other
  clients/tools as well, you may need to change the database that is used.
  The default database is 0, and the default installation allows up to 16 databases.
  See the Celery / Redis documentation for more.

If you want to modify the config, start by taking a look at

.. code-block:: bash

  CELERY_BROKER_URL = getattr(configuration, 'CELERY_BROKER_URL', 'redis://localhost:6379')
  CELERY_RESULT_BACKEND = getattr(configuration, 'CELERY_RESULT_BACKEND', 'redis://localhost:6379')

You may need to indicate the database number following the port, e.g. for database 3:

  redis://localhost:6379/3

For more, please contact your Redis admin, and/or read the Redis and Celery documentation.


Run Celery as a Service:
------------------------

You will need to configure systemd to run the Celery process.
(See more at https://docs.celeryproject.org/en/latest/userguide/daemonizing.html)

We need a user to run this process. You will need sudo (or root) access. Run:

.. code-block:: bash

  sudo useradd celery

Next, we need directories for the logs and PID files:

.. code-block:: bash

  sudo mkdir /var/run/celery
  sudo chmod 0755 /var/run/celery
  sudo chown celery:celery /var/run/celery
  sudo mkdir /var/log/celery
  sudo chmod 0755 /var/log/celery
  sudo chown celery:celery /var/log/celery


Copy the Celery configuration file celery.default to /etc/default/celeryd

.. code-block:: bash

  sudo cp celery.default /etc/default/celeryd


The service definition is in the file celery.service
Copy this file into the system directory:

.. code-block:: bash

  sudo cp celery.service /etc/systemd/system

Now, we can activate and start this service:

.. code-block:: bash

  sudo systemctl daemon-reload
  sudo systemctl start celery
  sudo systemctl enable celery

And verify:

.. code-block:: bash

  systemctl status celery


Sending Result Emails
---------------------

You can have the results of tasks be emailed to the users. This is enabled by default,
and assumes your server is running a standard SMTP server on port 25.

You can install a default email service as such:

On CentOS 7:

.. code-block:: bash

  sudo yum install postfix

On CentOS 8:

.. code-block:: bash

  sudo dnf install postfix

Then enable it (on 7 or 8):

.. code-block:: bash

  sudo systemctl start postfix
  sudo systemctl enable postfix


If you want to use another mail server you can adjust the values in configuration.py.
See the Django documentation for more at
https://docs.djangoproject.com/en/2.2/ref/settings/#email-host

E.g. To point to a different SMTP server, adjust this:

.. code-block:: bash

  EMAIL_HOST = 'smtp.your-domain.com'

E.g. if you want to send via Gmail, this is what you should use:

.. code-block:: bash

  EMAIL_HOST = 'smtp.gmail.com'
  EMAIL_HOST_USER = '<username>@gmail.com'
  EMAIL_HOST_PASSWORD = '<password>'
  EMAIL_PORT = 587
  EMAIL_USE_TLS = True

Viewing Tasks
-------------

There is a global 'Scheduled Tasks' option in the top right menu. You can see tasks here.
Admins and Staff have access to all tasks. Users can access their scheduled tasks.


Monitoring Celery
-----------------

If you have a desire to monitor your Celery background process, take a look at Celery Flower.
See https://flower.readthedocs.io/en/latest/ and
https://docs.celeryproject.org/en/latest/userguide/monitoring.html#flower-real-time-celery-web-monitor
for more.

Something like this should work in a new shell (window):

.. code-block:: bash

  cd /opt/openl2m/openl2m
  celery -A openl2m flower

This should start a web server on port 5555. Now point a browser to
http://localhost:5555/ to see lots of interesting details about your Celery tasks.


Time Format Customization
-------------------------

The default time selector for tasks uses a 12-hour AM/PM clock. If you want to use 24 Hour time format, set to True.

.. code-block:: bash

  TASK_USE_24HR_TIME = False

By default, users can choose time in 5 minute increments (0,5,10,15,...). Change this to set an increment as save_needed

.. code-block:: bash

  TASK_SUBMIT_MINUTE_INCREMENT = 5

By default, users can schedules tasks up to 28 days (4 weeks) into the future. Set this as needed.

.. code-block:: bash

  TASK_SUBMIT_MAX_DAYS_IN_FUTURE = 28


Advanced Time Field Customization
---------------------------------

.. warning::

  If you want to change the date & time format beyond what is listed above, take a look at the openl2m/settings.py file.
  There are several other format variables available, e.g Internation format with Day-Month-Year. The two settings below
  are inter-dependent, and if you make a mistake, date & time parsing will fail!

Take a look at:

.. code-block:: bash

  # pay attention to these two, they need to match format!
  # Flatpickr option 'dateFormat: "Y-m-d H:i"''
  FLATPICKR_DATE_FORMAT = getattr(configuration, 'FLATPICKR_DATE_FORMAT', 'Y-m-d H:i')
  # this next one needs to match the Flatpickr 'dateFormat' option above,
  # minus the ending %z which add timezone offset:
  TASK_SUBMIT_DATE_FORMAT = getattr(configuration, 'TASK_SUBMIT_DATE_FORMAT', '%Y-%m-%d %H:%M %z')

See the following two pages for more:

* https://flatpickr.js.org/formatting/
* https://docs.python.org/3.6/library/datetime.html#strftime-strptime-behavior
