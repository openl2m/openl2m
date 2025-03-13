.. image:: ../../../_static/openl2m_logo.png

==========================
Junos PyEZ Driver Overview
==========================

A Juniper 'netconf' driver based on the Juniper PyEZ module is implemented in the PyEZConnector()
class in *switches.connect/junos_pyez/connector.py*.

The *junos-eznc* library from PyPI is available at https://github.com/Juniper/py-junos-eznc

.. note::

   The current drivers supports Junos "ELS" device, ie. devices with Enhanced Layer2 Software.
   This unifies commands. We have not tested against non-ELS device, such as some MX product line.


.. toctree::
   :maxdepth: 1
   :caption: Here is more information about the Juniper JunOS PyEZ Netconf driver:

   junos-driver.rst
