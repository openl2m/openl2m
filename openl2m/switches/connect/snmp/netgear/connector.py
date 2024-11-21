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
Dell specific implementation of the SNMP object
This re-implements some methods found in the base SNMP() class
with Dell specific ways of doing things...
"""
from django.http.request import HttpRequest

from switches.connect.classes import Interface
from switches.connect.constants import POE_PORT_DETECT_DELIVERING
from switches.connect.snmp.connector import SnmpConnector, oid_in_branch
from switches.models import Switch, SwitchGroup
from switches.utils import dprint

from .constants import agentPethOutputPower

"""
Work in Progress
"""


class SnmpConnectorNetgear(SnmpConnector):
    """
    Netgear specific implementation of the SNMP object
    This re-implements some methods found in the base SNMP() class
    with Netgear specific ways of doing things...

    Mostly to read the PoE MIB the "netgear way".
    Of interest are:
    NETGEAR-POWER-ETHERNET-MIB - "NETGEAR Power Ethernet Extensions MIB"
    NETGEAR-SWITCHING-MIB - "NETGEAR Switching - Layer 2"
    """

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        # for now, just call the super class
        dprint("Netgear SnmpConnector __init__")
        super().__init__(request, group, switch)
        self.description = 'Netgear SNMP driver'
        self.can_save_config = False
        # force READ-ONLY for now! We have not implemented changing settings.
        self.switch.read_only = False
        self.vendor_name = ""

        # Netmiko is used for SSH connections. Here are some defaults a class can set.
        #
        # device_type:
        # if set, will be a value that will override (ie. hardcode) values from the
        # "Credentials Profile" (aka the NetmikoProfile() object)
        self.netmiko_device_type = "netgear"
        # self.netmiko_valid_device_types = False
        # the command that should be sent to disable screen paging
        # (defaults in the netmiko library to "terminal length 0", setting this to "" does NOT send a command.
        # self.netmiko_disable_paging_command = "terminal length 0"

        self.add_warning(
            "This Netgear driver has only been tested on a single M4250 switch, and may not work for your Netgear device!"
        )

    def _get_poe_data(self) -> int:
        """
        Get PoE data, first via the standard PoE MIB,
        then by calling the Netgear extended NETGEAR-POWER-ETHERNET-MIB
        """
        super()._get_poe_data()
        # The netgear switch we have show PSE consumed power (pethMainPseConsumptionPower) in milliwatts.
        # this even shows in their downloadable mibs, where pethMainPseConsumptionPower shows
        #    pethMainPseConsumptionPower OBJECT-TYPE
        #       UNITS       "Milliwatts"
        #       DESCRIPTION
        #          "Measured usage power expressed in Milliwatts."
        # per the standard POWER-ETHERNET-MIB defined in https://www.rfc-editor.org/rfc/rfc3621.html
        # this counter should be in Watts. We need to fix this over-reporting of power used!
        for pse in self.poe_pse_devices.values():
            pse.power_consumed = int(pse.power_consumed / 1000)
        # and the total usage:
        self.poe_power_consumed = int(self.poe_power_consumed / 1000)
        # now get Netgear specific port PoE power used
        retval = self.get_snmp_branch(branch_name='agentPethOutputPower', parser=self._parse_mibs_netgear_poe)
        if retval < 0:
            self.add_warning("Error getting 'PoE-Port-Current-Power' (agentPethOutputPower)")
        return 1

    """
    the NETGEAR-POWER-ETHERNET-MIB tables with port-level PoE power usage info
    OID is followed by PortEntry index (pe_index). This is typically
    or module_num.port_num for modules switch chassis, or
    device_id.port_num for stack members.
    This gets mapped to an interface later on in
    self._map_poe_port_entries_to_interface(), which is typically device specific
    """

    def _parse_mibs_netgear_poe(self, oid: str, val: str) -> bool:
        """
        Parse the Netgear extended NETGEAR-POWER-ETHERNET-MIB, power usage extension
        return True if we parse it, False if not.
        """
        dprint(f"_parse_mibs_netgear_poe() {oid}, len = {val}, type = {type(val)}")
        pe_index = oid_in_branch(agentPethOutputPower, oid)
        if pe_index:
            if pe_index in self.poe_port_entries.keys():
                self.poe_port_entries[pe_index].power_consumption_supported = True
                self.poe_port_entries[pe_index].power_consumed = int(val)
            return True

        return False

    def _map_poe_port_entries_to_interface(self):
        """
        This function maps the "pethPsePortEntry" indices that are stored in self.poe_port_entries{}
        to interface ifIndex values, so we can store them with the interface and display as needed.
        For Netgear single swithces,  the mapping appears to be <pse#>.<port#>, where each switch
        has a single PSE (ie PoE power supply)
        Therefor we can map this to interface name"o/<port#>"
        (It is also possible that Port# is the ifIndex directly; with one model of Netgear PoE devices
         tested, the ifIndex and Q-Bridge port ID are the same!)
        """
        dprint("_map_poe_port_entries_to_interface(Netgear)")
        for port_entry in self.poe_port_entries.values():
            (pse_module, port) = port_entry.index.split('.')
            # calculate the stack member number from PSE#
            member = int((int(pse_module) - 1) / 3)
            if_index = self._get_if_index_from_port_id(int(port))
            dprint(f"  PoE Entry {port_entry.index} => member {member} index {if_index}")
            for iface in self.interfaces.values():
                if iface.index == if_index:
                    dprint(f"  Interface found: {iface.name}")
                    iface.poe_entry = port_entry
                    if port_entry.detect_status > POE_PORT_DETECT_DELIVERING:
                        warning = (
                            f"PoE FAULT status ({port_entry.detect_status} = "
                            f"{poe_status_name[port_entry.detect_status]}) "
                            f"on interface {iface.name}"
                        )
                        self.add_warning(warning)
                        self.add_log(type=LOG_TYPE_ERROR, action=LOG_PORT_POE_FAULT, description=warning)
                    break
