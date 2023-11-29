.. OpenL2M - Open Layer 2 Management documentation entry file, created by
   sphinx-quickstart on Mon Sep 16 08:48:33 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: _static/openl2m_logo.png

=====================
Welcome to OpenL2M v2
=====================

Welcome to the documentation for the "Open Layer 2 Management" project.

OpenL2M is an open source network device management
application designed to allow users with minimal training to perform a set of basic
configuration changes on those devices, with a focus on port or interface (i.e Layer 2) changes.
It does so by providing a consistent web interface
for device management, independent of the underlying vendor.

OpenL2M attempts to address the needs of distributed IT groups managing parts
of a shared distributed layer 2 ("switching") network.

While primarily intended to manage network switches, OpenL2M can handle any device that has some
sort of network API (e.g. SSH, Netconf, REST, etc.)

See a list of features per device class supported :doc:`here.<feature_support>`

OpenL2M is written in Python 3 using the Django framework.
Documentation is written in ReStructured Text format, which is rendered with the Sphinx documentation generator.

**What's New:**

v3.0 introduces a REST API. This allows for remotely making changes to devices without needing to know the underlying vendor.
Read the API section of the documentation for more details.

v2.4 upgrades the Django framework to v4.2 LTS

v2.3 adds support for Juniper Junos devices.

v2.2 adds support for Aruba AOS-CX switches.

v2.1 implements command templates, a controlled method to give users variable input on commands.
This gives tremendous flexibility in giving users in a controlled fashion more visibility into the device.
See the Configuration section for more.

v2.0 implements a new plug-in API for add-on device drivers.
This makes is easy to add support for any kind of network device,
whether the interface is SSH, REST, NetConf, or other methods.
See more in the development section below.

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
   releases/index.rst
   screenshots.rst
   faq.rst
   howto/index.rst
   api/index.rst
   roadmap.rst
   references.rst


If you are interesting in contributing, writing drivers for new devices, or just learning about the internals of OpenL2M, read the following.

.. toctree::
  :maxdepth: 1
  :caption: For Developers:

  code/index.rst


These documents were generated on |today|.
