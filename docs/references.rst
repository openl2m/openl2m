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

Intro to Sphynx: https://www.writethedocs.org/guide/tools/sphinx/

Using Sphynx: https://www.sphinx-doc.org/en/master/contents.html

Sphynx-specific Directives: https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html


**Web frameworks and projects**

Django, the web framework used. See https://docs.djangoproject.com/

Bootstrap, the html front-end library used. See https://getbootstrap.com/

Introduction to the Bootstrap framework used for web rendering. See https://www.w3schools.com/bootstrap/default.asp

The Netbox project. This is the original project that inspired the birth of OpenL2M :-).
See https://github.com/netbox-community/netbox


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


**Aruba AOS-CX**

AOS-CX 10.04 REST v10.04 API Guide: https://support.hpe.com/hpsc/doc/public/display?docId=a00091710en_us


**Napalm Automation**

The Napalm documentation is at https://napalm.readthedocs.io/

We also use a few community libraries as documented here
https://napalm.readthedocs.io/en/latest/contributing/drivers.html

For Aruba AOS-CX support, we use this: https://developer.arubanetworks.com/aruba-aoscx/docs/installing-arubas-napalm-drivers

For Dell OS10 support, we use this: https://dellos10-napalm.readthedocs.io/en/latest/index.html

For HP Procurve support, we use this: https://github.com/ixs/napalm-procurve

A possible Comware Napalm driver is at https://github.com/firefly-serenity/napalm-flexfabric
