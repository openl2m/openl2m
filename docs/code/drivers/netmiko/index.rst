.. image:: ../../../_static/openl2m_logo.png

================
SSH CLI commands
================

CLI commands are implemented in the Connector() class by using the Netmiko library.
This provides standard SSH access into a device.

Predefined CLI commands are run by calling *Connector().run_command()*,
whereas form template input commands are calling *Connector().run_command_string()*.

Both functions then call *Connector()._execute_command()* to execute the SSH command.

Drivers can override the *self.execute_command()* functionality to implement their own
mechanism to execute CLI commands on a device.

An example if this is the Arista eAPI driver, in switches/connect/arista_eapi/connector.py,
the *_execute_command()* function. This uses the eAPI in "text" mode to run a command.
Note: for this device type, this is significanly faster then the normal SSH implementation via Netmiko.

**Note:** it is possible to implement a complete SSH interface to manage devices.
The Napalm library attempts to do this, but lacks support for 802.1q, PoE, and more.
This exercise is left to the reader...


