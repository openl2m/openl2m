.. image:: ../_static/openl2m_logo.png

Scheduling Bulk-Edit Tasks
==========================

We use the Celery scheduler to schedule tasks. This requires a broker backend.
We are using Redis (see the installation steps). This assumes Redis is installed and working.

The Celery with Django documentation is a good place to start:

* https://docs.celeryproject.org/en/latest/django/first-steps-with-django.html

There a number of other resources on how this works:

* https://stackabuse.com/asynchronous-tasks-in-django-with-redis-and-celery/


**In OpenL2M, all this translates as follows.**

The Celery instance is defined in openl2m/openl2m/celery.py and is instantiated in openl2m/openl2m/__init__.py

We add CELERY_* options to openl2m/openl2m/settings.py, telling Django about the Redis server we use.
We also added EMAIL_* settings, to allow for the results to be sent out.

In switches/tasks.py, we define the bulkedit_task() processing function.

The bulk-edit form in templates/_tab_if_bulkedit.html is modified to add a date/time
selection field, a description, and new submit. In switches/urls.py, we define the new url
'bulkedit_task', with the code in views.py switch_bulkedit_task()

This views.switch_bulkedit_task() function imports the switches.tasks.bulkedit_task(),
and schedules it upon a form submit:

.. code-block:: Python

  from switches.tasks import bulkedit_task



The Date Picker form element in the Bulk Edit form comes from
https://xdsoft.net/jqplugins/datetimepicker/
(source is at https://github.com/xdan/datetimepicker)
See also
https://simpleisbetterthancomplex.com/tutorial/2019/01/03/how-to-use-date-picker-with-django.html
