.. image:: ../../_static/openl2m_logo.png

================
Running Commands
================

Regular Commands
----------------

The **class SwitchCmdOutput()** is called when calling 'regular' commands. Ie. the commands that run
on the switch or the interface.

This reads the command-id, and then calls **switch_view()** with the variable *command_id* set.

Template Commands
-----------------

For full 'template' commands, **class SwitchCmdTemplateOutput()** is called.
This parses the POST template variables, and then hands off to **switch_view()**
with the expanded *command_string* variable set

Processing
----------

**switch_view()** will process this as descibed in the previous page
(i.e. since the data may be known at this stage, it would be rendered from cache).

To run the command, *Connector.run_command(command_id, interface_name)*
or *Connector.run_command_string(command_string)* are called.

These in turn call on *Connector._execute_command(command)* to connect to the device and execute the command.

We use the Netmiko framework to establish SSH CLI sessions, and execute the command string as a CLI command.
See :doc:`Netmiko Connector <../drivers/netmiko/index>` for more.

.. note::

    Drivers can override the *_execute_command()* functions. This is e.g. done in some of the REST drivers,
    as they can execute commands via the REST API instead of SSH.



