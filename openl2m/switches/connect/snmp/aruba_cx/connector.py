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
Aruba-AOS-CX (new style) specific implementation of the SNMP object
Note that the SNMP implementation in AOS-CX switches is read-only.
We will implement many features via the REST API of the product, See
https://developer.arubanetworks.com/aruba-aoscx/docs/python-getting-started
This will be done as part of the 'Aruba-AOS' configuration type, coded in
/switches/connect/aruba_aoscx/

Update June 2022:
per https://www.arubanetworks.com/techdocs/AOS-CX/10.08/PDF/snmp_mib.pdf
on pg. 46, OIDs that support SNMP write, write is supported to
ifAdminStatus (ie interface up/down), and pethPsePortAdminEnable (ie. PoE enable/disable)
"""
# from pysnmp.proto.rfc1902 import OctetString, Gauge32
# import traceback
from django.http.request import HttpRequest

# from switches.connect.classes import PortList
from switches.connect.classes import Interface
from switches.connect.snmp.connector import SnmpConnector, oid_in_branch
from switches.connect.snmp.constants import dot1qPvid
from switches.models import Switch, SwitchGroup
from switches.utils import dprint

from switches.connect.snmp.aruba_cx.constants import (
    arubaWiredPoePethPsePortPowerDrawn,
    arubaWiredVsfv2MemberProductName,
    arubaWiredVsfv2ConfigOperationType,
    arubaWiredVsfv2ConfigOperationSetSource,
    arubaWiredVsfv2ConfigOperationSetDestination,
    ARUBA_CONFIG_ACTION_WRITE,
    ARUBA_CONFIG_TYPE_STARTUP,
    ARUBA_CONFIG_TYPE_RUNNING,
)


class SnmpConnectorArubaCx(SnmpConnector):
    """
    Aruba AOS-CX specific implementation of the SNMP object,
    for now a derivative of the default SNMP connector.
    """

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        # for now, just call the super class
        dprint("Aruba SnmpConnector __init__")
        super().__init__(request, group, switch)
        self.description = 'Aruba Networks AOS-CX SNMP driver'
        self.vendor_name = "Aruba Networks (AOS-CX)"
        # self.switch.read_only = (
        #     False  # the new Aruba AOS switches support some R/W over SNMP. Full Write-access is via REST API.
        # )
        self.can_reload_all = True  # if true, we can reload all our data (and show a button on screen for this)
        # all firmware versions support admin-status and poe-status change via snmp:
        self.can_change_admin_status = True
        self.can_change_poe_status = True
        # firmware v10.09 allows description change via snmp
        # see https://www.arubanetworks.com/techdocs/AOS-CX/10.09/PDF/snmp_mib.pdf
        self.can_change_description = True
        # firmware v10.10 allow "save startup-config running-config" via snmp
        # see https://www.arubanetworks.com/techdocs/AOS-CX/10.10/PDF/snmp_mib.pdf
        self.can_save_config = True
        # firmware v10.12 allows interface vlan change, and vlan add/delete via snmp
        # see https://www.arubanetworks.com/techdocs/AOS-CX/10.12/PDF/snmp_mib.pdf
        self.can_change_vlan = True
        self.can_set_vlan_name = False  # vlan create/delete allowed over snmp, but cannot set name!

        # Netmiko is used for SSH connections. Here are some defaults a class can set.
        #
        # device_type:
        #   if set, will be a value that will override (ie. hardcode) values from the
        #   "Credentials Profile" (aka the NetmikoProfile() object)
        self.netmiko_device_type = "aruba_aoscx"
        # no need to override default of netmiko_valid_device_types[]
        #
        # the command that should be sent to disable screen paging
        # let Netmiko decide this...
        # self.netmiko_disable_paging_command = "no page"
        # even though there is now a Netmiko 'aruba_aoscx' driver, we still see prompt time-outs.
        # setting this to True disables prompt checking, and uses send_command_timing() calls.
        self.netmiko_ignore_prompt = True

        # we recommend using the AOS-CX API driver, tell the user so:
        self.add_warning(
            warning="We recommend using the AOS-CX API driver for this device. Please contact your OpenL2M administrator!",
            add_log=False,
        )

    def _parse_mibs_aruba_poe(self, oid: str, val: str) -> bool:
        """
        Parse Aruba's ARUBAWIRED-POE Mibs
        """
        dprint(f"_parse_mibs_aruba_poe() {oid} = {val}")
        pe_index = oid_in_branch(arubaWiredPoePethPsePortPowerDrawn, oid)
        if pe_index:
            dprint(f"Found branch arubaWiredPoePethPsePortPowerDrawn, pe_index = {pe_index}")
            if pe_index in self.poe_port_entries.keys():
                self.poe_port_entries[pe_index].power_consumption_supported = True
                self.poe_port_entries[pe_index].power_consumed = int(val)
            return True

        return False

    def _parse_mibs_aruba_vsf2(self, oid: str, val: str) -> bool:
        """
        Parse ARUBAWIRED-VSFv2 mibs.
        """
        dprint(f"_parse_mibs_aruba_vsf2() {oid} = {val}")
        dev_index = int(oid_in_branch(arubaWiredVsfv2MemberProductName, oid))
        if dev_index:
            dprint(f"Found branch arubaWiredVsfv2MemberProductName, device index = {dev_index}, val = {val}")
            # add to device/stacking info area:
            dprint(f"Device {dev_index}: {val}")
            # save this info!
            if dev_index in self.stack_members.keys():
                # save this info!
                self.stack_members[dev_index].info = val
            else:
                # should not happen:
                dprint(" ERROR: Device Index NOT found in StackMembers!")
            return True

        return False

    def _get_poe_data(self) -> int:
        """
        Aruba(HP) used both the standard PoE MIB, and their own ARUBAWIRED-POE mib.
        """
        # get standard data first, this loads PoE status, etc.
        super()._get_poe_data()
        # if we found power supplies, get Aruba specific info about power usage from ARUBAWIRED-POE mib
        if self.poe_capable:
            retval = self.get_snmp_branch(
                branch_name='arubaWiredPoePethPsePortPowerDrawn', parser=self._parse_mibs_aruba_poe
            )
            if retval < 0:
                self.add_warning(warning="Error getting 'PoE-Port-Actual-Power' (arubaWiredPoePethPsePortPowerDrawn)")

        return 1

    def _get_vlan_data(self) -> int:
        """
        Implement an override of vlan parsing to read Cisco specific MIB
        Get all neccesary vlan info (names, id, ports on vlans, etc.) from the switch.
        Returns -1 on error, or number to indicate vlans found.
        """
        dprint("_get_vlan_data(ArubaAosCx)\n")

        # first, Aruba vlan names
        retval = self.get_snmp_branch('ieee8021QBridgeVlanStaticName', self._parse_mibs_ieee_qbridge_vlan_static_name)
        if retval < 0:
            return retval
        # set vlan count
        self.vlan_count = len(self.vlans)

        # port PVID untagged vlan
        retval = self.get_snmp_branch(branch_name='ieee8021QBridgePvid', parser=self._parse_mibs_ieee_qbridge_pvid)
        if retval < 0:
            return retval

        # get the generic vlan data:
        super()._get_vlan_data()

        # Note: as of v10.13, AOS-CX does NOT use "dot1qVlanCurrentEgressPorts" to define
        # vlan port membership. Instead it uses the IEEE Q-Bridge equivalents at
        # "ieee8021QBridgeVlanCurrentEgressPorts" and "ieee8021QBridgeVlanCurrentUntaggedPorts" !

        # AOS-CX uses the ieee802.1 Q-Bridge mibs for interface vlan info on trunked ports:
        # read ports in vlans
        retval = self.get_snmp_branch(
            branch_name='ieee8021QBridgeVlanCurrentEgressPorts',
            parser=self._parse_mibs_ieee_qbridge_vlan_current_egress_ports,
        )
        if retval < 0:
            return retval
        # and get untagged ports in those vlans:
        retval = self.get_snmp_branch(
            branch_name='ieee8021QBridgeVlanCurrentUntaggedPorts',
            parser=self._parse_mibs_ieee_qbridge_vlan_current_untagged_ports,
        )
        if retval < 0:
            return retval

        # this adds no new information:
        # # and get dot1qVlanStaticUntaggedPorts, this could have some more untagged vlan info on tagged ports.
        # retval = self.get_snmp_branch(branch_name='dot1qVlanStaticUntaggedPorts', parser=self._parse_mibs_vlan_related)
        # if retval < 0:
        #     self.add_warning(warning="Error getting 'Q-Bridge-Vlan-Static-Ports' (dot1qVlanStaticUntaggedPorts)")
        #     return retval

        return self.vlan_count

    def get_my_hardware_details(self) -> bool:
        """
        Load hardware details from the VSF v2 mib (Virtual Switch Fabric)
        then call the generic SNMP hardware details.
        """
        super().get_my_hardware_details()

        # now read AOS-CX specific data:
        retval = self.get_snmp_branch(
            branch_name='arubaWiredVsfv2MemberProductName', parser=self._parse_mibs_aruba_vsf2
        )
        if retval < 0:
            self.add_warning(warning="Error getting 'Aruba Vsf Product name' ('arubaWiredVsfv2MemberProductName')")
            return False
        return True

    def set_interface_untagged_vlan(self, interface: Interface, new_vlan_id: int) -> bool:
        """
        Change the VLAN via the Q-BRIDGE MIB (ie generic)
        return True on success, False on error and set self.error variables
        """
        dprint(f"AosCxSnmpConnector.set_interface_untagged_vlan(intf-index={interface.index}, vlan={new_vlan_id})")
        if not interface:
            dprint("  Invalid interface!, returning False")
            return False
        # does this vlan exist on the device?
        if new_vlan_id not in self.vlans.keys():
            dprint(f"  Invalid new vlan {new_vlan_id}, returning False")
            return False
        # set this switch port on the new vlan:
        if interface.is_tagged:
            # if the vlan is allowed in the trunk, then we simply set the PVID.
            if new_vlan_id in interface.vlans:
                dprint("  New vlan allowed in TRUNK, setting PVID")
                if not self.set(
                    oid=f"{dot1qPvid}.{interface.index}",
                    value=int(new_vlan_id),
                    snmp_type='u',
                    parser=self._parse_mibs_vlan_related,
                ):
                    dprint("   ERROR!")
                    return False
                return True
            else:
                # this needs work!
                self.error.status = True
                self.error.description = f"Vlan {new_vlan_id} is not allowed on this trunk port."
                self.error.details = "We cannot yet change the untagged vlan if this is not allowed on the trunk!"
                dprint("  ERROR: New vlan NOT allowed on TRUNK!")
                return False

                # # need to add this vlan to the trunk vlans, by setting bit to 1.
                # # get the current list of static ports on this vlan:
                # egress_oid = f"{ieee8021QBridgeVlanStaticEgressPorts}.1.{new_vlan_id}"
                # (error_status, retval) = self.get(oid=egress_oid, parser=self._parse_mibs_vlan_related)
                # if error_status:
                #     dprint(f"Error getting SNMP value for 'ieee8021QBridgeVlanStaticEgressPorts': {self.error.details}")
                #     return False
                # # get the return value into a port list:
                # dprint(f"Portlist size is {len(str(retval))} bytes")
                # egress_portlist = PortList()
                # egress_portlist.from_unicode(str(retval))
                # # now set the bit for this port
                # egress_portlist[int(interface.index)] = 1
                # # and atomically set both the egress port list, and the pvid OIDs:
                # pvid_oid_val = (f"{dot1qPvid}.{interface.index}", Gauge32(new_vlan_id))
                # egress_oid_val = (egress_oid, OctetString(hexValue=egress_portlist.to_hex_string()), )
                # # get the PySNMP helper to do the work with the OctetString() BitMaps:
                # try:
                #     pysnmp = pysnmpHelper(self.switch)
                # except Exception as err:
                #     self.error.status = True
                #     self.error.description = "Error getting snmp connection object (pysnmpHelper())"
                #     self.error.details = f"Caught Error: {repr(err)} ({str(type(err))})\n{traceback.format_exc()}"
                #     return False

                # if not pysnmp.set_multiple([egress_oid_val, pvid_oid_val]):
                #     self.error.status = True
                #     self.error.description = f"Error setting vlan '{new_vlan_id}' on tagged port!"
                #     # copy over the error details from the call:
                #     self.error.details = pysnmp.error.details
                #     # we leave self.error.details as is!
                #     return False

        else:
            dprint("Setting NEW VLAN on ACCESS port")
            if not self.set(
                oid=f"{dot1qPvid}.{interface.index}",
                value=int(new_vlan_id),
                snmp_type='u',
                parser=self._parse_mibs_vlan_related,
            ):
                dprint("   ERROR!")
                return False
        return True

    def save_running_config(self) -> bool:
        """
        Aruba Aos-Cx interface to save the current config to startup via SNMP
        For details on how this works, see firmware v10.10 and above,
        read https://www.arubanetworks.com/techdocs/AOS-CX/10.10/PDF/snmp_mib.pdf
        Returns True is this succeeds, False on failure. self.error() will be set in that case
        """
        dprint("save_running_config(AOS-CX)")

        # According to page 12 of https://www.arubanetworks.com/techdocs/AOS-CX/10.13/PDF/snmp_mib.pdf
        # this implementes "copy running-config startup-config" using SNMP.
        retval = self.set_multiple(
            [
                (arubaWiredVsfv2ConfigOperationType, ARUBA_CONFIG_ACTION_WRITE, 'i'),
                (arubaWiredVsfv2ConfigOperationSetSource, ARUBA_CONFIG_TYPE_RUNNING, 'i'),
                (arubaWiredVsfv2ConfigOperationSetDestination, ARUBA_CONFIG_TYPE_STARTUP, 'i'),
            ]
        )
        if retval < 0:
            dprint(f"  return = {retval}")
            self.add_warning(warning="Error saving via SNMP (arubaWiredVsfv2ConfigOperation)")
            return False
        dprint("  All OK")
        return True
