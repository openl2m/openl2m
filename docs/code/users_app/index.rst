.. image:: ../../_static/openl2m_logo.png

==============
The users apps
==============

This is the simplest app, located in *users/*. The app that extends the Django native User model.
We add a Profile() class to User. This class is used to add more fields to the native objects.
We also register the signal-handlers to catch notifications when the original objects are modified.

* *models.py*

Here we create a relationship to the User() class, to add new attributes to them.

The Profile() class defines the one-to-one relationship to the original Django User() object.
It adds the severals attributes to the User() object (e.g. the 'Read-Only' flag), and handles the proper signals for creation and updating.

* *admin.py*

Here we create a custom admin view for the above expanded User() object. We also define a so-called "inline"
for the Profile object, and then add this to the User admin view. We register this as the handler
in the custom "admin_site" that was created in the projects' openl2m/admin.py

At the top of this file, we create the "inline" object that represent the 'inline add-on view' of
the User() extensions we created in models.py.

When we then define the custom MyUserAdmin(), we use this object as the 'inline' variable,
which in effect adds those objects to the admin portion of the User() model.

At the bottom, we register the admin class for the User() objects. Note that we
use the custom "admin_site" from the project defined in openl2m/

See these additional documents to learn about we add fields to the User and Group models:

* https://docs.djangoproject.com/en/2.2/topics/auth/customizing/#extending-the-existing-user-model

* https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html

* https://docs.djangoproject.com/en/2.2/topics/signals/

* https://docs.djangoproject.com/en/2.2/ref/signals/#django.db.models.signals.pre_save
