.. image:: ../../../_static/openl2m_logo.png

================================
Aruba AOS-CX API Driver Overview
================================

We implement an AOS-CX driver in the AosCxConnector() class in *switches/connect/aruba_aoscx/connector.py*.

This class uses the OpenL2M RestConnector() as the base class.

This is a custom AOS-CX REST connector that performs significantly faster then the
"pyaoscx" package, which also appears to be not thread-safe when running with gunicorn.py

This uses the documented REST API, and allows us to handle any AOS-CX device.
See https://developer.arubanetworks.com/aruba-aoscx/docs/python-getting-started

A good API doc (at time of writing) is at https://arubanetworking.hpe.com/techdocs/AOS-CX/10.16/PDF/rest_v10-0x.pdf

We implement *get_my_basic_info()* and *get_my_client_data()* by reading various switch REST API classes.

.. toctree::
   :maxdepth: 1
   :caption: Here is more information about the Aruba AOS-CX API driver:

   aos-cx-driver.rst
