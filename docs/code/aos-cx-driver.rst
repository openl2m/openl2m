.. image:: ../_static/openl2m_logo.png

AOS-CX Driver Overview
======================

The Aruba AOS-CX driver is located in *switches/connect/aruba_aoscx/connector.py*.
It uses the *pyaoscx* library provided by Aruba, and available at https://github.com/aruba/pyaoscx/

Documentation is a little sparse, but you can get started at
https://developer.arubanetworks.com/aruba-aoscx/docs/python-getting-started

At this time (June 2022), this drivers does not support LLDP and ARP viewing yet, so that functionality is not available.
Additionally, there are bugs in the PoE class, so this may or may not function.

We implement *get_my_basic_info()* and *get_my_client_data()* by reading various switch REST API classes.

**Basic device configs**

We use calls to the following pyaoscx classes: Device(), Vlan(), and  Interface()

**Arp/Lldp information**

Since LLDP and Arp are not implemented yet, we only read learned ethernet addresses for each Vlan() with the Mac() object.

**Making Changes**

Interface level changes, ie  enable/disable, description, are made with functions of the Interface() object.

PoE changes are made with the PoEInterface() object.

Vlan changes are made by assigning a Vlan() object to an interface via a call to Interface().set_untagged_vlan(Vlan())
