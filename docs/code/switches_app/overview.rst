.. image:: ../../_static/openl2m_logo.png

=================
Switches Overview
=================

The *switches/* directory contains the main app where nearly all the
functionality is implemented. Here are some details about various parts of this app.

urls.py
-------

In standard Django fashion, here we map the various urls of our app. **We use Class-Based URL mapping**,
as this allows us to take advantage of Django default handling of non-used HTTP methods.

models.py
---------

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


views.py
--------

As is typical in a Django framework application, this is where most of the
work to handle URLs is done. It is also where *Connector()* objects are created to connect to devices.

**All URLs are mapped in** *urls.py* **to classes in** *views.py*

There are three entry points for viewing data on a device:

* the basic view, that shows interfaces, vlans, etc.
* the details view, that shows known ethernet addresses, ARP, IPv6 ND and LLDP Neighbors.
* the command output view.

These 3 are described in the following pages.


Connections
-----------

Connections to the switch are derived from a base Connector() class.
We currently provide several vendor-specific drivers. Each is a sub-class of the Connector() object:

* several based on SNMP.
  This supports HPE/Aruba, HPE/AOS-Cx, Arista, and some Cisco, Juniper, and Netgear and generic switches.
* an Arista eAPI based drivers.
* an Aruba AOS-S REST-API driver.
* an Aruba AOS-CX REST-API driver.
* a HPE Comware REST-API driver.
* a Juniper PyEz-NC based driver.
* read-only demonstration driver based on the Napalm automation framework. Supports most Napalm-supported devices.
* a dummy driver, mostly used to show how the Connector API can be used to fill data, and to test/debug html templates.

See :doc:`Connections and Drivers <../drivers/index>` for more.
