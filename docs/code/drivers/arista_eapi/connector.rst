.. image:: ../../../_static/openl2m_logo.png

Arista eAPI Driver Overview
===========================

The Arista eAPI is a REST api that allows commands to be executed on the device. The caller can choose
to return the results in 'plain text' or as JSON data (ie "attribute = value" format)

Executing API commands is implemented in *self._run_commands()*

You can execute any "show" command, or any "config" command in this way.

We implement *get_my_basic_info()* and *get_my_client_data()*
by running various 'show' commands via the REST API.

Commands are execute are:

**get_my_basic_info()**

The commands below are returned in JSON format, and parsed as needed. See around line 91.

.. code-block:: bash

    show version    # get various system information.

    show vlan

    show interfaces             # get the interfaces on the device, and their settings.

    show interfaces switchport  # get the layer-2 configuration of interfaces (vlans).

    show interfaces transceiver properties      # get optical transceiver info.

    show port-channel           # info any any port-channels that may be configured.

    show vrf                    # any VRFs that may be configured.



**get_my_client_data()**

The commands below are returned in JSON format, and parsed as needed. See around line 345.

.. code-block:: bash

    show mac address-table          # the layer-2 switching table

    show arp vrf all                # IP-to-Mac info on all VRFs defined.

    show ipv6 neighbors vrf all     # IPv6-to-Mac info on all VRFs defined.

    show lldp neighbors detail      # neighbor device info.



Making Changes
--------------

To make changes, we send the following "config" commands via the eAPI.

Commands are wrapped with the following

.. code-block:: bash

    configure terminal
    <commands sent>
    end


**Enable/Disable Interface:**

.. code-block:: bash

  interfaces {name}
  (no) shutdown


**Enable/Disable Interface PoE:**

Not supported yet! (no test device :-) )


**Set Interface Description:**

.. code-block:: bash

  interface {name}
  description <new description>


**Clear Interface Description:**

.. code-block:: bash

  interfaces {name}
  no description


**Change Interface Vlan - access mode:**

.. code-block:: bash

  interface {name}
  switchport access vlan {new_vlan_id}


**Change Interface Vlan - trunk mode:**

.. code-block:: bash

  interface name
  switchport trunk native vlan {new_vlan_id}



**Set Untagged and 802.1q-tagged vlans**

If interface is set in "access" mode:

.. code-block:: bash

  interface {name}
  switchport mode access
  switchport access vlan {untagged_vlan}
  no switchport trunk native vlan       # not needed, added for config clarity!
  no switchport trunk allowed vlan


or if interface is set to "802.1q-tagged" mode:

.. code-block:: bash

  interface {name}
  switchport mode trunk
  no switchport access vlan       # not needed, added for config clarity!
  switchport trunk native vlan {untagged_vlan}

If "Allow All is set, we added

.. code-block:: bash

  switchport trunk allow vlan all

Else we add the list of allowed vlans:

.. code-block:: bash

  switchport trunk allowed vlan none        # clear all tagged vlans
  switch trunk allowed vlan add x, y, z     # add vlans allowed.



**VLAN Edit/Delete**

To create a new vlan:

.. code-block:: bash

  vlan {vlan_id}
  name {vlan_name}


To rename a vlan:

.. code-block:: bash

  vlan {vlan_id}
  'name {vlan_name}' or 'no name'


To delete a vlan:

.. code-block:: bash

  no vlans {vlan_id}