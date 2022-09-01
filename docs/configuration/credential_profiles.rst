.. image:: ../_static/openl2m_logo.png

===================
Credential Profiles
===================

OpenL2M uses credentials for a variety of authentications:
* SSH login to execute commands.
* Aruba-CX REST API access.
* Junos PyEZ (netconf) access.

To configure this, go to Admin, then go to *Credential Profiles* in the Switches section,
or click the "+ Add" option behind the menu entry.

At a minimum, you will need to give the new profile a name. This name is what you willl select it on the switch configuration page!
Set a name that is appropriate for the use, e.g "SSH-Access", "Junos-Netconf-Credentials", "AOS-CX API Access".

Next, set a username and password for the API, NetConf or SSH login.

Select the proper Netmiko device type (if applicable). If Cisco, you can give the 'enable'
password. This is currently not used yet, so you can leave it blank as well.

If you run SSH (Netmiko) on a non-standard port, enter it. If you want SSL host key checking,
select the option. Note this is not tested, but should work if you have
the proper SSH known hosts config files in the user profile that runs your web server.

**Note that firewall rules, device ACLs etc. will need to
allow SSH/API connections from the web server where OpenL2M is installed.**

Vendor and Other Notes:

To execute command-line commands over SSH on switches (if configured), we use the
`Netmiko Python library <https://github.com/ktbyers/netmiko>`_.

For **Aruba AOS-CX switch** support, we communicate via their REST API. Set the proper username and password for accessing these devices.

**Junos devices** are supported via the Junos PyEZ library. This requires a username and password. We do not support certificate-based access at this time.



