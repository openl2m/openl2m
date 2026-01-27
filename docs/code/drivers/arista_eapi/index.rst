.. image:: ../../../_static/openl2m_logo.png

===========================
Arista eAPI Driver Overview
===========================

We implement an Arista eAPI driver. At present, this does not yet support PoE, as we do not have a test device that supports PoE!

You will need a configuraton similar to documented here to get your device serving API calls:
https://arista.my.site.com/AristaCommunity/s/article/arista-eapi-101

.. note::

   Once configured, you can explore the eAPI by going to the following URL on an Arista device:

   https://<ip-address/eapi/

   No credentials are needed to look around!

There is a Python package available (pyeapi, see https://github.com/arista-eosplus/pyeapi),
however this requires configuration files to function. This is not compatible with a web app,
so the Arista eAPI driver implements it's own interface to the eAPI.

.. toctree::
   :maxdepth: 1
   :caption: Information about the Arista eAPI driver:

   connector.rst
