.. image:: ../_static/openl2m_logo.png

============
Installation
============

**To quickly test OpenL2M in your environment, run in a docker container! Please see ./docker/test/README.txt**

The following steps are for a full production install of OpenL2M. No containers are supported for production at this time.

**Requirements**

*We recommend you install OpenL2M on Ubuntu 24.04 LTS*

OpenL2M has some requirements:

* Python 3.10 - 3.13 (OpenL2M is developed and tested on v3.12.)
* net-snmp v5.7 or greater, including net-snmp-devel
* the Python "ezsnmp" package v1.0.0 or greater.
* a web server, with the WSGI capability. We use Nginx in all our documentation.
  Apache may work but is not tested.
* the Django framework, v5.1 or greater.
* a PostgreSQL database, running at least version 13. We use v16 in our testing.
  Note: Ubuntu 24.04 comes with PostgreSQL v16. Ubuntu 22.04 comes with v14.
  **Ubuntu 20.04 installs v12, and is no longer supported**

**Application Stack Overview**

Once installation is complete, you will have the following application stack
to get a working OpenL2M application:

* Nginx web server (handled user web requests)
* Gunicorn WSGI Process with Python (processes the request and runs OpenL2M)
* PostgreSQL database (minimum: version 13)

At the end of this page is an image showing the application stack.

**Installation**

OpenL2M is developed and tested in a Ubuntu 24.04 LTS environment.
All instructions are related to that. However, this should work just fine on other
distributions as long as the requirements are met.
(*We no longer develop and test on CentOS/Rocky/AlmaLinux environments.*)

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
