.. image:: ../../../../_static/openl2m_logo.png

================================
Aruba AOS-CX API Driver Overview
================================

We implement an AOS-CX driver in the AosCxConnector() class in *switches/connect/aruba_aoscx/connect.py*.

This class uses the *pyaoscx* library provided by Aruba, and available at https://github.com/aruba/pyaoscx/
See also https://developer.arubanetworks.com/aruba-aoscx/docs/python-getting-started

We implement *get_my_basic_info()* and *get_my_client_data()* by reading various switch REST API classes.

**Update:** as of November 2023, this library supports all functionality that OpenL2M needs.
I.e. **This driver is now fully functional!**

(**Note**: that at the time of this writing (May 2022), Power-over-Ethernet and LLDP functions are not implemented
in the library, so that data is not available in OpenL2M.)


.. toctree::
   :maxdepth: 1
   :caption: Here is more information about the Aruba AOS-CX API driver:

   aos-cx-driver.rst
   powersupplies.rst
