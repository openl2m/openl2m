.. image:: ../_static/openl2m_logo.png

User Authentication
===================

We use the default Django authentication provided in the *django.contrib.auth.views.login* view.
This will render the template from *templates/registration/login.html*.

In *openl2m/settings.py*, we set

.. code-block:: bash

  LOGIN_REDIRECT_URL = 'home'

This forces all logins, re-logins on time-out etc. back to the 'home' url (defined in *openl2m/urls.py*)

Then we enforce login requirements without redirect to a specific page with the
*@login_required(redirect_field_name=None)* decorator for all url handler functions,
except for the 'basic view' in *switches/views.py*, switch_basics()

This allows for bookmarks to specific switches to redirect properly.

**Logging**

We tie into the django signals for user_logged_in/out/failed() in *users/models.py*,
and add Log() entries as needed.

**Logout**

This is handled in *users/views.py*, LogoutView()

**Accounts & Profiles**

The Profile() model is defined in *users/models.py*. This adds fields to the base Django User() object via a 1to1 relationship.
We also receive signals here to handle user account actions, so we can add/update the profile fields as needed.

Finally, in *users/admin.py* we override the default admin page for User(),
and add in the view for both the Profile() and SwitchGroup() to the user view.

**LDAP Authentication**

in openl2m/settings.py, if openl2m/ldap_config.py exists, we import it.
After settings variables for the django ldap module, we then add this to the authentication workflow as such:

.. code-block:: bash

  AUTHENTICATION_BACKENDS.insert(0, 'django_auth_ldap.backend.LDAPBackend')

Ldap authentication now becomes to first one to check, so this now takes care of all the magic!

LDAP group mapping is managed via a signal handler in *users/signals.py*, ldap_auth_handler()

Here we enumerate through the group names for the user, and match them to the

.. code-block:: bash

  settings.AUTH_LDAP_GROUP_TO_SWITCHGROUP_REGEX

expression. Matching ldap groups get created as SwitchGroup() (if needed), and the user is assigned a member of that SwitchGroup().
