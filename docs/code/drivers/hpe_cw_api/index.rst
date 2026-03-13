.. image:: ../../../_static/openl2m_logo.png

===========================
HPE Comware REST API Driver
===========================

This drivers uses the HPE Comware REST API, and is located in *switches/connect/hpe_cw7_rest/connector.py*.

The REST API is documented in the NetConf document called "HPE Comware 7 NETCONF XML API Reference".

There are a few useful web pages to help with understanding the API and hence this driver. At time of writing, these are:

NetConf API docs, also shows REST info. Note there is a newer document only available from the HPE Networking Support site:
https://support.hpe.com/hpesc/public/docDisplay?docId=a00127309en_us&docLocale=en_US

H3C Access Controllers REST API Developers Guide:
https://www.h3c.com/en/Support/Resource_Center/EN/Home/Public/00-Public/Technical_Documents/Developer_Documents/Developer_Guides/H3C_Access_Controllers_REST_API-28618/?CHID=1210933


HTTP Methods
------------

We use the request library, see https://requests.readthedocs.io/en/latest/api/

HTTP GET is used to read various API end-points, documented in the NetConf docs described above.
These calls return body data with JSON structures related to interfaces, PoE, etc. We use those as regular Python Dictionaries.

HTTP PUT will update an existing attribute with a new value, but NOT clear out! (ie you cannot set description="").
Success will (typically) return code 204 - No content. You can repeatedly PUT with the same value!

HTTP POST can only be used to create new attributes, ie when they are NOT SET YET!

HTTP DELETE needs to be used to remove an attribute.

Resources
---------

https://www.h3c.com/en/Support/Resource_Center/EN/Home/Switches/00-Public/Developer_Documents/Developer_Guides/NETCONF_API_Developers_Guide-Long/


Making Changes
--------------

In general, when changing interface attributes you need to HTTP PUT to a URL that includes **all** the index attributes
for a specific API endpoint.

In most cases, this is just "IfIndex". And, e.g. for Poe Port status, it includes the PSEID, ie the power supply that services a specific port!

