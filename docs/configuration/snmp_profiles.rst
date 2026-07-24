.. image:: ../_static/openl2m_logo.png

=============
SNMP Profiles
=============

For devices managed by SNMP, you will first need to add at least one SNMP Profile.
This contains the information about the SNMP v2c or v3 settings of one or more devices.
By creating an SNMP Profile once, you can apply this to as many devices as needed,
without the need to repeatedly enter the same information.

From the **Admin menu** option, go to **SNMP Profiles** or click the **+ Add** option.

At a minimum, you will need to give the new profile a *name*, and select the proper **Version**.
A **Description** may be helpful as well.

If the SNMP credentials provide for **Read-Only access**, mark it as such.
Note that checking this on R/W credentials will also make devices that use this R/O !

For **version 2c**, fill in the 'read-write' **V2c Community name**.

If using **v3** (which we strongly recommend), select that **Security level**, and then
fill in the proper security options for NoAuth-NoPriv, Auth-No-Priv, or Auth-Priv. (We do not recommend you use No-Auth-No-Priv)

Make sure you use credentials that can read & write the switches,
if your intention is to allow users to make changes. E.g. for routers you could
configure a read-only SNMP Profile, if that device will only be read from!

*Note: We do NOT support the ancient SNMP version 1 !*

