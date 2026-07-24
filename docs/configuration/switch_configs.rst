.. image:: ../_static/openl2m_logo.png

==============
Adding Devices
==============

*Switches* are devices that OpenL2M will try to access.
We support a number of different vendors and access methods.
There are many different *drivers* or *connectors*,
and each has driver/vendor-specific settings.

**Here we describe the "generic" configuration options for each device.
Vendor/Driver-specific settings are described in the following pages.**

From the **Admin menu** option, go to **Switches** or click the **+ Add** option
Below are the common options for each Switch/Device configured in OpenL2M.


Prerequisites
-------------

* create connection profiles (snmp, credentials, etc.)
* create commands, command lists, and command templates as needed.
* create switch groups as needed.


Basic Settings
--------------

Give a **Name** and a **Description**. The name will be shown as the meny item,
whereas the latter will show when you hover of the menu item.

The **IPv4** address can be an actual IP of a resolvable hostname. Note that IPv6 is not yet supported.

Comments are for internal use only.

*Connection Configuration and Napalm Options are described in the driver pages following!*


Commands Configuration
----------------------

Here we set CLI commands to execute on the device.

**Command List** is the list of desired commands. :doc:`See here for more.<commands>`

**Command Templates** can be assigned as well. These allow the users to fill in certain fields of a CLI command.
They are more complicated to configure, :doc:`as is described here<cmd_templates>`.


View Options
------------

The **Default View** setting defines the opening tab when a user clicks on the
switch. Setting this to Details is useful for routers, so that ARP/ND and
LLDP information are loaded immediately. Note that it then may take a little longer
to render the page, due to the extra data that needs to be read from the device.


Access Options
--------------

**Status** - only Active devices are shown in the menu system. This is the default setting.

If a device is marked **'Read-Only'**, no user (not even admin), can change settings.
However, if commands are configured, they can be executed.
This is useful for e.g. routers, or a special switch group for helpdesk users that only need to view data.

The **'Bulk Edit'** setting is enabled by default. If disabled (un-checked),
the switches in this switch group will not allow multiple interfaces to be edited at once.

The **'Poe Toggle All'** setting, if enabled, allows PoE to be toggle even on interfaces the user would
not have access to based on the vlan rules. This is helpful to get support personnel the ability
to reboot VOIP phones, Wireless AP's, etc.

The **'Edit Port Description'** setting, if enabled, allows users to edit the interface description if they have
access based on their vlan rules.

The **'Read Hardware Details'** can be unchecked if you want disable reading hardware info for any devices in this group.
Primarily intended to save time on slower devices. This will skip reading such info as stacking data, hardware module info and more.

Note that this can also be disabled for each individual Switch. And it can be globally disabled by editing configuration.py
and restarting the OpenL2M service.


Other Options
-------------

**External NMS ID** if set, can be used in admin-configurable links. See configuration.py for more details.


Switch Group Memberships
------------------------

Here you can assign a device to a Switch Group, which defines what users can access this device,
and what vlans they can manage. :doc:`See Switch Groups for more<switchgroups>`.


.. note::

    Do not forget to click SAVE !
