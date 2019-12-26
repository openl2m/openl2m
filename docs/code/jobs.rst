.. image:: ../_static/openl2m_logo.png

Scheduling Bulk-Edit Jobs
=========================

We use the Celery scheduler to schedule jobs. This requires a broker backend.
We are using Redis (see the installation steps). This assumes Redis is installed and working.

The Celery with Django documentation is a good place to start:

* https://docs.celeryproject.org/en/latest/django/first-steps-with-django.html

There a number of other resources on how this works:

* https://stackabuse.com/asynchronous-tasks-in-django-with-redis-and-celery/


**In OpenL2M, all this translates as follows.**

The Celery instance is defined in openl2m/openl2m/celery.py and is instantiated in openl2m/openl2m/__init__.py

We add CELERY_* options to openl2m/openl2m/settings.py, telling Django about the Redis server we use.
We also added EMAIL_* settings, to allow for the results to be sent out.

In switches/tasks.py, we define the bulkedit_job() task.

The bulk-edit form in templates/_tab_if_bulkedit.html is modified to add a date/time selection field and new submit.
In switches/urls.py, we define the new url 'bulkedit_job', with the code in views.py switch_bulkedit_job()

This views.switch_bulk_edit_job() function imports the tasks.bulkedit_job(), and schedules it upon a form submit:

.. code-block:: Python

  from switches.tasks import bulkedit_job



The Date Picker form element in the Bulk Edit form comes from
  OLD:  https://github.com/uxsolutions/bootstrap-datepicker
  CURRENT: https://github.com/xdan/datetimepicker
  See also: https://www.jqueryscript.net/time-clock/Clean-jQuery-Date-Time-Picker-Plugin-datetimepicker.html

See this for more:
  https://formden.com/blog/date-picker
