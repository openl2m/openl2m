.. image:: ../_static/openl2m_logo.png


===========
Permissions
===========

**What can a user modify in OpenL2M?**

The intention of this software is the allow for distributed simple layer-2 management
of switches across a campus-network. As such, we only allow changing of 'end-user'
switch ports. This includes enabling/disabling the interface, changing the 'user' vlan
(PVID or untagged vlan), the interface description, and toggling PoE (when implemented).

This tool is not intended to be a full-blown network management tool!

**Here are the basic rules:**

* an interface that does not have a physical connection (eg Loopback, Vlan, etc) cannot be managed.
  For 'regular' users, it will not even be shown.

* users with the 'Superuser' flag set can manage the application via the Adminstration menu item.
  Ie. they can add users, switches, groups, etc.

* users with the 'Superuser' or 'Staff' flag set can manage any aspect of any manageable
  interface on all switches in all groups, UNLESS a switch, group, or user is marked as Read-Only!
  The Read-Only flag cannot be overwritten, not even by the SuperUser!

  The 'Staff' flag is useful for central service desk personnel that need to be able to
  help any user or distributed IT member. Read-Only staff could be e.g. students at that
  central service desk that can see all, but cannot modify. This obviously depends on your
  internal management policies.

* the Bulk-Edit flag is enabled by default on Users, Switch Groups, and Switches. If disabled on
  any of those, the user will not see the Bulk Edit tab (web form).

* the 'Allow PoE Toggle' flag can be set in the global settings (configuration.py), or on the User,
  Switch Group or Switch objects. If set anywhere, the user can toggle PoE on any interface,
  even if they cannot change the interface status or vlan.
  This allows for all users to power-cycle devices like VOIP Phones, Access Points, etc.

* the 'Edit Port Description' flag is enabled by default on Users, Switch Groups, and Switches. If disabled on
  any of those, the user will not able to edit the interface description on interfaces they have access to.

* the 'Tasks' flag allows the user to schedule tasks on a switch. *Any* user with the ability to create tasks
  on a given switch can delete scheduled tasks from the switch's "Information" tab.
  (Assuming the background processes are running!) Administrators and Staff have access to all tasks.


**Finally, the fun part:**

You add switches, vlans, and users to switch groups. A user in a group can ONLY manage the
switches in that group, and only change interfaces that have a 'user vlan' that is
in the list of vlans for that group! If a user is marked 'read-only', that is what they
can do!

Note that any switch, vlan or user can be in multiple groups. This is useful in
co-located buildings where multiple units are using network ports that terminate
on the same switches. Using the above group scheme, you can give IT personnel of several
departments rights to "their switches", but they can only touch ports that are on their
departmental vlans!

E.g.: you can have Group-1, containing switch-A with vlans 1,2,3,4 for IT Staff (users)
A, B and C in Department One.
Group-2 contains the same switch-A, but with vlans 8,9,10, with IT staff D and E in
Department Two.  Both groups can manage their ports, but not touch the other
departments' ports.

If you need the ability to 'hand-off' ports between departments, create a 'unused' vlan,
and add this to both groups. When a group is done with the interface, change the vlan
to the 'unused' vlan, and now the other department can manage that port!
