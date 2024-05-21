.. image:: ../_static/openl2m_logo.png

==============
The Basic view
==============

When you click on a device, we will read all sorts of data from the device (depending on the vendor driver!).
This can take a while; on stacked devices we have seen this take 30-45 seconds for a 5 or 6 member stack.
Please be patient!

Once data has been retrieved, the basic view will open up, with the following elements.

Top Menu Banner
---------------

.. image:: ../_static/device-menu-bar.png

The banner bar shows the device name on the left. This may be preceded by one or more icons (configurable by the admin),
which would be links to external systems with more information about the device. E.g. you may see a link to the
Network Management System.

The entry in the center, |device-arp-lldp-button|, will get you a real-time read of the ethernet
tables (MAC address) and LLPD neighbors of the device. If the device is a router, ARP entries for IPv4 will also be shown.

.. |device-arp-lldp-button| image:: ../_static/device-arp-lldp-button.png

On the right, |device-reload-button|, does exactly that! This forces a complete refresh of all device data.

.. |device-reload-button| image:: ../_static/device-reload-button.png

|save_warning|  If you have made changes that require saving the config, an additional option to save the config
will appear on the right with a warning icon in front! Click it to save the running config to the device startup config.
(I.e. this is a 'write mem'!) When completed, that option will disappear.

.. |save_warning| image:: ../_static/device-save-changes.png


The Tabs
--------

.. image:: ../_static/device-menu-tabs.png

Below the bar are the tabs. The default tab is the **Interfaces** tab,
containing the visible interfaces on the device. If you have the ability to
manage any of the interfaces, they will be listed with the proper forms
to allow changing the configuration.

Additionally, you will see tabs with device **Information**, and OpenL2M
**Activity** logs for this device. If configured, there may even be a tab
for **Commands**.

Interfaces Tab
--------------

|interfaces_tab|

.. |interfaces_tab| image:: ../_static/interfaces-tab.png

In the Interfaces tab, the following fields are shown:

* **Name**

If the interface is enabled, the name will show on a green background.
If Link is UP, it will be brighter green, if link is DOWN, a somewhat lighter
green color. If the interface is disabled, the background will be red!
(Note these are the default colors. They are admin-configurable, so your mileage may vary!)

Note that the interface name can be preceded by one or more images.
If so, these are links to external systems, such as your Network Management
System. This is configured by the admin.

Interface names can also have several icons behind them. They are:

.. raw:: html

  <i class="fas fa-ellipsis-v" aria-hidden="true"></i>

This means the interface is in trunking or 802.1Q tagged mode.
Hovering over the icon will show the tagged Vlans on this port.

.. raw:: html

  <i class="fas fa-link" aria-hidden="true"></i>

This means the interface is an LACP bridge-aggregate interface, or a member of an LACP
aggregation interface. Hovering over the icon will either show the member interfaces
for a virtual aggregate interface, or for a physical interface the bridge aggregate it is part of.

.. raw:: html

  <i class="fas fa-phone" aria-hidden="true"></i>

This means the interface has a voice vlan defined on it. This is Cisco
specific. Hovering over the icon will
show the Voice Vlan.

.. raw:: html

  <i class="fas fa-cogs" aria-hidden="true"></i>

This means the interface is in routed mode (i.e. layer 3).
Routed Mode interfaces can not be managed.

**Enabling or Disabling the Interface**

|disable_interface|

If you want to Disable a currently enabled interface, click on the interface name on the left side.
In the warning box, select OK. To enable a disabled port, do the same!

.. |disable_interface| image:: ../_static/disable-interface.png


* **Link**

If the interface is enabled, and link established, this will show the link speed in Mbps. A dash indicates no link.

* **Vlan**

The current 'PVID' or 'untagged' vlan of the port will be shown.

.. image:: ../_static/vlan-list.png

Click the drop-down arrow next to the current untagged vlan, and select the
new untagged vlan. You will only see vlans you are allowed to change to.
Click the 'Change' button to apply the new untagged vlan. Note this may take a
little while, so please be patient.

In some cases, the interface is on a VLAN that is not defined on the device
(due to backend configurations; this should not happen in properly configured devices!)
In that case, this will show as "<vlan id> - Not Defined"

* **PoE**

If Power-over-Ethernet is enabled on capable devices,
the interface PoE status will be indicated in this field. The power drawn will also be listed,
If we can read it from the device. An example of the PoE display of enabled
port serving about 9 Watts of power is:

.. image:: ../_static/poe-powered-port.png

Here are the meanings of the various icons used in the PoE section:

|poe_enabled| This means PoE is enabled, but not serving power.

.. |poe_enabled| image:: ../_static/poe-enabled.png

|poe_serving| This means PoE is serving power. Depending on vendor, we can also show
the power consumed by the device on this port.

