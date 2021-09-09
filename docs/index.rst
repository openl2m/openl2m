.. OpenL2M - Open Layer 2 Management documentation entry file, created by
   sphinx-quickstart on Mon Sep 16 08:48:33 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: _static/openl2m_logo.png

=====================
Welcome to OpenL2M v2
=====================

Welcome to the documentation for the "Open Layer 2 Management" project.

**What's New:**
v2 implements a new plug-in API that will allow add-on drivers.
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
   switches.rst
   releases/index.rst
   screenshots.rst
   faq.rst
   howto/index.rst
   roadmap.rst
   references.rst


If you are interesting in contributing, writing drivers for new devices, or just learning about the internals of OpenL2M, read the following.

.. toctree::
  :maxdepth: 2
  :caption: For Developers:

  code/index.rst
