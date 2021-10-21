.. image:: ../_static/openl2m_logo.png

=============
Switch Groups
=============

Switch Groups are how OpenL2M gives permissions to Users.

From the Admin menu option, go to Switch Groups or click the "+ Add" option

Give the Switch Group a name. If you have added switches and vlans,
you can then select the switches and vlans/vlangroups to add to this switch group.

On the selected switches, selected users will only be able to manage ports that are on the Vlans
in the 'Allowed VLANs' or 'Vlan Groups' list. Other ports will show, but will not be manageable.

If you check 'Allow All VLANs', regardless of the above settings, users can access all vlans defined on the device.

If a switch group is marked Read-Only, no user (not even admin), can change settings
on the switches in this group. However, if commands are configured, they can be executed.
This is useful for e.g. routers, or a special switch group for helpdesk users that only need to view data.

The Bulk Edit setting is enabled by default. If disabled (un-checked),
the switches in this switch group will not allow multiple interfaces to be edited at once.

The Poe Toggle All setting, if enabled, allows PoE to be toggle even on interfaces the user would
not have access to based on the vlan rules. This is helpful to get support personnel the ability
to reboot VOIP phones, Wireless AP's, etc.

The Edit Port Description setting, if enabled, allows users to edit the interface description if they have
access based on their vlan rules.

**LDAP Groups**

If you configured :doc:`LDAP login <../installation/ldap>`,
switch groups can be auto-created based on the ldap group
membership for the user. You can then use these groups to assign switches,
vlans, etc. This allows you to manage rights in a central location,
e.g. an active directory domain, or via Grouper integration,
see https://www.internet2.edu/products-services/trust-identity/grouper/

If the switch group is 'auto' created from LDAP, you may want to override the
display name to show a more user-friendly group name.
(OpenL2M Admin -> Switch Groups -> select -> Display Name)
