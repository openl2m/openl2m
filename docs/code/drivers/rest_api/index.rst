.. image:: ../../../_static/openl2m_logo.png

=======================
Generic REST API Driver
=======================

We implement a generic REST APi driver, to be used by other drivers.
This RestConnector() class is defined in *switches/connect/restconnector.py*.

This implements generic HTTP GET, PUT, POST and DELETE functions.

This class is used at time of writing by:
* :doc:`Aruba AOS-S REST api driver<../aos_s_api/index>`
* :doc:`HPE Comware REST api driver<../hpe_cw_api/index>`
