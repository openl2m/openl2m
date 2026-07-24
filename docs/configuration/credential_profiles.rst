.. image:: ../_static/openl2m_logo.png

===================
Credential Profiles
===================

OpenL2M uses credentials for a variety of authentications:

* SSH login to execute commands on devices.
* REST API access ion drivers. E.g. for Arista, Aruba AOS-S, Aruba AOS-CX and HPE Comware devices for REST.
* Junos PyEZ (netconf) access.
* Devices configured for the (minimal, read-only) Napalm driver.

To configure this, go to **Admin menu**, then go to **Credential Profiles** and click the **+ Add** option behind the menu entry.

At a minimum, you will need to give the new profile a **Name**.
This name is what you willl select it on the switch configuration page!
We recommend you set a name that is appropriate for the use,
e.g "SSH-Access", "Junos-Netconf-Credentials", "AOS-CX API Access".

A **Description** may be helpful to track usage as well.

Next, set a **Username** and **Password** for the API, NetConf or SSH login.

If this is used for Commands over SSH, select the proper **Netmiko device type**.

If using this Credential Profile for Cisco devices, you can give the **enable password**.
This is currently not used yet, so you can leave it blank as well.

If you run SSH (Netmiko) on a non-standard port, enter it in the **Tcp port** field.

If you want SSL host key checking, select the option to **Verify host key** (default is to ignore SSL cert errors).
Note enabling this is not tested, but should work if you have
the proper SSH known hosts config files and SSL certs *in the user profile that runs your web server!*
Please follow your organization's security policy.

.. note::

    On the AOS-S and Comware REST connectors, when running Python 3.13+,
    with SSL checking disabled (the default), we added support to
    ignore the new Python/SSL library defaults to check for X.509, older ciphers, etc.


**Note that firewall rules, device ACLs etc. will need to
allow SSH/API connections from the IP address of the web server where OpenL2M is installed.**

Vendor and Other Notes
----------------------

To execute command-line commands over SSH on switches (if configured), we use the
`Netmiko Python library <https://github.com/ktbyers/netmiko>`_.

For **Aruba AOS-CX switches** using the REST driver (ie not snmp), we communicate via their REST API.
Set the proper username and password for accessing these devices.

**Junos devices** are supported via the Junos PyEZ library. This requires a username and password.
**We do not support certificate-based access at this time.**



