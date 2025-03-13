.. image:: ../../_static/openl2m_logo.png

=========================
LLDP Neighbor Information
=========================

Below is documented how a driver should set this information, and where it shows.

This typically is loaded when the driver's *get_my_client_data()* function is called. 
I.e. This is when the user click the 'Read Arp/LLDP' button.

The *NeighborDevice()* class  is used to store LLDP information.
See the definition in openl2m/switches/connect/classes.py

Neighbor information is stored for each Interface(), in the *interface.lldp** dictionary,
with key "" as string.

I.e. the *interface.eth* dictionary contains the ethernet address heard on a particular interface.


Storing Neighbor Objects
------------------------

There are a number of functions to help with storing NeighborDevice objects:

*connector.add_neighbor_object(if_name, neighbor)*

    This can be used to add a newly created NeighborDevice() object to an interface name.

*interface.add_neighbor(neighbor)*

    Same as above, but can be used if you already have the Interface() object.

Where It Shows
--------------

This shows under the 'Arp/LLDP' tab, and is rendered in the file *templates/_tab_if_arp_lldp.html*

See the code segment similar to this, inside the 'for each interface' loop:

.. code-block:: python

    # around line 29:
    {% for key,iface in connection.interfaces.items %}

        # around line 97:
        {% if connection.neighbor_count > 0%}
            <td>{# lldp neigbors #}
                {% for lldp_index,neighbor in iface.lldp.items %}
                <div>{{ neighbor|get_lldp_info }}
                </div>
                {% endfor %}
            </td>