.. image:: ../../../_static/openl2m_logo.png

=======================
Generic REST API Driver
=======================

We implement a generic REST APi driver, to be used by other drivers.
This RestConnector() class is defined in *switches/connect/restconnector.py*.

This implements generic HTTP GET, PUT, POST and DELETE functions.

API login, and setting tokens, cookies, etc. for subsequent request should be performed by the driver classes,
as these differ by REST server implementation.

We provide the 'standard' query parameters, cookie header, and post data options as are defined in the
Python Request package. See https://requests.readthedocs.io/en/latest/ for more.

This class is used at time of writing by:
* :doc:`Aruba AOS-S REST api driver<../aos_s_api/index>`
* :doc:`HPE Comware REST api driver<../hpe_cw_api/index>`
