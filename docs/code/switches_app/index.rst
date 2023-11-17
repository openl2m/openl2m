.. image:: ../../_static/openl2m_logo.png

================
The switches app
================

The switches/ directory contains the main app where nearly all the
functionality is implemented. Most of the rest of this document describes
various aspects of this app.

**urls.py**
In standard Django fashion, here we map the various urls of our app.


**models.py**
We define a number of classes/objects here.


**Choices**

Several models, ie Django objects defined in models.py, have a list of "choices"
defined in the class definition. These choices are visible in the admin interface,
e.g. when you create a new SNMP Profile.

If you want to refer to these choices from a template (ie on the web page),
you can use the format model.get_*fieldname*_display,
where *fieldname* is the name of the field in the model that has choice.
Eg. the Log() object defined in models.py, has attributes called
'type' and 'action'. These fields have a list of choices
that show several fields ("View", "Change", "Error", "Warning").

To show these values in the log view template, see   templates/_tab_logs.html,
we use the format  {{ l.get_type_display }}  and   {{ l.get_action_display }}

See https://docs.djangoproject.com/en/dev/ref/models/fields/#field-choices
This statuses  "For each model field that has choices set, Django will add a
method to retrieve the human-readable name for the field’s current value.
See get_FOO_display() in the database API documentation."


**views.py**
As is typical in a Django framework application, this is where most of the
work to handle urls is done. Please read :doc:`Views <views>`


**Connections**

Connections to the switch are derived from a base Connector() class.
We currently provide several sub-connectors (sub-classes): several based on SNMP,
a Juniper PyEz-NC based driver, a REST-API based connector for the Aruba AOS-CX line of devices,
and a read-only driver based on the Napalm automation framework.


See :doc:`Connections <connections>` for more.


**Netmiko for CLI**

We use the Netmiko framework to establish SSH CLI sessions, and execute CLI commands.

See :doc:`Netmiko Connector <netmiko>` for more.


.. toctree::
   :maxdepth: 1
   :caption: Here is what is available at this time:

   connections.rst
   netmiko.rst
   snmp.rst
   views.rst
   vendor_specific.rst
   napalm.rst
