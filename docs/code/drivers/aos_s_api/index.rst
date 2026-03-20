.. image:: ../../../_static/openl2m_logo.png

===========================
Aruba AOS-S REST API Driver
===========================

We implement an AOS-S driver in the AosCxConnector() class in *switches/connect/aruba_aoss_rest/connector.py*.

This class uses the *RestConnector()* class to use it's generic HTTP functions

We implement *get_my_basic_info()* and *get_my_client_data()* by reading various switch REST API classes.

API endpoints are documented the HPE Support site downloadable file "device-api-v7.0-16.xx.zip" for your firmware version.
Look at the files "services/common/service.html" and "services/wired/server.html" in the "device-rest-api" folder
for your device type (e.g. WC)

Aruba has provided some insighful sample code here: https://github.com/aruba/arubaos-switch-api-python/tree/master/src
