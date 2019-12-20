.. image:: ../_static/openl2m_logo.png

===============
Writing Scripts
===============

**Writing your own scripts**

You can write stand-alone scripts to add or modify objects in the database without adding
to the OpenL2M code base. Look in the /scripts directory for an example.py script.

You can also extend the command line capability of OpenL2M by writing Django Admin Commands.
See **openl2m/switches/management/commands/import_csv.py**
for the implementation of the "import_csv" admin command.

Finally, you can use the Django admin shell to do "inline scripting":

.. code-block:: bash

  python3 manage.py shell


Additional reference are
https://docs.djangoproject.com/en/2.2/howto/custom-management-commands/
and
https://simpleisbetterthancomplex.com/tutorial/2018/08/27/how-to-create-custom-django-management-commands.html
and
https://docs.djangoproject.com/en/2.2/ref/django-admin/#shell
