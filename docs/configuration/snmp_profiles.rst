.. image:: ../_static/openl2m_logo.png


SNMP Profiles
=============

SNMP Profiles contain the information about the SNMP v2c or v3 settings of one or more devices.
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


