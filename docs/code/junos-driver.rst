.. image:: ../_static/openl2m_logo.png

Junos Driver Overview
=====================

The Junos driver uses the Juniper Py-EzNC library. We make extensive use of the RPC
capabilities of this library. We parse the responses with the lxml library elements,
using the rpc.find('.//<element name>') functions to build out the various Interface()
and other internal OpenL2M objects. See the references section for links. Note:
the O'Reilly book Chapter 4 is especially useful!

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

  delete interfaces {name} unit 0 family ethernet-switching vlan")
  set interfaces {name} unit 0 family ethernet-switching vlan members {vlan-name}")

**Change Vlan - trunk mode:**

.. code-block:: bash

  set interfaces {name} native-vlan-id {vlan-id}

**Set Description:**

.. code-block:: bash

  set interfaces {name} description "{description}"

**Clear Description:**

.. code-block:: bash

  delete interfaces {name} description
