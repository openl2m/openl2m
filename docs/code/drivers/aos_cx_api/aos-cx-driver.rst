.. image:: ../../../_static/openl2m_logo.png

AOS-CX Driver Overview
======================

The Aruba AOS-CX driver is located in *switches/connect/aruba_aoscx/connector.py*.
It uses the *pyaoscx* library provided by Aruba,
and available at https://github.com/aruba/pyaoscx/

Documentation is a little sparse, but you can get started at
https://developer.arubanetworks.com/aruba-aoscx/docs/python-getting-started

As of November 2023, this library supports all functionality that OpenL2M needs.

Documentation for the API in AOS-CX v10.13 is at
https://www.arubanetworks.com/techdocs/AOS-CX/10.13/PDF/rest_v10-0x.pdf


We implement *get_my_basic_info()* and *get_my_client_data()* by reading various switch REST API classes.

.. note::

    Since the AOS-CX module *pyaoscx* implements objects with the same name as OpenL2M native classes,
    we import those AOS-CX object as *AosCx<OriginalName>* in order to avoid name collisions and confusion.


**Basic device configs**

Implemented in *get_my_basic_info()*:

We make calls to the following pyaoscx classes: Device(), Vlan(), and  Interface(),

We used the discovered data to fill in the appropriate data in the OpenL2M Connection() and Interface() objects.

**Interface Info**

When we get all interface information from as below with get_facts(), all data comes in dictionary form:

.. code-block:: python

    interfaces = Interface.get_facts(session)
    for name, iface in interfaces:
        description = iface['description']
        state = iface['admin_state']
        # etc...

Each item in the result is an interface, but as a dictionary, where the keys are the attributes!


If you instantiate a specific interface object as shown below, the return a Interface() object!
Ie. you can access attributes as object attributes:

.. code-block:: python

    iface = Interface(session, name)
        description = iface.description
        state = iface.admin_state


..

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

**VLAN Edit**

Vlan edits are done use the Vlan() object. This is relatively straight forward.

Creating vlans:

.. code-block:: python

    new_vlan = AosCxVlan(session=self.aoscx_session, vlan_id=vlan_id, name=vlan_name, voice=False)
    try:
        new_vlan.apply()

Edit vlan name:

.. code-block:: python

    vlan = AosCxVlan(session=self.aoscx_session, vlan_id=vlan_id)
    vlan.get()
    vlan.name = vlan_name
    changed = vlan.apply()

Deleting vlans:

.. code-block:: python

    vlan = AosCxVlan(session=self.aoscx_session, vlan_id=vlan_id)
    vlan.delete()


**Fully Populated Objects**

In many cases, you need a fully populated object (Interface(), Vlan() or whatever).
To instantiate this, you need to call the .get() with selector="configuration".

*If you do NOT do this, the object has many attributes missing or empty!*

.. code-block:: python

    session = Session(...)
    session.open(...)
    iface = Interface(session=session, name="1/1/1")
    iface.get(selector="configuration")

See more in the API Documentation under "GET method, selector parameters"