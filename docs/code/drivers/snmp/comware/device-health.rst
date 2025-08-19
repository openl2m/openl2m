
.. image:: ../../../../_static/openl2m_logo.png

=======================
HPE Comware SNMP Health
=======================

The function *check_my_device_health()* implements a check of the IRF stacking technology.

We first class the super-class, and then *_check_irf_health()*. The latter reads entries from the
HPE Comware HH3C-STACK-MIB.

A good explaination is at https://www.h3c.com/en/d_202302/1769896_294551_0.htm and an easily
readable mib format at https://mibs.observium.org/mib/HH3C-STACK-MIB/

We read **hh3cStackMemberNum** to see if there are stack members. If so, we next read the members,
their member ID, active IRF ports and their priority at **hh3cStackDeviceConfigEntry**.
This is parsed at *_parse_mibs_irf_device_config()*

Next, we read their roles from **hh3cStackBoardConfigEntry**, parsed at *_parse_mibs_irf_device_role()*.
This is an indirect read, each device can have boards with a role. So we map the board-id to the member-id.

Finally, we check if:
* each member has at least 2 active IRF ports,
* that the 'master' member has the highest priority (if not, this means there was a failure somewhere)

In either of those situations, we add a log warning about device health.



