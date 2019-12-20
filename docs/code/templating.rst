.. image:: ../_static/openl2m_logo.png

Templating
==========

In normal Django fashion, templates are used to render various data to the web browser.
We choose to implement a "central" template directory, in *templates/*
This is configured in *openl2m/settings.py* as:

.. code-block:: bash

  TEMPLATES = [
    {
        ...
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        ...
    }

Note that we still allow templates in app-specific sub-directories (APP_DIRS = True).

From *switches/view.py* we call then call these templates to render the pages.

**The base.html template**

This is the main template that defines the screen layout of all others. It is included
in all other templates. This template defines the HTML headers, includes the various
script files, and defines the template tags {% block content %}{% endblock %}

This tag that can be overwritten in other templates, and is the placeholder for
the content in individual pages.

**Static files**

We store static images, javascript, etc in */project-static/*.
`See Django docs on static files here. <https://docs.djangoproject.com/en/2.2/howto/static-files/>`_

The upgrade.sh script moves these to the */static/* location as needed.

We use a "context preprocessor" to get access to Python variables inside the template engine.
In the settings file, we add the following function to map those variables:

.. code-block:: bash

  TEMPLATES = [
    ...
    'switches.context_processors.add_variables',
    ...
    ]

This means we use the switches/context_processors.py file, and the add_variables() function
map data from Python to templating.


**Template tags**

In some templates, we use 'template tags'. Simply put, these are python functions that
can be called from the template engine. Template tags are stored in
*switches/templatetags/helpers.py* and can be included in templates with {% load helpers %}
Note that *each* template needs to load the helper!

`See more about template tags here.
<https://docs.djangoproject.com/en/2.2/howto/custom-template-tags/>`_

We use several important functions to get strings rendered in the helpers files.
Notably are the get_*_nms_link() functions, where we have to render based on objects
passed from the template, and strings that are django templates. We create the html
using render().

Additionally, get_lldp_capabilities_icon() produces html code, and we pass that back
via mark_safe() to make sure it does not get marked up, i.e. gets interpreted as html.
