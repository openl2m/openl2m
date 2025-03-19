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

from django.http.request import HttpRequest

from switches.models import Switch, SwitchGroup
from switches.constants import LOG_TYPE_ERROR, LOG_PORT_POE_FAULT
from switches.connect.classes import Transceiver
from switches.connect.constants import POE_PORT_DETECT_DELIVERING, poe_status_name
from switches.connect.snmp.connector import SnmpConnector, oid_in_branch
from switches.utils import dprint

from .constants import (
    hpicfPoePethPsePortPower,
    hpEntPowerCurrentPowerUsage,
    hpnicfIfLinkMode,
    hpnicfCfgRunModifiedLast,
    hpnicfCfgRunSavedLast,
    HP_ROUTE_MODE,
    hpicfXcvrInfoTable,
    hpicfXcvrModel,
    hpicfXcvrType,
    hpicfXcvrConnectorType,
    hpicfXcvrWavelength,
)


class SnmpConnectorProcurve(SnmpConnector):
    """
    HP-Procurve specific implementation of the SNMP object
    This re-implements some methods found in the base SNMP() class
    with Procurve specific ways of doing things...
    """

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        # for now, just call the super class
        dprint("HP/Procurve SnmpConnector __init__")
        super().__init__(request, group, switch)
        self.description = 'Aruba Networks (HP/ProCurve) SNMP driver'
        self.vendor_name = "Aruba Networks (HP/Procurve)"

        # Netmiko is used for SSH connections. Here are some defaults a class can set.
        #
        # device_type:
        # if set, will be a value that will override (ie. hardcode) values from the
        # "Credentials Profile" (aka the NetmikoProfile() object)
        self.netmiko_device_type = "hp_procurve"
        # no need to override default of netmiko_valid_device_types[]
        #
        # the command that should be sent to disable screen paging
        # let Netmiko decide...
        # self.netmiko_disable_paging_command = "no page"

        # some capabilities we cannot do:
        self.can_save_config = False  # not needed on ProCurve, it has auto-save!

    def _get_interface_data(self) -> bool:
        """
        Implement an override of the interface parsing routine,
        so we can add HP specific interface MIBs
        """
        # first call the base class to populate interfaces:
        super()._get_interface_data()

        # now add HP data, and cache it:
        if self.get_snmp_branch(branch_name='hpnicfIfLinkMode', parser=self._parse_mibs_hp_if_linkmode) < 0:
            dprint("Comware hpnicfIfLinkMode returned error!")
            return False

        return True

    def _get_interface_transceiver_types(self) -> int:
        """
        Augment SnmpConnector._get_interface_transceiver_type() to read more transceiver info of a physical port
        from an HP-specific MIB.

        Returns 1 on succes, -1 on failure
        """
        super()._get_interface_transceiver_types()
        # now read HP data
        retval = self.get_snmp_branch(branch_name='hpicfXcvrInfoTable', parser=self._parse_mibs_procurve_transceiver)
        if retval < 0:
            self.add_warning(f"Error getting Transceiver data (hpicfXcvrInfoTable)'")
            return retval

    def get_my_hardware_details(self) -> bool:
        """
        Implement the get_my_hardware_details(), called from the base object get_hardware_details()
        """
        super().get_my_hardware_details()

        # now read Procurve specific data:
        retval = self.get_snmp_branch(branch_name='hpnicfCfgLog', parser=self._parse_mibs_procurve_config)
        if retval < 0:
            self.add_warning(warning="Error getting Procurve config details ('hpnicfCfgLog')")
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

    def _parse_mibs_hp_poe(self, oid: str, val: str) -> bool:
        """
        Parse HP specific Power Extention MIBs
        """
        dprint(f"HP _parse_mibs_hp_poe(): {str(oid)} = {val}")

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

    def _parse_mibs_hp_if_linkmode(self, oid: str, val: str) -> bool:
        """
        Parse HP specific Interface Extension MIB for link mode, PoE info
        """
        dprint(f"HP _parse_mibs_hp_if_linkmode(): {str(oid)} = {val}")

        if_index = int(oid_in_branch(hpnicfIfLinkMode, oid))
        if if_index:
            dprint(f"HP LinkMode if_index {if_index} link_mode {val}")
            if if_index in self.interfaces.keys():
                if int(val) == HP_ROUTE_MODE:
                    self.interfaces[if_index].is_routed = True
            return True
        return False

    def _parse_mibs_procurve_config(self, oid: str, val: str) -> bool:
        """
        Parse Procurve specific ConfigMan MIBs for running-config info
        This gets added to the Information tab!
        """
        dprint(f"HP _parse_mibs_procurve_config(): {str(oid)} = {val}")

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

    def _parse_mibs_procurve_transceiver(self, oid: str, val: str) -> bool:
        """
        Parse HP/Procurve specific interface Transeiver information.
        See HP-ICF-TRANSCEIVER-MIB
        return True if we parse it, False if not.
        """
        dprint(f"HP _parse_mibs_procurve_transceiver(): {str(oid)} = {val}")

        if_index = oid_in_branch(hpicfXcvrModel, oid)
        if if_index:
            iface = self.get_interface_by_key(key=if_index)
            if iface:
                if not iface.transceiver:
                    iface.transceiver = Transceiver()
                iface.transceiver.model = val
            return True

        if_index = oid_in_branch(hpicfXcvrType, oid)
        if if_index:
            iface = self.get_interface_by_key(key=if_index)
            if iface:
                if not iface.transceiver:
                    iface.transceiver = Transceiver()
                # ifMauType was parsed before this, so it is possible that type field is already set!
                # we prefer the standardized ifMayType format!
                if not iface.transceiver.type:
                    # not yet set from the ifMau mib!
                    iface.transceiver.type = val.strip()  # some entries have extra spaces.
            return True

        if_index = oid_in_branch(hpicfXcvrWavelength, oid)
        if if_index:
            iface = self.get_interface_by_key(key=if_index)
            if iface:
                if not iface.transceiver:
                    iface.transceiver = Transceiver()
                iface.transceiver.wavelength = val
            return True

        if_index = oid_in_branch(hpicfXcvrConnectorType, oid)
        if if_index:
            iface = self.get_interface_by_key(key=if_index)
            if iface:
                if not iface.transceiver:
                    iface.transceiver = Transceiver()
                iface.transceiver.connector = val
            return True

        return False

    def _get_poe_data(self) -> int:
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
            retval = self.get_snmp_branch(branch_name='hpicfPoePethPsePortPower', parser=self._parse_mibs_hp_poe)
            if retval < 0:
                self.add_warning(warning="Error getting 'PoE-Port-Actual-Power' (hpicfPoePethPsePortActualPower)")
            if retval == 0:
                # maybe this device supports HP-ENTITY-POWER-MIB
                retval = self.get_snmp_branch(branch_name='hpEntPowerCurrentPowerUsage', parser=self._parse_mibs_hp_poe)

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
                    self.add_warning(warning=warning)
                    self.add_log(type=LOG_TYPE_ERROR, action=LOG_PORT_POE_FAULT, description=warning)
            else:
                # should not happen!
                dprint(f"ERROR: PoE entry NOT FOUND for pe_index={pe_index}")
