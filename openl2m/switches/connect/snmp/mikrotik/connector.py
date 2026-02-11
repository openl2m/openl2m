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
MikroTik-specific implementation of the SNMP object
This re-implements some methods found in the base SNMP() class
with vendor specific ways of doing things...
"""

from django.http.request import HttpRequest

import switches
from switches.connect.classes import PoePort

# from switches.constants import LOG_TYPE_ERROR, LOG_PORT_POE_FAULT
from switches.connect.constants import (
    POE_PORT_ADMIN_ENABLED,
    POE_PORT_ADMIN_DISABLED,
    #    POE_PORT_DETECT_DISABLED,
    POE_PORT_DETECT_SEARCHING,
    POE_PORT_DETECT_DELIVERING,
    POE_PORT_DETECT_FAULT,
)
from switches.connect.snmp.connector import SnmpConnector, oid_in_branch
from switches.models import Switch, SwitchGroup
from switches.utils import dprint

from switches.connect.snmp.mikrotik.constants import (
    mtxrPOEInterfaceIndex,
    mtxrPOEStatus,
    mtxrPOEPower,
)

#
# Work in Progress !
#

#
# MikroTik on supports the mibs described at
# https://help.mikrotik.com/docs/spaces/ROS/pages/8978519/SNMP#SNMP-Managementinformationbase(MIB)
#


class SnmpConnectorMikroTik(SnmpConnector):
    """
    MikroTik specific implementation of the SNMP object
    This re-implements some methods found in the base SNMP() class
    with MikroTik specific ways of doing things...
    """

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        # for now, just call the super class
        dprint("MikroTik SnmpConnector __init__")
        super().__init__(request, group, switch)
        self.description = "MikroTik SNMP driver"
        self.can_save_config = False
        # force READ-ONLY for now! We have not implemented changing settings.
        # self.switch.read_only = False
        self.vendor_name = "MikroTik"
        # map PoE-index to if_index
        self.poe_index_to_if_index = {}

        # Netmiko is used for SSH connections. Here are some defaults a class can set.
        #
        # device_type:
        # if set, will be a value that will override (ie. hardcode) values from the
        # "Credentials Profile" (aka the NetmikoProfile() object)
        self.netmiko_device_type = "mikrotik_routeros"
        # Note: this can also be "mikrotik_switchos", but both are handled in the same class "MikrotikBase()"
        # see https://github.com/ktbyers/netmiko/blob/develop/netmiko/mikrotik/mikrotik_ssh.py
        # and the netmiko handler at:
        # See https://github.com/ktbyers/netmiko/blob/develop/netmiko/ssh_dispatcher.py

        # self.netmiko_valid_device_types = False
        # the command that should be sent to disable screen paging
        # let Netmiko decide...
        # self.netmiko_disable_paging_command = "terminal length 0"

        # capabilities of the MikroTik driver:
        self.can_change_admin_status = True
        # no Vlan capabilities in MikroTik SNMP:
        self.can_change_vlan = False
        self.can_edit_vlans = False  # if true, this driver can edit (create/delete) vlans on the device!
        self.can_set_vlan_name = False  # set to False if vlan create/delete cannot set/change vlan name!
        # we can read PoE, but NOT change it:
        self.can_change_poe_status = False
        self.can_change_description = True
        self.can_save_config = False  # do we have the ability (or need) to execute a 'save config' or 'write memory' ?
        self.can_reload_all = True  # if true, we can reload all our data (and show a button on screen for this)

        self.add_warning(
            warning="This MikroTik driver has only been tested on a single Hex-S (RB760iGS) router, and may not work for your MikroTik device!",
            add_log=False,
        )
        self.add_warning(
            warning="Note: MikroTik does NOT support reading VLAN information via SNMP!",
            add_log=False,
        )

    def _get_poe_data(self) -> int:
        """
        Get PoE data, by calling the MikrTik extended "mtxrPOE" entry in MIKROTIK.MIB
        Note: we do not need to call super()._get_poe_data() to parse the standard PoE MIB,
        as this is NOT implemented on MikroTik devices.
        """
        # MikroTik POE to be read here:
        self.get_snmp_branch(branch_name="mtxrPOEEntry", parser=self._parse_mibs_mikrotik_poe)

        return 1

    #
    # the MikroTik mtxrPOE MIB tables with port-level PoE power usage info
    #

    def _parse_mibs_mikrotik_poe(self, oid: str, val: str) -> bool:
        """
        Parse the MikroTik extended POE table entries, power usage extension
        return True if we parse it, False if not.
        """

        dprint(f"_parse_mibs_mikrotik_poe() {oid}, len = {val}, type = {type(val)}")

        poe_index = oid_in_branch(mtxrPOEInterfaceIndex, oid)
        if poe_index:
            dprint(f"  mtxrPOEInterfaceIndex poe_index = {poe_index}, for if_index = {val}")
            # add PoE() to Interface()
            iface = self.get_interface_by_key(key=val)
            if iface:
                # save for other attributes of this entry:
                self.poe_index_to_if_index[poe_index] = val
                # add PoE info to interface:
                iface.poe_entry = PoePort(index=poe_index, admin_status=POE_PORT_ADMIN_ENABLED)
                dprint(f"  add PoePort object to {iface.name}")
                # in order to show on WebGUI, we have set PoE capabilities:
                self.poe_capable = True
                self.poe_enabled = True
                # and add a fake PoePSE (power supply)
                # self.poe_pse_devices[1] = PoePSE(1)
                # self.poe_pse_devices[1].set_max_power(power=10)
                # self.poe_pse_devices[1].description = "SIMULATED PowerSupply!"
            else:
                dprint(f"ERROR: interface '{val}' not found for index {poe_index}")
                self.add_warning(warning=f"Warning: interface '{val}' not found for index {poe_index}")
            return True  # parsed.

        # port PoE status
        poe_index = oid_in_branch(mtxrPOEStatus, oid)
        if poe_index:
            dprint(f"  mtxrPOEStatus poe_index = {poe_index}, status = {val}")
            if poe_index in self.poe_index_to_if_index:
                iface = self.get_interface_by_key(key=self.poe_index_to_if_index[poe_index])
                if iface:
                    # set PoE status
                    match int(val):
                        case switches.connect.snmp.mikrotik.constants.MIKROTIK_POE_DISABLED:
                            iface.poe_entry.admin_status = POE_PORT_ADMIN_DISABLED
                            dprint("  set PoE disabled!")

                        case switches.connect.snmp.mikrotik.constants.MIKROTIK_POE_WAITINGFORLOAD:
                            # this is the PoeEntry() class object default:
                            iface.poe_entry.detect_status = POE_PORT_DETECT_SEARCHING
                            dprint("  set PoE searching!")

                        case switches.connect.snmp.mikrotik.constants.MIKROTIK_POE_POWEREDON:
                            iface.poe_entry.detect_status = POE_PORT_DETECT_DELIVERING
                            dprint("  set PoE delivering!")

                        case _:  # anything else is error.
                            iface.poe_entry.detect_status = POE_PORT_DETECT_FAULT
                            dprint("  set PoE fault!")

            return True  # parsed.

        poe_index = oid_in_branch(mtxrPOEPower, oid)
        if poe_index:
            dprint(f"  mtxrPOEPower poe_index = {poe_index}, power = {val}W")
            if poe_index in self.poe_index_to_if_index:
                iface = self.get_interface_by_key(key=self.poe_index_to_if_index[poe_index])
                if iface:
                    # set PoE power on:
                    dprint(" adding power used!")
                    iface.poe_entry.power_consumed = int(val)

            return True  # parsed.

        return False
