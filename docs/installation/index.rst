.. image:: ../_static/openl2m_logo.png

============
Installation
============

**To quickly test OpenL2M in your environment, run in a docker container! Please see ./docker/test/README.txt**

The following steps are for a full, production install of OpenL2M. No containers are supported at this time.

**Requirements**

OpenL2M has some requirements:

* Python 3.10 or greater (OpenL2M is developed and tested on Python 3.11)
* net-snmp v5.7 or greater, including net-snmp-devel
* the Python "easysnmp" package v0.2.5 or greater.
* a web server, with the WSGI capability. We use Nginx in all our documentation.
  Apache may work but is not tested.
* the Django framework, v5.0 or greater.
* a PostgreSQL database, running at least version 12. We use v12 and v14 in our testing.

**Application Stack Overview**

Once installation is complete, you will have the following application stack
to get a working OpenL2M application:

* Nginx web server
* Gunicorn WSGI Process with Python
* PostgreSQL database

At the end of this page is an image showing the application stack.

**Installation**

OpenL2M is developed and tested in a Ubuntu 22.04 LTS environment.
All instructions are related to that. However, this should work just fine on other
distributions as long as the requirements are met.
(*We no longer support CentOS Linux v7 and v8 environments, as we no longer developed and tested on them.*)

.. toctree::
   :maxdepth: 1
   :caption: These are the steps to install OpenL2M:

   database.rst
   openl2m.rst
   api.rst
   gunicorn.rst
   nginx.rst
   nginx-ssl.rst
   ldap.rst
   upgrading.rst
   alt-python.rst


**Application Stack Overview**

.. image:: ../_static/openl2m-application-stack.png
