.. image:: ../_static/openl2m_logo.png

============
Installation
============

**Requirements**

OpenL2M has some requirements:

* Python 3.8 or greater (OpenL2M is developed and tested on Python 3.10)
* net-snmp v5.7 or greater, including net-snmp-devel
* the Python "easysnmp" package v0.2.5 or greater.
* a web server, with the WSGI capability. We use Nginx in all our documentation.
  Apache may work but is not tested.
* a PostgreSQL database, running at least version v9.6. We use v12 and v10.17 in our testing.
* the Django framework, v3.2 or greater.

**Application Stack Overview**

Once installation is complete, you will have the following application stack
to get a working OpenL2M application:

* Nginx web server
* Gunicorn WSGI Process with Python
* PostgreSQL database

At the end of this page is an image showing the application stack.

**Installation**

OpenL2M v2.0 is developed and tested in a Ubuntu 20.04 LTS environment.
(Previous versions were developed and tested in CentOS Linux v7 and v8 environments.)
All instructions are related to that. However, this should work just fine on other
distributions as long as the requirements are met.

.. toctree::
   :maxdepth: 1
   :caption: These are the steps to install OpenL2M:

   database.rst
   openl2m.rst
   gunicorn.rst
   nginx.rst
   nginx-ssl.rst
   tasks.rst
   ldap.rst
   upgrading.rst
   alt-python.rst


**Application Stack Overview**

.. image:: ../_static/openl2m-application-stack.png
