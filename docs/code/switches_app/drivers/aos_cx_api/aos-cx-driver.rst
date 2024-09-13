.. image:: ../../../../_static/openl2m_logo.png

AOS-CX Driver Overview
======================

The Aruba AOS-CX driver is located in *switches/connect/aruba_aoscx/connector.py*.
It uses the *pyaoscx* library provided by Aruba, and available at https://github.com/aruba/pyaoscx/

Documentation is a little sparse, but you can get started at
https://developer.arubanetworks.com/aruba-aoscx/docs/python-getting-started

As of November 2023, this library supports all functionality that OpenL2M needs. 

We implement *get_my_basic_info()* and *get_my_client_data()* by reading various switch REST API classes.

.. note::

    Since the AOS-CX module *pyaoscx* implements objects with the same name as OpenL2M native classes,
    we import those AOS-CX object as *AosCX<OriginalName>* in order to avoid name collisions and confusion.


**Basic device configs**

Implemented in *get_my_basic_info()*:

We make calls to the following pyaoscx classes: Device(), Vlan(), and  Interface(), 

We used the discovered data to fill in the appropriate data in the OpenL2M Connection() and Interface() objects.


**Arp/Lldp information**

Implemented in *get_my_client_data()*:

Ethernet data is learned per vlan. So we loop through all vlans, and read learned ethernet addresses
for each Vlan() with the Mac() object.

LLDP neighbors are listed per interface, so we loop through each OpenL2M Interface(), 
get the AOS-CX Interface(), and next enumerate the LldpNeighbor() objects on that interface.


**Making Changes**

Interface level changes, ie  enable/disable, description, are made with functions of the Interface() object.

PoE changes are made with the PoEInterface() object.

Vlan changes are made by assigning a Vlan() object to an interface via a call to Interface().set_untagged_vlan(Vlan())
