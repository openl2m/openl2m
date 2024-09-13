.. image:: ../../../_static/openl2m_logo.png

====================
Ethernet Information
====================

Below is documented how a driver should set this information, and where it shows.

This typically is loaded when the driver's *get_my_client_data()* function is called. 
I.e. This is when the user click the 'Read Arp/LLDP' button.

The *EthernetAddress()* class  is used to store MAC address information.
See the definition in openl2m/switches/connect/classes.py

Ethernet information is stored for each Interface(), in the *interface.eth** dictionary, with key "ethernet address" as string.

I.e. the *interface.eth* dictionary contains the ethernet address heard on a particular interface.


Storing Ethernet Addresses
--------------------------

There are a number of functions to help with storing ethernet address:

*connector.add_learned_ethernet_address()*

    This can be used to add an ethernet as string to an interface name, with IPv4 (aka Arp) and Vlan data if known.

*interface.add_learned_ethernet_address()*

    Same as above, but can be used if you already have the Interface() object.

Where does it shows
-------------------

This shows under the 'Arp/LLDP' tab, and is rendered in the file *templates/_tab_if_arp_lldp.html*

See the code segment similar to this, inside the 'for each interface' loop:

.. code-block:: python

    # around line 29:
    {% for key,iface in connection.interfaces.items %}

        # around line 74
        {% if connection.eth_addr_count > 0 %}
            <td>{# known ethernet addresses #}
                {% for macaddr, eth in iface.eth.items %}
                <div>
                    ...
