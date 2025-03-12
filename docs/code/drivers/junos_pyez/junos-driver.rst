.. image:: ../../../_static/openl2m_logo.png

Junos Driver Overview
=====================

The Junos driver is located in *switches/connect/junos_pyez/connector.py*.
This driver uses the Juniper Py-EzNC library. We make extensive use of the RPC
capabilities of this library. We parse the responses with the lxml library elements,
using the rpc.find('.//<element name>') functions to build out the various Interface()
and other internal OpenL2M objects. See the references section for links. Note:
the O'Reilly book Chapter 4 is especially useful!

To see RPC version of commands:

  show xyz | display xml rpc


**Basic device configs**

We issue the xml rpc equivalents of the following commands:

"show interfaces extensive" becomes *rpc.get_interface_information()*

"show poe controller" becomes *rpc.get_poe_controller_information()*
See also https://www.juniper.net/documentation/us/en/software/junos/cli-reference/topics/ref/command/show-poe-controller.html

"show poe interface" becomes *rpc.get_poe_interface_information()*

"show vlans extensive" becomes *rpc.get_vlan_information()*

**Arp/Lldp information**

We use the following commands:

"show ethernet-switching table extensive" becomes *rpc.get_ethernet_switching_table_information()*

"show arp no-resolve" becomes *rpc.get_arp_table_information()*

"show lldp neigbor interface <name>" becomes *rpc.get_lldp_interface_neighbors(interface_device=<name>)*

**VRF information**

We issue this command:

"show route instance details" becomesn *rpc.get-instance-information()*


**Making Changes**

To make changes to interfaces, we use the *Config()* class as such:

.. code-block:: bash

  conf = Config(device)
  conf.lock
  conf.load(set-command)
  conf.commit_check()
  conf.commit()

The set commands used are as follows:

**Enable/Disable:**

.. code-block:: bash

  delete/set interfaces {name} disable

**Enable/Disable PoE:**

.. code-block:: bash

  delete/set poe interface {name} disable

**Change Vlan - access mode:**

.. code-block:: bash

  delete interfaces {name} unit 0 family ethernet-switching vlan
  set interfaces {name} unit 0 family ethernet-switching vlan members {new-vlan-name}

**Change Vlan - trunk mode:**

.. code-block:: bash

  set interfaces {name} native-vlan-id {new-vlan-id}

**Set Description:**

.. code-block:: bash

  set interfaces {name} description "{description}"

**Clear Description:**

.. code-block:: bash

  delete interfaces {name} description

**VLAN Edit/Delete**

We use the following commands:

"set vlans <new_name> vlan_id <new-id>"  to create a new vlan.

"rename vlans <old_name> to <new_name>"  to rename a vlan.

"delete vlans <name>"  to delete a vlan.