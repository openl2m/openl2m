.. image:: ../_static/openl2m_logo.png

============
Installation
============

**To quickly test OpenL2M in your environment, run in a docker container! Please see ./docker/test/README.txt**

The following steps are for a full, production install of OpenL2M. No containers are supported at this time.

**Requirements**

OpenL2M has some requirements:

* Python 3.10 - 3.12 (OpenL2M is developed and tested on v3.12.)
  Note: Python 3.13 or greater are not supported at present!
* net-snmp v5.7 or greater, including net-snmp-devel
* the Python "ezsnmp" package v1.0.0 or greater.
* a web server, with the WSGI capability. We use Nginx in all our documentation.
  Apache may work but is not tested.
* the Django framework, v5.1 or greater.
* a PostgreSQL database, running at least version 13. We use v16 in our testing.
  Note: Ubuntu 24.04 comes with PostgreSql v16. Ubuntu 22.04 comes with v14
  **Ubuntu 20.04 installs v12, and is no longer supported**

**Application Stack Overview**

Once installation is complete, you will have the following application stack
to get a working OpenL2M application:

* Nginx web server
* Gunicorn WSGI Process with Python
* PostgreSQL database (minimum: version 13)

At the end of this page is an image showing the application stack.

**Installation**

OpenL2M is developed and tested in a Ubuntu 24.04 LTS environment.
All instructions are related to that. However, this should work just fine on other
distributions as long as the requirements are met.
(*We no longer develop and test on CentOS/Rocky/AlmaLinux environments.*)

.. note::

  Ubuntu 24.04 LTS comes with Python v3.12 by default. This is NOT yet supported,
  due to SNMP library dependencies on functionality that was removed in v3.12.
  Please use the Alternate Python installation steps to mitigate this by backing down to v3.11.

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
