.. image:: _static/openl2m_logo.png

==========
References
==========

Various projects that have played a role in the development of OpenL2M

**Documentation**

Sphinx is used to handle the ReStructuredText this documentation is written in.
Get started here:  https://docs.readthedocs.io/en/stable/intro/getting-started-with-sphinx.html

Python doc string options are nicely described here:
https://stackoverflow.com/questions/3898572/what-is-the-standard-python-docstring-format

RST Tutorial:  https://docs.typo3.org/m/typo3/docs-how-to-document/main/en-us/WritingReST/

RST Directives (ie. tags): https://docutils.sourceforge.io/docs/ref/rst/directives.html

Intro to Sphinx: https://www.writethedocs.org/guide/tools/sphinx/

Using Sphinx: https://www.sphinx-doc.org/en/master/contents.html

Sphinx-specific Directives: https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html


**Web frameworks and projects**

Django, the web framework used. See https://docs.djangoproject.com/

Bootstrap, the html front-end library used. See https://getbootstrap.com/

Introduction to the Bootstrap framework used for web rendering. See https://www.w3schools.com/bootstrap/default.asp

The Netbox project. This is the original project that inspired the birth of OpenL2M :-).
See https://github.com/netbox-community/netbox

HP/Aruba vlan management tool. https://sourceforge.net/projects/procurve-admin/


**SNMP related**

Python easysnmp, using native Net-Snmp:
See https://easysnmp.readthedocs.io/en/latest/ and
https://github.com/kamakazikamikaze/easysnmp

MIB browser at
http://cric.grenoble.cnrs.fr/Administrateurs/Outils/MIBS/?oid=1.3.6.1.2.1

SNMP Introductions

While there are many, this one has a good basic explanation and includes a
good example of the GetBulk non-repeaters and max-repetitions parameters:
https://www.snmpsharpnet.com/?page_id=30

Using SNMP to discover MAC, IP and Vlan information from switches:
https://www.akips.com/resources?mode=blog;doc=mac_ip_vlan_switch


**Aruba AOS-CX**

AOS-CX REST API v10.08 Guide: https://www.arubanetworks.com/techdocs/AOS-CX/10.08/PDF/rest_v10-0x.pdf

The pyasocx library is at https://github.com/aruba/pyaoscx/


**Junos PyEZ**

Juniper documentation is at https://www.juniper.net/documentation/us/en/software/junos-pyez/junos-pyez-developer/index.html
and at https://junos-pyez.readthedocs.io/

Juniper PyEZ library, at https://github.com/Juniper/py-junos-eznc and installable via pip.

"Automating Junos Administration", chapter 4 "Junos PyEZ", O'Reilly books
Ch. 4 is also at https://www.oreilly.com/library/view/automating-junos-administration/9781491928875/ch04.html
The example code for this book can be found at https://github.com/AutomatingJunosAdministration

Example code at https://saidvandeklundert.net/2019-07-04-using-junos-pyez-for-information-gathering/
and https://alexwilkins.dev/index.php/python-pyez/


**Napalm Automation**

The Napalm documentation is at https://napalm.readthedocs.io/

We also use a few community libraries as documented here
https://napalm.readthedocs.io/en/latest/contributing/drivers.html

For Aruba AOS-CX support, we use this: https://developer.arubanetworks.com/aruba-aoscx/docs/installing-arubas-napalm-drivers

For Dell OS10 support, we use this: https://dellos10-napalm.readthedocs.io/en/latest/index.html

For HP Procurve support, we use this: https://github.com/ixs/napalm-procurve

A possible Comware Napalm driver is at https://github.com/firefly-serenity/napalm-flexfabric


**Icons**

We use several free icon packages:

Font Awesome, with previews https://fontawesome.com/v5/search

Material Design Icons, from https://materialdesignicons.com/ and a preview at https://pictogrammers.github.io/@mdi/font/6.5.95/


**Python**

Virtual Environments:  https://docs.python.org/3/library/venv.html

Google Python Style Guide:  http://google.github.io/styleguide/pyguide.html

Google Docstrings: https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings

Google Doc Style examples:  https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html

pycodestyle documentation: https://pycodestyle.pycqa.org/en/latest/

Flake8 code style checker: https://flake8.pycqa.org/en/latest/user/index.html
