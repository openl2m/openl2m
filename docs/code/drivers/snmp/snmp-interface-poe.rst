.. image:: ../../../_static/openl2m_logo.png

=============================
Discover interface PoE status
=============================

In *self.get_my_basic_info()*, we finally call *self._get_poe_data()*. This reads data from the POE MIB.

.. code-block:: python

    retval = self._get_poe_data()
    if retval != -1:
        # try to map poe port info to actual interfaces
        self._map_poe_port_entries_to_interface()



1 - Power Supplies
------------------

We first read **pethMainPseEntry**, this will return the PSE's or Power Sourcing Entities; ie the PoE Power Supplies.
These mib entries are parsed in *self._parse_mibs_poe_supply()*
This will add objects of **class PoEPSE()**

2 - PoE Ports
-------------

If PSEs are found, we next read **pethPsePortAdminEnable**. This provides us with the admin status of a PoE port, i.e. PoE enabled or disabled.
And, this then also tells us if a port is PoE enabled! If PoE info is found, we create a **class PoePort()** object, and save that info.
More on that below.

Next, we read **pethPsePortDetectionStatus**. This gives us the current state of PoE when enabled;
i.e. is it sourcing power, searching for remote device, etc.

(Note these two MIB entities are under the "full attributes" info at *pethPsePortEntry*,
but we only need a few entries, so we don't read the full entry table.)

Both are parsed in *self._parse_mibs_poe_port()* around line 3435.

**Important:**

PoE info from the entities abovfe not directly mapped to ifIndex, so you cannot directly connect the above attributes to an *Interface()* object!

All PoE attributes in the *pethPsePortEntry* table are indexed by a separate "PortEntry index", which we call "pe_index" in our code.
We store these entries in a Dict() structure of "pe_index => PoePort()", and fill in attributes as we find them:

.. code-block:: python

    pe_index = oid_in_branch(pethPsePortAdminEnable, oid)
    if pe_index:
        self.poe_port_entries[pe_index] = PoePort(pe_index, int(val))
        return True

    pe_index = oid_in_branch(pethPsePortDetectionStatus, oid)
    if pe_index:
        if pe_index in self.poe_port_entries:
            self.poe_port_entries[pe_index].detect_status = int(val)
        return True

3 - PoE Power Used
------------------

The standard PoE MIB does **NOT** support entities to read the power drawn by a PoE port.
This data comes from vendor-specific PoE extensions.

Drivers typically handle this by overriding the *_get_poe_data()* function from the *SnmpConnector()* class,
calling the base function, and next implement reading of additional custom vendor MIB entities.

E.g. frm the HPE Comware driver:

.. code-block:: python

    def _get_poe_data(self) -> int:
        super()._get_poe_data()
        if self.poe_capable:  # we found PoE power supplies!
            # now get HP specific info from HP-IFC-POE-MIB first
            retval = self.get_snmp_branch(branch_name="hh3cPsePortCurrentPower", parser=self._parse_mibs_comware_poe)


4 - Map PoE Port info to Interface
----------------------------------

As the "pe_index" is not the same as the *ifIndex*, we need to map this to a physical port. *This is vendor-specific!*

We have a base implementation in *self._map_poe_port_entries_to_interface()*, which tries to map the interface name
"gigE1/1" to pe_index "1.1", and find *PoePort()* info to add to an *Interface().poe_entry* attribute.

This *may* work, but vendor-drivers should overload this function for proper mapping...

The SNMP drivers for Cisco, HPE Comware, HPE Procurve, Juniper and Netgear implement this custom override.