.. |poe_serving| image:: ../_static/poe-serving.png

|poe_fault| This means PoE is enabled, and there is a fault on the port.

.. |poe_fault| image:: ../_static/poe-fault.png

|poe_disabled| This means PoE is disabled on this port.

.. |poe_disabled| image:: ../_static/disabled.png

To change state, simply click on the Disabled or Enabled icon to change the power state of the port.

|poe_toggle| Click this icon to toggle the power off,
and then on again after a short wait (5 seconds by default, but admin configurable)
Note this only shows for port with power enabled.

.. |poe_toggle| image:: ../_static/down-up.png


* **Description**

This is the current interface description. If you are allowed to change the description,
type in the new text, and hit 'Change'.

* **Commands**

If defined by the admin, there will be a list of 'show' commands you can issue **for this interface**.

|commands|  Select the command, and click on 'Run Command'. Be patient, and the page will refresh will all current data,
but with a new active 'Command Output' tab showing the results of the command. Continue navigating as usual.

.. |commands| image:: ../_static/commands.png


Bulk Edit Tab
-------------

|bulk_edit_tab|

.. |bulk_edit_tab| image:: ../_static/bulk-edit-tab.png

If permissions allow, users will see the Bulk Edit tab. This shows the Bulk Edit form.
This form allows you to apply a variety of changes at once to several interfaces.

.. image:: ../_static/bulk-edit-form.png

* You can toggle the interface up/down state (a admin-down interface will be brought up, and vice versa,
  an up interface will go admin-down, all at once!)
* You can change the interface (untagged) vlan
* You can change or append to the interface description.
* You can choose to either change the PoE state (PoE Enabled to Disabled, and PoE Disabled to Enabled),
  or on interfaces with power enabled, 'toggle' power down, and back up (with an admin configurable wait time)
  Note this is done serially, so if you perform this on many interfaces at once, it will take some time!
  Please be patient!

Fill in the form, then select the interfaces you want to apply this to.

**To apply the change now**, click the "Update Selected Interfaces NOW" button,
and your changes will be applied. Please be patient!


Device Information Tab
----------------------

|device_information_tab|

This shows a series of information about the device. Depending on the device and what is supported in the driver,
this can include items such as model, firmware,serial numbers, vlans defined on device, PoE power supply info, stacking info,
IP(v4) addresses of the device, and more.

E.g.:

|device_ip_poe_info|

|device_stacking_info|

 On properly configured Cisco devicees (:doc:`see Faq <../faq>`), we can show recent log entries:

|cisco_log_entries|

.. |device_information_tab| image:: ../_static/device-information-tab.png
.. |device_stacking_info| image:: ../_static/device-stacking-info.png
.. |device_ip_poe_info| image:: ../_static/device-ip-and-poe-info.png
.. |cisco_log_entries| image:: ../_static/cisco-log-entries.png


Activity Logs Tab
-----------------

|activity_logs_tab|

This will show recent OpenL2M activity on this device. I.e. recent changes using OpenL2M will be
listed here by user and time.

This does *not* show configuration changes applied through other methods, not does this
show device logs! (You could, however, create a command that shows the last N log entries.)

Note that admins have full OpenL2M activity log access, as documented elsewhere.

.. |activity_logs_tab| image:: ../_static/activity-logs-tab.png


Commands Tab
------------

|switch_commands_tab|

This tab will only show if 'global' device-level commands are configured by the admin.

This tab will give a simple form with some 'global' show commands you can execute on the device.
Select a command, click on 'Run Command', and be patient!

|command_output_tab|

When complete, the page will refresh and a new 'Command Output' tab will show the output from the device.


.. |switch_commands_tab| image:: ../_static/switch-commands-tab.png
.. |command_output_tab| image:: ../_static/command-output-tab.png



Command Templates Tab
---------------------

.. image:: ../_static/command-templates-tab.png

On devices that have Command Templates associated, this tab will show a list of one or more
Command Templates names. The name, and the associated description
hover-over text, should explain what the command can be used for.

.. image:: ../_static/command-templates.png

Once you click on the name, the form with the associated input fields will be showing.

.. image:: ../_static/command-template-form.png

Once the user fills in the form, and clicks Run, the data will be validated according the any regular expression set.
If all matches, the command will run on the device.

|command_output_tab|

When complete, the page will refresh and a new 'Command Output' tab will show the output from the device.


Warnings/Errors Tab
-------------------

|warnings_errors_tab|

This tab will only show if warnings or errors were found at some point.

.. |warnings_errors_tab| image:: ../_static/warnings-errors-tab.png

|warnings|

The content of this tab will show a variety of warnings and non-critical errors discovered.
Note that these findings are also logged.

.. |warnings| image:: ../_static/warnings.png
