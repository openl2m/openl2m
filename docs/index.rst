.. OpenL2M - Open Layer 2 Management documentation entry file, created by
   sphinx-quickstart on Mon Sep 16 08:48:33 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: _static/openl2m_logo.png

=======================
Welcome to OpenL2M v3.1
=======================

Welcome to the documentation for the "Open Layer 2 Management" project.

OpenL2M is an open source network device management
application designed to allow users with minimal training to perform a set of basic
configuration changes on those devices, with a focus on port or interface (i.e Layer 2) changes.
It does so by providing a consistent WebUI and REST API
for device management, independent of the underlying vendor.

OpenL2M attempts to address the needs of distributed IT groups managing parts
of a shared distributed layer 2 ("switching") network.

While primarily intended to manage network switches, OpenL2M can support any device that has some
sort of network API (e.g. SNMP, SSH, Netconf, REST, etc.) through an extendable internal driver class.

See a list of features per device class supported :doc:`here.<feature_support>`

For quick testing of OpenL2M, we provide `Docker Compose configuration files. <https://github.com/openl2m/openl2m/tree/main/docker/test>`_

OpenL2M is written in Python 3 using the Django framework.
Documentation is written in ReStructured Text format, which is rendered with the Sphinx documentation generator.

Click here to :doc:`See What Is New <what_is_new>`!


.. toctree::
   :maxdepth: 1
   :caption: Contents:

   introduction.rst
   using/index.rst
   installation/index.rst
   configuration/index.rst
   switch_requirements.rst
   feature_support.rst
   switches.rst
   screenshots.rst
   faq.rst
   howto/index.rst
   api/index.rst
   what_is_new.rst
   releases/index.rst
   docker.rst
   roadmap.rst
   references.rst
   credits.rst


If you are interesting in contributing, writing drivers for new devices, or just learning about the internals of OpenL2M, read the following.

.. toctree::
  :maxdepth: 1
  :caption: For Developers:

  code/index.rst


These documents were generated on |today|.
