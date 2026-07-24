.. image:: ../_static/openl2m_logo.png

=============
Switch Groups
=============

Switch Groups are how OpenL2M gives permissions to Users.

From the **Admin menu** option, go to **Switch Groups** or click the **+ Add** option

Give the Switch Group a **Name**. You can also set a **Display Name** that will override the group name.
This is usefull if using e.g. LDAP to get group membership. See below for more details on this.


Users
-----

Add the **Group Users**. This can be done by hand here by moving user entries to the right.
You can also use LDAP to set group membership. See below for more details on this.


VLAN Allowances
---------------

This sections lets you sets the vlans the users in this group can access on the devices in this group.

You can select **Allow All Vlans**. This permits *access to device and OpenL2M defined* vlans!

.. note::

    If a vlan is defined on the device, but NOT defined in the OpenL2M Admin pages, access is still denied!


If you have already created **Vlans** and **Vlan groups**, you can then select the allowed
vlans/vlangroups to add to this switch group.

On the member switches, users in this group will only be able to manage ports that are (untagged/access-mode) on the Vlans
in the **'Allowed VLANs'** or **'Vlan Groups'** list. Other ports will show, but will not be manageable.


Other Options
-------------

If a switch group is marked **'Read-Only'**, no user (not even admin), can change settings
on the switches in this group. However, if commands are configured, they can be executed.
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

The **Comments** fields is internal only, and can be used to document whatever is needed.


Switch Group Membership
-----------------------

If you have already created switches, at the bottom select the switches to add to this switch group.

You can also added devices (Switches) from the :doc:`Switch configuration page<switch_configs>`, once the Switch Group exists.


**Do not forget to SAVE !**


LDAP Groups
-----------

If you configured :doc:`LDAP login <../installation/ldap>`,
switch groups can be auto-created based on the ldap group
membership for the user. You can then use these groups to assign switches,
vlans, etc. This allows you to manage rights in a central location,
e.g. an active directory domain, or via Grouper integration,
see https://www.internet2.edu/products-services/trust-identity/grouper/

If the switch group is 'auto' created from LDAP, you may want to override the
display name to show a more user-friendly group name.
(OpenL2M Admin -> Switch Groups -> select -> Display Name)
