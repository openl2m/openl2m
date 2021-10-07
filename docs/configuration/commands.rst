.. image:: ../_static/openl2m_logo.png

==========================
Commands and Command Lists
==========================

Command are 'show' or 'display' commands that can be executed on a switch once a Netmiko profile as been applied.
They are meant to 'show' or 'display' more information about a switch or an interface on the switch that
is not supported in OpenL2M via SNMP. Command Lists are NOT intended to configure a switch.
They are NOT executed in 'enable' or 'system' mode.

After configuring one or more Commands, they can be added to a Command List,
which in turn can be applied to one or more switches.
Switches do not need a Command List, but can only have one Command List applied.

**Commands**

To configure Commands, go to Admin, then go to Commands in the Switches section,
or click the "+ Add" option behind the menu entry.

Each command has a name and an OS. The OS is mostly to easily keep track of commands for various switch platform.
The description is optional.

The command type is either Interface, or Global.

Interface commands require a "%s" somewhere in the command string,
in order to place the interface name in that location. Ie. they pertain to a specific interface.
E.g. the entry "Show Power" with the command string "show power interface %s", when selected
on interface GigabitEthernet2, will be sent as "show power interface GigabitEthernet2"

Global commands are available in the context of the switch, i.e they are system level commands.
E.g. an entry named "Show LLDP" with command string "show lldp neighbor details"
Note that global commands do not need (or use) a "%s"!


**Command Lists**

Command Lists are groupings of commands that can be assigned to switches.

To configure Command Lists, go to Admin, then go to Command Lists in the Switches section,
or click the "+ Add" option behind the menu entry.

Command Lists have a name, a description, and 4 areas for commands:

* *Global commands*
  These are "system level" show or display commands executed in the context of the switch.
  Pick the appropriate commands. All users of a particular switch will be able to execute them.
  These commands are sent literal to the switch, in 'regular' login mode.

* *Interface commands*
  These are "interface level" commands executed in the context of an interface.

* *Global commands for staff*
  These are identical to *Global commands*, only a user needs to have 'Staff' permissions to see and
  be able to run these commands. In the switch view, we will show a select list with 'separators'
  identifying the staff commands.

* *Interface commands for staff*
  These are identical to *Interface commands*, only a user needs to have 'Staff' permissions
  to see and be able to run these commands. In the switch view, we will show a select list with 'separators'
  identifying the staff commands.
