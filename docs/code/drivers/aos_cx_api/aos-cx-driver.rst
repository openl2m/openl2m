.. image:: ../../../_static/openl2m_logo.png

AOS-CX Driver Overview
======================

The Aruba AOS-CX driver is located in *switches/connect/aruba_aoscx/connector.py*.
It uses the OpenL2M RestConnector() class to implement the API, thus it inherits from *switches/connect/restconnector.py*.

Documentation for the REST API in AOS-CX v10.13 is at
https://www.arubanetworks.com/techdocs/AOS-CX/10.13/PDF/rest_v10-0x.pdf

REST endpoints (calls) may need a "depth" parameter, that indicates how deep (recursive)
you want the return data of a particular object.


API Login
---------

REST Login is a two step process, performed in the function *_open_device()*

First, a HTTP GET call to *<host-or-ip>/rest*. This returns the list of api versions supported in a dictionary.
We use the latest version (*['latest']['version']*), and it's URI endpoint from *['latest']['prefix']*,
stored in *self.api_prefix*

Then all subsequent calls to endpoints are URI's below the URL *https://<host-or-ip>/{api_prefix}/*

For REST api login, we then call the *login* endpoint (e.g. *https://<host-or-ip>/10.13/login*) with an
HTTP POST with JSON form data containing the *username* and *password* fields.

.. code-block:: python

    # around line 1320:

    # auth data is sent in a form post
    data = {
        "username": f"{self.switch.netmiko_profile.username}",
        "password": f"{self.switch.netmiko_profile.password}",
    }
    retval = self._post(path="login", data=data, headers=headers, message="API LOGIN")

Upon success, we store the cookies and CSRF tokens, and are ready for other API calls.


API Logout
----------

*_close_device()* simply performs a POST to *logout* without parameters
(e.g. *https://<host-or-ip>/10.13/logout*)

Note that the session cookies are still set for this call, but are invalid after completion!


Basic Device Config
-------------------

In *get_my_basic_info()* we make calls to the following REST endpoints with HTTP GET:


*system?depth=1* - read basis system info such as version, model, etc.

*system/subsystems?depth=2* - reads the basic hardware info. We do this get information about the PoE Power Supplies,
which is available for "chassis" type entries returned from this call. Returns a dictionary of data similar to below
(some fields skipped). This returns all possible devices in a virtual stack, so we look at the 'state' field for
presence of hardware.

.. code-block:: python

    subsystems = {
        'chassis,1': {
            'poe_power': {'available_power': 370,
                    'drawn_power': 61.1,
                    'failover_power': 0,
                    'power_status_refresh_timestamp': 22430,
                    'power_status_update_timestamp': 22430,
                    'redundant_power': 0,
                    'reserved_power': 66.7999999999999},
            'power_supplies': '/rest/v10.13/system/subsystems/chassis,1/power_supplies',
            'product_info': {
                ...
                'part_number': 'JL660A',
                'product_description': '6300M 24-port HPE Smart Rate 1/2.5/5GbE Class 6 PoE and 4-port SFP56 Switch',
                'product_name': '6300M 24SR5 CL6 PoE 4SFP56 Swch',
            },
            'state': 'ready',
        },


Based on the "poe_power" entry, we add a simulated 'PoE Power Supply', even though that is really part of the main 'power_supplies'.

We then call a HTTP GET to read "power_supplies" for this entry: we call *system/subsystems/chassis,1/power_supplies?depth=2*
This returns something like this:

.. code-block:: python

    {
    '1/1': {'characteristics': {'instantaneous_power': 134, 'maximum_power': 680},
         'identity': {'airflow': 'F2B',
                      'description': 'Aruba X372 54VDC 680W PS',
                      'hardware_rev': '10',
                      'input_voltage_high': 240,
                      'input_voltage_low': 100,
                      'model_number': '0957-2475',
                      'product_name': 'JL086A',
                      'serial_number': 'xxxx',
                      'voltage_type': 'AC'},
         'status': 'ok'},
        ...

This is then added to the hardware environment as a StackMember() object.


*system/vlans?depth=2* - read VLAN data. Note that we also store the direct REST endpoint for vlans.
This is used to manipulate vlans. And, ehternet information is loaded per vlan, so we store "macs_uri"
and "static_macs_uri" sub-endpoints to read during ethernet discovery.

.. code-block:: python

    v.uri = "/system/vlans/{vlan_id}"
    v.macs_uri = vlan["macs"]
    v.static_macs_uri = vlan["static_macs"]

*system/vrfs?depth=2* - read VRF info.

*system/interfaces?depth=2* - get interface information. We read and assign various attributes.
Among this, we read the "lldp_neighbors" attribute and assigned to "interface.lldp_uri".
This is used to read LLDP Neighbors (see below).

*system/vsx?depth=2* - read Virtual Stacking info


Arp/Lldp Information
--------------------

Implemented in *get_my_client_data()*

Ethernet data is learned per vlan. So we loop through all vlans, and read learned ethernet addresses
for each Vlan() with the "macs_uri" learned above. At present, we do not use "static_macs_uri" as we are not
interested in statically coded ethernet addresses.

LLDP neighbors are listed per interface, so we loop through each OpenL2M Interface(),
and call *interface.lldp_uri?depth=2* to get neighbor information.


Hardware Info
-------------

We can read more hardware info from this endpoint:

*system/subsystems?depth=2* - currently not used, get additional hardware info.


Interface Changes
-----------------

Interface level changes, ie  enable/disable, description, Vlan changes, PoE changes, etc. are made by making
HTTP PATCH calls to endpoints with properly JSON formatted PATCH/POST form data.

Note that all functions need to create a "url safe" version of the interface name, as this is part of the URI.
This is done with

.. code-block:: python

    if_name_url = urllib.parse.quote(interface.name, safe="")


Interface changes in **set_interface_admin_status()**, **set_interface_description()**, **set_interface_untagged_vlan()**
all call *system/interfaces/{if_name_url}* with a self-explanatory post dictionary.

Interface PoE calls a slightly different endpoint, with similar post dictionary:

**set_interface_poe_status()** calls *system/interfaces/{if_name_url}/poe_interface*

**set_interface_vlans()**

Setting tagged and untagged vlans is handled slightly different. First we read (HTTP GET) *all* modifiable attributes
of the interface with *system/interfaces/{if_name_url}?selector=writable*. Note the **selector** component.

Then we set the mode (*vlan_mode*), untagged vlan (*vlan_tag*), and tagged vlans (*vlan_trunks*) and write
the complete structure back to the device with an HTTP PUT call to *system/interfaces/{if_name_url}*


VLAN Edit
---------

Creating vlans is a HTTP POST to *system/vlans* with the complete post form data for a new vlan.

Editing a vlan name is an HTTP PATCH to *system/vlans/{vlan_id}* with proper form data.

Deleting a vlan is a simple HTTP DELETE to *system/vlans/{vlan_id}*


Saving The Config
-----------------

In **save_running_config()**, this is performed by an HTTP PUT to *fullconfigs/startup-config?from={api_prefix}/fullconfigs/running-config*

*api_prefix* is found during the login section (see login), and is the current API version used.
