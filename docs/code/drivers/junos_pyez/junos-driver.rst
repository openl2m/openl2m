.. image:: ../../../_static/openl2m_logo.png

Junos Driver Overview
=====================

The Junos driver is located in *switches/connect/junos_pyez/connector.py*.

This driver uses the Juniper Py-EzNC library. We make extensive use of the RPC
capabilities of this library. We parse the responses with the lxml library elements,
using the rpc.find('.//<element name>') functions to build out the various Interface()
and other internal OpenL2M objects.

See the references section for links. Note: the O'Reilly book Chapter 4 is especially useful!

To see the RPC version of commands, run this at the device CLI:

  show xyz | display xml rpc


**Basic device configs**

The function *get_my_basic_info()* is called to read the interface and vlan data of a device.

After opening the connection with *self._open_device()*, we read the facts in *device.facts[]*
to get some info about the type of Juniper device we are talking to.

Next, we issue the xml rpc equivalents of the following commands:

"show interfaces extensive" becomes *rpc.get_interface_information()* Here we parse interface names, types, speeds, etc.

"show poe controller" becomes *rpc.get_poe_controller_information()* This gets us information about PoE power supplies. (if any)
See also https://www.juniper.net/documentation/us/en/software/junos/cli-reference/topics/ref/command/show-poe-controller.html

If we found PoE Power Supplies, then we look for PoE enabled interfaces. The command
"show poe interface" becomes *rpc.get_poe_interface_information()*

Next, we get VLAN data from "show vlans extensive", which becomes *rpc.get_vlan_information()*

And finally, for VRF information we issue the command "show route instance details",
which is *rpc.get-instance-information()*


**ARP/LLDP information**

in *get_my_client_data()* we issue the following RPC commands:

"show ethernet-switching table extensive" becomes *rpc.get_ethernet_switching_table_information()*

"show arp no-resolve" becomes *rpc.get_arp_table_information()*

"show ipv6 neighbors" becomes *rpc.et_ipv6_nd_information*

For LLDP info, we loop through all interfaces, and issue this command:
"show lldp neigbor interface <name>", which is *rpc.get_lldp_interface_neighbors(interface_device=<name>)*


**Making Changes**

To make changes to interfaces, we use the *Config()* class as such:

.. code-block:: bash

  conf = Config(device)
  conf.lock
  conf.load("set command")
  conf.commit_check()
  conf.commit()

The set commands used are as follows:

**Enable/Disable Interface:**

.. code-block:: bash

  delete/set interfaces {name} disable

**Enable/Disable Interface PoE:**

.. code-block:: bash

  delete/set poe interface {name} disable

**Change Interface Vlan - access mode:**

.. code-block:: bash

  delete interfaces {name} unit 0 family ethernet-switching vlan
  set interfaces {name} unit 0 family ethernet-switching vlan members {new-vlan-name}

**Change Interface Vlan - trunk mode:**

.. code-block:: bash

  set interfaces {name} native-vlan-id {new-vlan-id}

**Set Interface Description:**

.. code-block:: bash

  set interfaces {name} description "{description}"

**Clear Interface Description:**

.. code-block:: bash

  delete interfaces {name} description

**VLAN Edit/Delete**

To create a new vlan:

.. code-block:: bash

  set vlans <new_name> vlan_id <new-id>

To rename a vlan:

.. code-block:: bash

  rename vlans <old_name> to <new_name>

To delete a vlan:

.. code-block:: bash

  delete vlans <name>