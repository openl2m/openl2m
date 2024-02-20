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
HPE/3Com ComWare specific implementation of the SNMP object
This re-implements some methods found in the base SNMP() class
with HH3C specific ways of doing things...
"""
import datetime
import math
import traceback

from pysnmp.proto.rfc1902 import OctetString, Gauge32

from switches.models import Log
from switches.constants import LOG_TYPE_ERROR, LOG_PORT_POE_FAULT
from switches.connect.classes import PortList
from switches.connect.constants import IF_TYPE_ETHERNET, POE_PORT_DETECT_DELIVERING, poe_status_name
from switches.connect.snmp.connector import pysnmpHelper, SnmpConnector, oid_in_branch
from switches.connect.snmp.constants import SNMP_TRUE, dot1qPvid
from switches.utils import dprint, get_remote_ip

from .constants import (
    BYTES_FOR_2048_VLANS,
    HH3C_IF_MODE_INVALID,
    HH3C_IF_MODE_TRUNK,
    HH3C_IF_MODE_HYBRID,
    HH3C_IF_MODE_FABRIC,
    HH3C_ROUTE_MODE,
    hh3cifVLANTrunkAllowListLow,
    hh3cifVLANTrunkAllowListHigh,
    hh3cdot1qVlanPorts,
    hh3cCfgRunModifiedLast,
    hh3cCfgRunSavedLast,
    hh3cCfgStartModifiedLast,
    hh3cPsePortCurrentPower,
    hh3cdot1qVlanName,
    hh3cifVLANType,
    hh3cIfLinkMode,
    hh3cCfgOperateRowStatus,
    hh3cCfgOperateType,
    HH3C_running2Startup,
    HH3C_createAndGo,
    hh3cIgmpSnoopingVlanEnabled,
)


class SnmpConnectorComware(SnmpConnector):
    """
    HP/3Com specific implementation of the SNMP object
    This re-implements some methods found in the base SNMP() class
    with H3C specific ways of doing things...
    """

    def __init__(self, request, group, switch):
        # for now, just call the super class
        dprint("Comware SnmpConnector __init__")
        super().__init__(request, group, switch)
        self.description = 'HPE Comware SNMP driver'
        self.vendor_name = "HPE (Comware)"
        self.can_save_config = True
        # needed for saving config file:
        self.active_config_rows = 0

        """
        # capabilities of the Comware snmp driver are identical to the snmp driver:
        self.can_change_admin_status = True
        self.can_change_vlan = True
        self.can_change_poe_status = True
        self.can_change_description = True
        self.can_save_config = True    # do we have the ability (or need) to execute a 'save config' or 'write memory' ?
        self.can_reload_all = True      # if true, we can reload all our data (and show a button on screen for this)
        """

    def _get_interface_data(self):
        """
        Implement an override of the interface parsing routine,
        so we can add Comware specific interface MIBs
        """
        # first call the base class to populate interfaces:
        super()._get_interface_data()

        # now add Comware data, and cache it:
        if self.get_snmp_branch('hh3cIfLinkMode', self._parse_mibs_comware_if_linkmode) < 0:
            dprint("Comware hh3cIfLinkMode returned error!")
            return False

        return True

    def _get_max_qbridge_port_id(self):
        """
        Get the maximum value of the switchport id, for physical ports.
        Used for bitmap/byte sizing.
        Returns integer
        """
        max_port_id = 0
        for iface in self.interfaces.values():
            if iface.type == IF_TYPE_ETHERNET and iface.port_id > max_port_id:
                max_port_id = iface.port_id
        return max_port_id

    def _get_vlan_data(self):
        """
        Implement an override of vlan parsing to read Comware specific MIB
        """
        dprint("Comware _get_vlan_data()\n")

        # read some Comware specific items.
        # some Comware switches do not report vlan names in Q-Bridge mib
        # so read HH3C version
        if self.get_snmp_branch('hh3cdot1qVlanName', self._parse_mibs_comware_vlan) < 0:
            dprint("Comware hh3cdot1qVlanName returned error!")
            self.add_warning("Error getting 'HH3C-Vlan-Names' (hh3cdot1qVlanName)")

        # call the standard vlan reader
        super()._get_vlan_data()

        # read the Comware port type:
        if self.get_snmp_branch('hh3cifVLANType', self._parse_mibs_comware_if_type) < 0:
            dprint("Comware hh3cifVLANType returned error!")
            self.add_warning("Error getting 'HH3C-Vlan-Types' (hh3cifVLANType)")

        # for each vlan, PortList bitmap of untagged ports
        """  NOT PARSED YET:
        if self.get_snmp_branch('hh3cdot1qVlanPorts') < 0:
            dprint("Comware hh3cdot1qVlanPorts returned error!")
        """

        # tagged vlan types are next
        # if not self.get_snmp_branch('hh3cifVLANTrunkAllowListLow'):
        #    dprint("Comware Low VLAN PortList FALSE")
        #    return False
        # next, read vlan names
        # if not self.get_snmp_branch('hh3cifVLANTrunkAllowListHigh'):
        #    dprint("Comware High VLAN PortList FALSE")
        #    return False

        # read IGMP-snooping for vlans:
        if self.get_snmp_branch('hh3cIgmpSnoopingVlanEnabled', self._parse_mibs_comware_vlan_igmp) < 0:
            dprint("hh3cIgmpSnoopingVlanEnabled returned error!")
            self.add_warning("Error getting 'HH3C-Vlan-IGMP-Info' (hh3cIgmpSnoopingVlanEnabled)")

        return True

    def get_my_hardware_details(self):
        """
        Implement the get_my_hardware_details() called from from the base object get_hardware_details()
        Does not return anything!
        """
        # dprint("Comware get_my_hardware_details()")
        super().get_my_hardware_details()

        # now read Comware specific data:
        retval = self.get_snmp_branch('hh3cCfgLog', self._parse_mibs_comware_config)
        if retval < 0:
            self.add_warning("Error getting Comware log details ('hh3cCfgLog')")
            return False
        return True

    def set_interface_untagged_vlan(self, interface, new_vlan_id):
        """
        Override the VLAN change, this is done Comware specific using the Comware VLAN MIB
        return True on success, False on error and set self.error variables
        """
        dprint(f"Comware set_interface_untagged_vlan() port {interface.name} to {new_vlan_id} ({type(new_vlan_id)})")
        new_vlan = self.get_vlan_by_id(new_vlan_id)
        if not new_vlan:
            self.error.status = True
            self.error.description = f"Cannot find Vlan object for vlan {new_vlan_id}"
            self.error.details = ""
            return False
        if interface:
            if interface.is_tagged:
                dprint("Tagged/Trunk Mode!")
                # set the TRUNK_NATIVE_VLAN OID:
                low_vlan_list = PortList()
                low_vlan_list.from_byte_count(BYTES_FOR_2048_VLANS)
                high_vlan_list = PortList()
                high_vlan_list.from_byte_count(BYTES_FOR_2048_VLANS)
                # add the new vlan id:
                if new_vlan_id > 2048:
                    # set the propper bit, adjust by the offset!
                    high_vlan_list[new_vlan_id - 2048] = 1
                else:
                    low_vlan_list[new_vlan_id] = 1
                # now loop through all vlans in this port and set the bit for the vlan:
                for vlan in interface.vlans:
                    if vlan > 2048:
                        # set the propper bit, adjust by the offset!
                        high_vlan_list[vlan - 2048] = 1
                    else:
                        low_vlan_list[vlan] = 1

                # now setup the OIDs to send as an atomic set:
                # first set Low-VLANs (1-2048) on this port:
                # Comware needs bits in opposite order inside each byte! (go figure)
                # note that to_hex_string() is same as .__str__ representation,
                # but we use it for extra clarity!
                low_vlan_list.reverse_bits_in_bytes()
                low_oid = (
                    f"{hh3cifVLANTrunkAllowListLow}.{interface.port_id}",
                    OctetString(hexValue=low_vlan_list.to_hex_string()),
                )

                # next High-VLANs (2049-4096) on this port:
                # Comware needs bits in opposite order inside each byte! (go figure)
                high_vlan_list.reverse_bits_in_bytes()
                high_oid = (
                    f"{hh3cifVLANTrunkAllowListHigh}.{interface.port_id}",
                    OctetString(hexValue=high_vlan_list.to_hex_string()),
                )

                # finally, set untagged vlan:  dot1qPvid
                pvid_oid = (f"{dot1qPvid}.{interface.port_id}", Gauge32(new_vlan_id))

                # now send them all as an atomic set():
                # get the PySNMP helper to do the work with the OctetString() BitMaps:
                try:
                    pysnmp = pysnmpHelper(self.switch)
                except Exception as err:
                    self.error.status = True
                    self.error.description = "Error getting snmp connection object (pysnmpHelper())"
                    self.error.details = f"Caught Error: {repr(err)} ({str(type(err))})\n{traceback.format_exc()}"
                    return False

                if not pysnmp.set_multiple([low_oid, high_oid, pvid_oid]):
                    self.error.status = True
                    self.error.description = f"Error setting vlan '{new_vlan_id}' on tagged port!"
                    # copy over the error details from the call:
                    self.error.details = pysnmp.error.details
                    # we leave self.error.details as is!
                    return False

            else:
                # regular access mode untagged port:
                dprint("Acces Mode!")
                # create a PortList() to represent the ports/bits that are in the new vlan.
                # we need byte size from number of ethernet ports:
                max_port_id = self._get_max_qbridge_port_id()
                bytecount = math.ceil(max_port_id / 8)
                dprint(f"max_port_id = {max_port_id}, bytecount = {bytecount}")
                new_vlan_portlist = PortList()
                # initialize with "00" bytes
                new_vlan_portlist.from_byte_count(bytecount)
                # now set bit to 1 for this interface (i.e. set the port_id bit!):
                dprint(f"interface.port_id = {interface.port_id}")
                new_vlan_portlist[int(interface.port_id)] = 1

                """
                # next, read current Egress PortList bitmap first:
                # note the 0 to hopefull deactivate time filter!
                (error_status, snmpval) = self.get(f"{dot1qVlanCurrentEgressPorts}.0.{new_vlan_id}")
                if error_status:
                    # Hmm, not sure what to do
                    self.error.status = True
                    self.error.description = "Error retrieving new vlan member portlist (dot1qVlanCurrentEgressPorts)"
                    return -1
                # now calculate new bitmap by removing this switch port
                current_egress_portlist = PortList()
                current_egress_portlist.from_unicode(snmpval.value)
                """

                # now loop to find other existing ports on this vlan:
                dprint("Finding other ports on this vlan:")
                for this_iface in self.interfaces.values():
                    if this_iface.type == IF_TYPE_ETHERNET:
                        if this_iface.port_id > -1:  # we have a valid PortId
                            if this_iface.is_tagged:
                                # tagged interface
                                # is the new vlanId active on this port (i.e. PVID or on trunk) ?
                                if (this_iface.untagged_vlan == new_vlan_id) or (new_vlan_id in this_iface.vlans):
                                    dprint(
                                        f"   Tagged on VLAN: {this_iface.name} port {this_iface.port_id}, Vlan dict: {this_iface.vlans}"
                                    )
                                    # is this port in Current Egress PortList?
                                    # if not, do NOT add!
                                    # this can happen with a PVID set on a port in trunk mode, but
                                    # the trunk does not allow that vlan! (edge use case)
                                    if self.vlans[new_vlan_id].current_egress_portlist[this_iface.port_id]:
                                        dprint("  and in allow list, adding!")
                                        new_vlan_portlist[this_iface.port_id] = 1
                                    """
                                    if current_egress_portlist[this_iface.port_id]:
                                        # dprint("  and in allow list!")
                                        new_vlan_portlist[this_iface.port_id] = 1
                                    """
                            else:
                                # untagged on this new vlanId ?
                                if this_iface.untagged_vlan == new_vlan_id:
                                    dprint(f"  Untagged {this_iface.name} Port PVID added to new vlan!")
                                    new_vlan_portlist[this_iface.port_id] = 1
                        else:
                            # no switchport? "should" not happen for a valid switch port interface
                            warning = f"Warning: {this_iface.name} - no port_id found in set_interface_untagged_vlan(Comware)!"
                            self.add_warning(warning)

                # send to the switch!
                # Comware needs bits in opposite order inside each byte! (go figure)
                new_vlan_portlist.reverse_bits_in_bytes()
                # get the PySNMP helper to do the work with this BitMap:
                # note that to_hex_string() is same as .__str__ representation,
                # but we use it for extra clarity!
                octet_string = OctetString(hexValue=new_vlan_portlist.to_hex_string())
                try:
                    pysnmp = pysnmpHelper(self.switch)
                except Exception as err:
                    self.error.status = True
                    self.error.description = "Error getting snmp connection object (pysnmpHelper())"
                    self.error.details = f"Caught Error: {repr(err)} ({str(type(err))})\n{traceback.format_exc()}"
                    return False

                dprint("Setting via pysnmpHelper()")
                if not pysnmp.set(f"{hh3cdot1qVlanPorts}.{new_vlan_id}", octet_string):
                    self.error.status = True
                    self.error.description = f"Error setting vlan '{new_vlan_id}' on access port!"
                    # copy over the error details from the call:
                    self.error.details = pysnmp.error.details
                    return False

            # now trick the next switch view into showing this as the vlan on the interface
            # without the need to re-read SNMP data! We could also just read it here :-)
            # self._parse_oid(QBRIDGE_VLAN_IFACE_UNTAGGED_PVID + "." + str(if_index), str(new_vlan_id), 'u')

            # now we need to reread the interface to VLAN mib part
            dprint("Re-reading vlan membership")
            self._get_port_vlan_membership()
            return True
        # interface not found, return False!
        return False

    def _can_manage_interface(self, iface):
        """
        vendor-specific override of function to check if this interface can be managed.
        We check for IRF ports here. This is detected via 'hh3cifVLANType' MIB value,
        in _parse_mibs_comware_if_type()
        Returns True for normal interfaces, but False for IRF ports.
        """
        if iface.type == IF_TYPE_ETHERNET:
            if iface.if_vlan_mode <= HH3C_IF_MODE_INVALID:
                # dprint(f"Interface {iface.name}: mode={iface.if_vlan_mode}, NO MANAGEMENT ALLOWED!")
                iface.unmanage_reason = "Access denied: interface in IRF (stacking) mode!"
                return False
            if iface.if_vlan_mode == HH3C_IF_MODE_HYBRID or iface.if_vlan_mode == HH3C_IF_MODE_FABRIC:
                iface.unmanage_reason = "Access denied: interface in Hybrid or Fabric mode!"
                return False
        return True

    def _parse_mibs_comware_config(self, oid, val):
        """
        Parse Comware specific ConfigMan MIB
        Mostly entries under 'hh3cCfgLog'
        return True if we parse it, False if not.
        """
        sub_oid = oid_in_branch(hh3cCfgRunModifiedLast, oid)
        if sub_oid:
            ago = str(datetime.timedelta(seconds=(int(val) / 100)))
            self.add_more_info("Configuration", "Running Last Modified", ago)
            return True

        sub_oid = oid_in_branch(hh3cCfgRunSavedLast, oid)
        if sub_oid:
            ago = str(datetime.timedelta(seconds=(int(val) / 100)))
            self.add_more_info("Configuration", "Running Last Saved", ago)
            return True

        sub_oid = oid_in_branch(hh3cCfgStartModifiedLast, oid)
        if sub_oid:
            ago = str(datetime.timedelta(seconds=(int(val) / 100)))
            self.add_more_info("Configuration", "Startup Last Saved", ago)
            return True

        return False

    """
    the HH3C-POWER-ETH MIB tables with port-level PoE power usage info
    OID is followed by PortEntry index (pe_index). This is typically
    or module_num.port_num for modules switch chassis, or
    device_id.port_num for stack members.
    This gets mapped to an interface later on in
    self._map_poe_port_entries_to_interface(), which is typically device specific
    """

    def _parse_mibs_comware_poe(self, oid, val):
        """
        Parse the Comware extended HH3C-POWER-ETH MIB, power usage extension
        return True if we parse it, False if not.
        """
        dprint(f"_parse_mibs_comware_poe() {oid}, len = {val}, type = {type(val)}")
        pe_index = oid_in_branch(hh3cPsePortCurrentPower, oid)
        if pe_index:
            if pe_index in self.poe_port_entries.keys():
                self.poe_port_entries[pe_index].power_consumption_supported = True
                self.poe_port_entries[pe_index].power_consumed = int(val)
            return True

        return False

    def _parse_mibs_comware_vlan(self, oid, val):
        """
        Parse Comware specific VLAN MIB
        return True if we parse it, False if not.
        """
        vlan_id = int(oid_in_branch(hh3cdot1qVlanName, oid))
        if vlan_id > 0:
            if vlan_id not in self.vlans.keys():
                # define vlan:
                self.add_vlan_by_id(vlan_id)
            # some Comware switches only report "VLAN xxxx", skip that!
            if not val.startswith('VLAN '):
                self.vlans[vlan_id].name = val
            return True
        return False

    def _parse_mibs_comware_vlan_igmp(self, oid, val):
        """
        Parse Comware specific VLAN IGMP mib
        return True if we parse it, False if not.
        """
        vlan_id = int(oid_in_branch(hh3cIgmpSnoopingVlanEnabled, oid))
        if vlan_id > 0:
            # this vlan has IMGP snooping enabled.
            if vlan_id in self.vlans.keys():
                if int(val) == SNMP_TRUE:
                    self.vlans[vlan_id].igmp_snooping = True
            return True
        return False

    def _parse_mibs_comware_if_type(self, oid, val):
        """
        Parse Comware specific Interface Type MIB
        return True if we parse it, False if not.
        """
        if_index = oid_in_branch(hh3cifVLANType, oid)
        if if_index:
            dprint(f"Comware if_index {if_index} if_type {val}")
            self.set_interface_attribute_by_key(if_index, "if_vlan_mode", int(val))
            if int(val) == HH3C_IF_MODE_TRUNK:
                self.set_interface_attribute_by_key(if_index, "is_tagged", True)
            return True
        return False

    def _parse_mibs_comware_if_linkmode(self, oid, val):
        """
        Parse Comware specific Interface Extension MIB for link mode
        return True if we parse it, False if not.
        """
        if_index = oid_in_branch(hh3cIfLinkMode, oid)
        if if_index:
            dprint(f"Comware LinkMode if_index {if_index} link_mode {val}")
            if int(val) == HH3C_ROUTE_MODE:
                self.set_interface_attribute_by_key(if_index, "is_routed", True)
            return True
        return False

    def _parse_mibs_comware_configfile(self, oid, val):
        """
        Parse Comware specific ConfigMan MIB
        return True if we parse it, False if not.
        """
        dprint("_parse_mibs_comware_configfile(Comware)")
        sub_oid = oid_in_branch(hh3cCfgOperateRowStatus, oid)
        if sub_oid:
            if int(sub_oid) > self.active_config_rows:
                self.active_config_rows = int(sub_oid)
            return True

    def _get_poe_data(self):
        """
        Get PoE data, first via the standard PoE MIB,
        then by calling the Comware extended HH3C-POWER-ETH MIB
        """
        super()._get_poe_data()
        # now get HP specific info from HP-IFC-POE-MIB first
        retval = self.get_snmp_branch('hh3cPsePortCurrentPower', self._parse_mibs_comware_poe)
        if retval < 0:
            self.add_warning("Error getting 'PoE-Port-Current-Power' (hh3cPsePortCurrentPower)")
        return 1

    def _map_poe_port_entries_to_interface(self):
        """
        This function maps the "pethPsePortEntry" indices that are stored in self.poe_port_entries{}
        to interface ifIndex values, so we can store them with the interface and display as needed.
        For Comware IRF stack, the mapping appears to be <pse#>.<port#>, where
        PSE# = 1 + (3 x stack member number)
        Port# = Q-Bridge-Port# as found in the Q-bridge MIB.
        (It is also possible that Port# is the ifIndex directly; so far on all comware PoE devices we
         tested, the ifIndex and Q-Bridge port ID are the same!)
        """
        dprint("_map_poe_port_entries_to_interface(Comware)")
        for port_entry in self.poe_port_entries.values():
            # we take the ending part of "7.12", where 7=PSE#, and 12=port!
            (pse_module, port) = port_entry.index.split('.')
            # calculate the stack member number from PSE#
            member = int((int(pse_module) - 1) / 3)
            if_index = self._get_if_index_from_port_id(int(port))
            dprint(f"  Entry for member {member}, index {if_index}")
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
                    break

    def save_running_config(self):
        """
        HP/3COM interface to save the current config to startup via SNMP
        For details on how this works, see
        http://www.h3c.com.hk/products___solutions/technology/system_management/configuration_example/200912/656452_57_0.htm
        or Google the H3C file
        "Configuration_Examples_for_Configuration_File_Management_Using_SNMP.pdf"
        see page 11!
        Returns True is this succeeds, False on failure. self.error() will be set in that case
        """
        dprint("save_running_config(Comware)")

        # According to the
        # run the Operations row status to find free slot to write to:
        retval = self.get_snmp_branch('hh3cCfgOperateRowStatus', self._parse_mibs_comware_configfile)
        if retval < 0:
            self.add_warning("Error reading 'Config File MIB' (hh3cCfgOperateRowStatus)")
            return False

        # now figure out where we need to write to
        row_place = self.active_config_rows + 1
        # set_multiple() needs a list of tuples(oid, value, type)
        dprint(f"row_place = {row_place}")
        retval = self.set_multiple(
            [
                (f"{hh3cCfgOperateType}.{row_place}", HH3C_running2Startup, 'i'),
                (f"{hh3cCfgOperateRowStatus}.{row_place}", HH3C_createAndGo, 'i'),
            ]
        )
        if retval < 0:
            dprint(f"return = {retval}")
            self.add_warning("Error saving via SNMP (hh3cCfgOperateRowStatus)")
            return False
        dprint("All OK")
        return True
