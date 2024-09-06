.. image:: ../../../../_static/openl2m_logo.png

---------------
Netmiko for CLI
---------------

When we need to SSH to execute commands on the switch, we call a Netmiko
wrapper class defined in switches/connect/netmiko/execute.py

**Note:** it is possible to implement a complete SSH interface to manage devices.
This could go in a file in switches/connect/netmike/connector.py

The Napalm library attempts to do this, but lacks support for 802.1q, PoE, and more.
