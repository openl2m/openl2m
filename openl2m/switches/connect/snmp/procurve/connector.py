#
# This file is part of Open Layer 2 Management (OpenL2M).
#
# OpenL2M is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with OpenL2M. If not, see <http://www.gnu.org/licenses/>.
#
"""
HP-Procurve specific implementation of the SNMP object.
This also support recent "Aruba" branded switches.
Note that this does NOT support "Aruba CX" switches.
The latter are supported via connect/snmp/aruba-cx/ (read-only), or connect/aruba_aoscx/

This re-implements some methods found in the base SNMP() class
with Procurve/Aruba specific ways of doing things...
"""
import datetime

from switches.models import Log
from switches.constants import LOG_TYPE_ERROR, LOG_PORT_POE_FAULT
from switches.connect.constants import POE_PORT_DETECT_DELIVERING, poe_status_name
from switches.connect.snmp.connector import SnmpConnector, oid_in_branch
from switches.utils import dprint, get_remote_ip

from .constants import (
    hpicfPoePethPsePortPower,
    hpEntPowerCurrentPowerUsage,
    hpnicfIfLinkMode,
    hpnicfCfgRunModifiedLast,
    hpnicfCfgRunSavedLast,
    HP_ROUTE_MODE,
)


class SnmpConnectorProcurve(SnmpConnector):
    """
    HP-Procurve specific implementation of the SNMP object
    This re-implements some methods found in the base SNMP() class
    with Procurve specific ways of doing things...
    """

    def __init__(self, request, group, switch):
        # for now, just call the super class
        dprint("HP/Procurve SnmpConnector __init__")
        super().__init__(request, group, switch)
        self.description = 'Aruba Networks (HP/ProCurve) SNMP driver'
        self.vendor_name = "Aruba Networks (HP/Procurve)"

        # some capabilities we cannot do:
        self.can_save_config = False  # not needed on ProCurve, it has auto-save!

    def _parse_oid(self, oid, val):
        """
        Parse a single OID with data returned from a switch through some "get" function
        Returns True if we parse the OID!
        """
        dprint(f"HP _parse_oid() {oid}")
        if self._parse_mibs_hp_poe(oid, val):
            return True
        if self._parse_mibs_hp_if_linkmode(oid, val):
            return True
        # call the generic base parser
        return super()._parse_oid(oid, val)

    def _get_interface_data(self):
        """
        Implement an override of the interface parsing routine,
        so we can add HP specific interface MIBs
        """
        # first call the base class to populate interfaces:
        super()._get_interface_data()

        # now add HP data, and cache it:
        if self.get_snmp_branch('hpnicfIfLinkMode', self._parse_mibs_hp_if_linkmode) < 0:
            dprint("Comware hpnicfIfLinkMode returned error!")
            return False

        return True

    def get_my_hardware_details(self):
        """
        Implement the get_my_hardware_details(), called from the base object get_hardware_details()
        """
        super().get_my_hardware_details()

        # now read Procurve specific data:
        retval = self.get_snmp_branch('hpnicfCfgLog', self._parse_mibs_procurve_config)
        if retval < 0:
            self.add_warning("Error getting Procurve config details ('hpnicfCfgLog')")
            return False
        return True

    """
    HP has 2 possible MIBs with port(interface) power information:
    the hpicfPoePethPsePortPower or hpEntPowerCurrentPowerUsage tables.
    OID is followed by PortEntry index (pe_index). This is typically
    or module_num.port_num for a modular switch chassis, or
    device_id.port_num for stack members.
    This gets mapped to an interface later on in
    self._map_poe_port_entries_to_interface()
    """

    def _parse_mibs_hp_poe(self, oid, val):
        """
        Parse HP specific Power Extention MIBs
        """
        dprint("HP _parse_mibs_hp_poe()")
        pe_index = oid_in_branch(hpicfPoePethPsePortPower, oid)
        if pe_index:
            dprint(f"Found hpicfPoePethPsePortPower, pe_index = {pe_index}")
            if pe_index in self.poe_port_entries.keys():
                self.poe_port_entries[pe_index].power_consumption_supported = True
                self.poe_port_entries[pe_index].power_consumed = int(val)
            return True

        pe_index = oid_in_branch(hpEntPowerCurrentPowerUsage, oid)
        if pe_index:
            dprint(f"Found branch hpEntPowerCurrentPowerUsage, pe_index = {pe_index}")
            if pe_index in self.poe_port_entries.keys():
                self.poe_port_entries[pe_index].power_consumption_supported = True
                self.poe_port_entries[pe_index].power_consumed = int(val)
            return True

        return False

    def _parse_mibs_hp_if_linkmode(self, oid, val):
        """
        Parse HP specific Interface Extension MIB for link mode, PoE info
        """
        dprint("HP _parse_mibs_hp_if_linkmode()")
        if_index = int(oid_in_branch(hpnicfIfLinkMode, oid))
        if if_index:
            dprint(f"HP LinkMode if_index {if_index} link_mode {val}")
            if if_index in self.interfaces.keys():
                if int(val) == HP_ROUTE_MODE:
                    self.interfaces[if_index].is_routed = True
            return True
        return False

    def _parse_mibs_procurve_config(self, oid, val):
        """
        Parse Procurve specific ConfigMan MIBs for running-config info
        This gets added to the Information tab!
        """
        dprint("HP _parse_mibs_procurve_config()")
        sub_oid = oid_in_branch(hpnicfCfgRunModifiedLast, oid)
        if sub_oid:
            ago = str(datetime.timedelta(seconds=int(val) / 100))
            self.add_more_info("Configuration", "Running Last Modified", ago)
            return True

        sub_oid = oid_in_branch(hpnicfCfgRunSavedLast, oid)
        if sub_oid:
            ago = str(datetime.timedelta(seconds=int(val) / 100))
            self.add_more_info("Configuration", "Running Last Saved", ago)
            return True
        return False

    def _get_poe_data(self):
        """
        HP has 2 possible MIBs with port(interface) power information:
        the hpicfPoePethPsePortPower or hpEntPowerCurrentPowerUsage tables.
        First get PoE data from the HP-IFC-POE-MIB, and if not found
        call the HP-ENTITY-POWER-MIB
        """
        # get standard data first, this loads PoE status, etc.
        super()._get_poe_data()
        # if we found power supplies, get HP specific info about power usage from HP-IFC-POE-MIB first
        if self.poe_capable:
            retval = self.get_snmp_branch('hpicfPoePethPsePortPower', self._parse_mibs_hp_poe)
            if retval < 0:
                self.add_warning("Error getting 'PoE-Port-Actual-Power' (hpicfPoePethPsePortActualPower)")
            if retval == 0:
                # maybe this device supports HP-ENTITY-POWER-MIB
                retval = self.get_snmp_branch('hpEntPowerCurrentPowerUsage', self._parse_mibs_hp_poe)

        return 1

    def _map_poe_port_entries_to_interface(self):
        """
        This function maps the "pethPsePortEntry" indices that are stored in self.poe_port_entries{}
        to interface ifIndex values, so we can store them with the interface and display as needed.
        In general, for traditional Procurve devices, the power index is "modules.port", eg 1.12
        The power indices for modular or stacked devices is 1.1 - 1.24, then 2.25 - 2.48, 3.49 - 3.72, etc.
        I.e. the first digit is the module or stack member, and the port numbers continue to count up,
        and is likely the ifIndex!
        """
        dprint("Procurve _map_poe_port_entries_to_interface()\n")
        for pe_index, port_entry in self.poe_port_entries.items():
            # we take the ending part of "5.12" as the index
            (module, index) = port_entry.index.split('.')
            # for the SnmpConnector() class and sub-classes, the "index" is the key to the Interface()
            if index in self.interfaces.keys():
                iface = self.interfaces[index]
                dprint(f"   PoE Port Map FOUND {iface.name}")
                # add this poe entry to the interface
                iface.poe_entry = port_entry
                if port_entry.detect_status > POE_PORT_DETECT_DELIVERING:
                    warning = (
                        f"PoE FAULT status ({port_entry.detect_status} = "
                        f"{poe_status_name[port_entry.detect_status]}) on interface {iface.name}"
                    )
                    self.add_warning(warning)
                    # log my activity
                    log = Log(
                        user=self.request.user,
                        group=self.group,
                        switch=self.switch,
                        type=LOG_TYPE_ERROR,
                        ip_address=get_remote_ip(self.request),
                        action=LOG_PORT_POE_FAULT,
                        description=warning,
                    )
                    log.save()
            else:
                # should not happen!
                dprint(f"ERROR: PoE entry NOT FOUND for pe_index={pe_index}")
