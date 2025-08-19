.. image:: _static/openl2m_logo.png

==========
References
==========

Below are links to various projects that have played a role in the development of OpenL2M.
These are mostly provided to make it easy to get started with understanding,
and potentially developing, OpenL2M.

Documentation
-------------

**Sphinx** is used to handle the ReStructuredText this documentation is written in.
Get started here:  https://docs.readthedocs.io/en/stable/intro/getting-started-with-sphinx.html

We use Sphinx-Design to make life easier: https://sphinx-design.readthedocs.io/en/latest/get_started.html

Python doc string options are nicely described here:
https://stackoverflow.com/questions/3898572/what-is-the-standard-python-docstring-format

RST Tutorial:  https://docs.typo3.org/m/typo3/docs-how-to-document/main/en-us/WritingReST/

RST Directives (ie. tags): https://docutils.sourceforge.io/docs/ref/rst/directives.html

Intro to Sphinx: https://www.writethedocs.org/guide/tools/sphinx/

Using Sphinx: https://www.sphinx-doc.org/en/master/contents.html

Sphinx-specific Directives: https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html


Frameworks and projects
---------------------------

**Django**, the web framework used. See https://docs.djangoproject.com/

**Bootstrap**, the html front-end library used. See https://getbootstrap.com/

Where there are many tutotials about using Bootstrap, a very comprehensive one is at https://www.tutorialrepublic.com/twitter-bootstrap-tutorial/

Additionally, the W3Schools "Introduction to the Bootstrap" is a valuable resource: See https://www.w3schools.com/bootstrap/default.asp

**Django Rest Framework**, used to implement our REST api. See https://www.django-rest-framework.org/

The Netbox project. This is the original project that inspired the birth of OpenL2M :-).

See https://github.com/netbox-community/netboxHP/Aruba vlan management tool. https://sourceforge.net/projects/procurve-admin/

Uninett NAV (Network Adminstration Visualized), at https://nav.uninett.no/
and specifically the SNMP portadmin code at https://github.com/Uninett/nav/tree/master/python/nav/portadmin/snmp

Icons
-----

We use the **Font Awesome** v6 free web icon package: https://fontawesome.com/v6/search


Python
------

Virtual Environments:  https://docs.python.org/3/library/venv.html

Google Python Style Guide:  http://google.github.io/styleguide/pyguide.html

Google Docstrings: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings

Google Doc Style examples:  https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html

pycodestyle documentation: https://pycodestyle.pycqa.org/en/latest/

Flake8 code style checker: https://flake8.pycqa.org/en/latest/user/index.html

Type Hints: https://realpython.com/python-type-checking/


Nginx
-----

Documenation: https://nginx.org/en/docs/


Docker
------

Dockerfile: https://docs.docker.com/reference/dockerfile/

Compose: https://docs.docker.com/compose/

Nginx in docker: https://hub.docker.com/_/nginx


SNMP related
------------

Python EzSNMP, using native Net-Snmp:
See https://github.com/carlkidcrypto/ezsnmp
and the docs at https://carlkidcrypto.github.io/ezsnmp/html/index.html

PySNMPLib, a native Python SNMP stack: https://github.com/pysnmp/pysnmp

MIB browser at
http://cric.grenoble.cnrs.fr/Administrateurs/Outils/MIBS/?oid=1.3.6.1.2.1


Juniper SNMP: https://www.juniper.net/documentation/us/en/software/junos/network-mgmt/topics/topic-map/snmp-mibs-supported-by-junos-os-and-junos-os-evolved.html

Arista SNMNP: https://www.arista.com/en/support/product-documentation/arista-snmp-mibs


Aruba AOS-CX
------------

AOS-CX REST API v10.08 Guide: https://www.arubanetworks.com/techdocs/AOS-CX/10.08/PDF/rest_v10-0x.pdf

The pyasocx library is at https://github.com/aruba/pyaoscx/

AOS-CX SNMP Capabilities are documented here (for v10.14, Sept 2024):
https://www.arubanetworks.com/techdocs/AOS-CX/10.14/HTML/snmp_mib/Content/Chp_SNMP/snm.htm


Junos PyEZ
----------

Juniper documentation is at https://www.juniper.net/documentation/us/en/software/junos-pyez/junos-pyez-developer/index.html
and at https://junos-pyez.readthedocs.io/

Juniper PyEZ library, at https://github.com/Juniper/py-junos-eznc and installable via pip.

"Automating Junos Administration", chapter 4 "Junos PyEZ", O'Reilly books
Ch. 4 is also at https://www.oreilly.com/library/view/automating-junos-administration/9781491928875/ch04.html
The example code for this book can be found at https://github.com/AutomatingJunosAdministration

Example code at https://saidvandeklundert.net/2019-07-04-using-junos-pyez-for-information-gathering/
and https://alexwilkins.dev/index.php/python-pyez/


Napalm
------

The Napalm documentation is at https://napalm.readthedocs.io/

We also use a few community libraries as documented here
https://napalm.readthedocs.io/en/latest/contributing/drivers.html

For Aruba AOS-CX support, we use this: https://developer.arubanetworks.com/aruba-aoscx/docs/installing-arubas-napalm-drivers

For Dell OS10 support, we use this: https://dellos10-napalm.readthedocs.io/en/latest/index.html

For HP Procurve support, we use this: https://github.com/ixs/napalm-procurve

A possible Comware Napalm driver is at https://github.com/firefly-serenity/napalm-flexfabric

Accessibility & Validation
--------------------------

W3 Markup Validator: https://validator.w3.org/

WAVE Browser Extensions: https://wave.webaim.org/extension