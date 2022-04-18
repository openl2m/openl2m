.. image:: ../_static/openl2m_logo.png


========
Profiles
========

Profiles are configuration settings that are related to each other.
Once you have created one or more of the profiles below,
they can be applied to switches.

SNMP Profiles
=============

SNMP Profiles contain the information about the SNMP v2c or v3 settings of one or more switches.
By creating an SNMP Profile once, you can apply this to as many switches as needed,
without the need to repeatedly enter the same information.

To configure, go to Admin, then in the Switches section, go to SNMP Profiles
or click the "+ Add" option behind the SNMP Profiles menu entry.

At a minimum, you will need to give the new profile a name, and the proper version.

For v2c, fill in the 'read-write' community name.

If using v3 (which we strongly recommend), fill in the proper security options
for Auth-No-Priv, or Auth-Priv. (We do not recommend you use No-Auth-No-Priv)
Make sure you use credentials that can read & write the switches,
if your intention is to allow users to make changes. E.g. for routers you could
configure a read-only SNMP Profile, if that device will only be read from!


Credential Profiles
===================

OpenL2M uses credentials for a variety of authentications: SSH logins (with Netmiko library),
and various API accounts such as REST, NetConf, and more.

Netmiko has the ability to execute command-line commands on switches, if configured.
For this, we use the `Netmiko Python library <https://github.com/ktbyers/netmiko>`_.
This library allows us to establish SSH connections to the switch to execute the commands.

For Aruba AOS-CX switch support, we communicate via their REST API. Set the proper username and password for accessing these devices.

Junos device will be supported via the Junos PyEZ library. This requires a username and password set.

To configure this, go to Admin, then go to *Credential Profiles* in the Switches section,
or click the "+ Add" option behind the menu entry.

At a minimum, you will need to give the new profile a name,
and a username and password for the API, NetConf or SSH login.

Select the proper Netmiko device type (if applicable). If Cisco, you can give the 'enable'
password. This is currently not used yet, so you can leave it blank as well.

If you run SSH (Netmiko) on a non-standard port, enter it. If you want SSL host key checking,
select the option. Note this is not tested, but should work if you have
the proper SSH known hosts config files in the user profile that runs your web server.

**Note that firewall rules, switch ACLs etc. will need to
allow SSH/API connections from the web server.**
