.. image:: ../_static/openl2m_logo.png

Code Introduction
=================

This document attempts to describe how OpenL2M is functioning inside the Django framework

As is Django custom, all Django files are stored in the *openl2m/* sub-directory.
From here forward, all references to other directories will be relative to this location.

**The OpenL2M Django Project**

A Django project consists of a project definition directory, and one or more applications in separate directories.

Django's "project" is in the *openl2m/openl2m/* directory. This is where the whole process starts.

* *urls.py*

This file is the 'mapper' where all urls paths are mapped, either directly or by
including url files from the apps that make up the project.

* *admin.py*

Here we create a custom admin site variable, named "admin_site".
This allows use to make changes to the admin functionality and views,
and is referenced also in the "users" app. We customize the admin site
`using the techniques described here.
<https://docs.djangoproject.com/en/2.2/ref/contrib/admin/#hooking-adminsite-to-urlconf>`_

**Authentication**

All pages require user authentication. :doc:`This is described here. <authentication>`

**The apps**

There are two apps at this time:

* :doc:`users <users_app/index>`

This where additional attributes are defined for the built-in Django User()
object. It is in the users/ directory.

* :doc:`switches <switches_app/index>`

This is where most of the work with SNMP and the GUI is handled.
It is in the switches/ directory.


**Additional directories**

They are:

* *templates/*

This is where all templates are stored. (I.e. we use a central directory,
and not templates-per-app, as is custom for some other Django applications)

* *static/*

This is where static files such as CSS, images, etc. are stored.
This is separately mapped in :doc:`the web server config <../installation/index>`.
The content of this folder is created when running the ./upgrade.sh script.

* *static-project/*

This is the base location for all static CSS, images, etc.
This where you maintain these files. The upgrade.sh script copies
files as needed to the *static/* directory.
