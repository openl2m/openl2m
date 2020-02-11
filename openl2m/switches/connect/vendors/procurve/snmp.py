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
HP-Procurve specific implementation of the SNMP object
This re-implements some methods found in the base SNMP() class
with Procurve specific ways of doing things...
"""
from switches.models import Log
from switches.connect.classes import *
from switches.connect.snmp import SnmpConnector, oid_in_branch
from switches.connect.constants import *
from switches.utils import *

from .constants import *


class SnmpConnectorProcurve(SnmpConnector):
    """
    HP-Procurve specific implementation of the SNMP object
    This re-implements some methods found in the base SNMP() class
    with Procurve specific ways of doing things...
    """

    def __init__(self, request, group, switch):
        # for now, just call the super class
        dprint("HP-Aruba/Procurve SnmpConnector __init__")
        super().__init__(request, group, switch)
        self.name = "HP-Aruba/Procurve SnmpConnector"  # what type of class is running!
        self.vendor_name = 'HP/Procurve'

    def _parse_oid(self, oid, val):
        """
        Parse a single OID with data returned from a switch through some "get" function
        Returns True if we parse the OID!
        """
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
        if self._get_branch_by_name('hpnicfIfLinkMode', True, self._parse_mibs_hp_if_linkmode) < 0:
            dprint("Comware hpnicfIfLinkMode returned error!")
            return False

        return True

    def _get_vendor_data(self):
        """
        Implement the get_vendor_data() class from the base object
        """
        self._get_branch_by_name('hpnicfCfgLog', True, self._parse_mibs_procurve_config)

    """
    HP has 2 possible MIBs with port(interface) power information:
    the hpicfPoePethPsePortPower or hpEntPowerCurrentPowerUsage tables.
    OID is followed by PortEntry index (pe_index). This is typically
    or module_num.port_num for modules switch chassis, or
    device_id.port_num for stack members.
    This gets mapped to an interface later on in
    self._map_poe_port_entries_to_interface()
    """
    def _parse_mibs_hp_poe(self, oid, val):
        """
        Parse HP specific Power Extention MIBs
        """
        dprint("_parse_mibs_hp_poe()")
        pe_index = oid_in_branch(hpicfPoePethPsePortPower, oid)
        if pe_index:
            if pe_index in self.poe_port_entries.keys():
                self.poe_port_entries[pe_index].power_consumption_supported = True
                self.poe_port_entries[pe_index].power_consumed = int(val)
            return True

        pe_index = oid_in_branch(hpEntPowerCurrentPowerUsage, oid)
        if pe_index:
            if pe_index in self.poe_port_entries.keys():
                self.poe_port_entries[pe_index].power_consumption_supported = True
                self.poe_port_entries[pe_index].power_consumed = int(val)
            return True

        return False

    def _parse_mibs_hp_if_linkmode(self, oid, val):
        """
        Parse HP specific Interface Extension MIB for link mode, PoE info
        """
        if_index = int(oid_in_branch(hpnicfIfLinkMode, oid))
        if if_index:
            dprint("HP LinkMode if_index %s link_mode %s" % (if_index, val))
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
        sub_oid = oid_in_branch(hpnicfCfgRunModifiedLast, oid)
        if sub_oid:
            ago = str(datetime.timedelta(seconds=int(val) / 100))
            self.add_vendor_data("Configuration", "Running Last Modified", ago)
            return True

        sub_oid = oid_in_branch(hpnicfCfgRunSavedLast, oid)
        if sub_oid:
            ago = str(datetime.timedelta(seconds=int(val) / 100))
            self.add_vendor_data("Configuration", "Running Last Saved", ago)
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
        # now get HP specific info about power usage from HP-IFC-POE-MIB first
        retval = self._get_branch_by_name('hpicfPoePethPsePortPower', True, self._parse_mibs_hp_poe)
        if retval < 0:
            self._add_warning("Error getting 'PoE-Port-Actual-Power' (hpicfPoePethPsePortActualPower)")
        if retval == 0:
            # maybe this device supports HP-ENTITY-POWER-MIB
            retval = self._get_branch_by_name('hpEntPowerCurrentPowerUsage', True, self._parse_mibs_hp_poe)

        return 1

    def _map_poe_port_entries_to_interface(self):
        """
        This function maps the "pethPsePortEntry" indices that are stored in self.poe_port_entries{}
        to interface ifIndex values, so we can store them with the interface and display as needed.
        In general, you can generate the interface ending "x/y" from the index by substituting "." for "/"
        E.g. "5.12" from the index becomes "5/12", and you then search for an interface with matching ending
        e.g. GigabitEthernet5/12
        """
        dprint("Procurve _map_poe_port_entries_to_interface()\n")
        for (pe_index, port_entry) in self.poe_port_entries.items():
            # we take the ending part of "5.12" as the index
            (module, port) = port_entry.index.split('.')
            count = len(port)
            for (if_index, iface) in self.interfaces.items():
                if iface.name == port:
                    dprint("   PoE Port Map FOUND %s" % iface.name)
                    iface.poe_entry = port_entry
                    if port_entry.detect_status > POE_PORT_DETECT_DELIVERING:
                        warning = "PoE FAULT status (%s) on interface %s" % (port_entry.status_name, iface.name)
                        self._add_warning(warning)
                        # log my activity
                        log = Log()
                        log.user = self.request.user
                        log.type = LOG_TYPE_ERROR
                        log.ip_address = get_remote_ip(request)
                        log.action = LOG_PORT_POE_FAULT
                        log.description = warning
                        log.save()
                    break


"""
    def can_save_config(self):
        # If True, this instance can save the running config to startup
        # Procurve has auto-save, so no save needed, i.e. return False
        return False
"""
