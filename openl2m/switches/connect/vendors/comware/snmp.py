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
from pysnmp.proto.rfc1902 import ObjectName, OctetString, Gauge32

from switches.models import Log
from switches.constants import *
from switches.connect.classes import *
from switches.connect.snmp import pysnmpHelper, SnmpConnector, oid_in_branch
from switches.connect.constants import *
from switches.connect.netmiko.netmiko import *
from switches.utils import *

from .constants import *


class SnmpConnectorComware(SnmpConnector):
    """
    HP/3Com specific implementation of the SNMP object
    This re-implements some methods found in the base SNMP() class
    with H3C specific ways of doing things...
    """

    def __init__(self, request, group, switch):
        # for now, just call the super class
        dprint("Comware SnmpConnector __init__")
        SnmpConnector.__init__(self, request, group, switch)
        self.name = "Comware SnmpConnector"  # what type of class is running!
        self.vendor_name = "HPE/Comware"
        # needed for saving config file:
        self.active_config_rows = 0

    def _parse_oid(self, oid, val):
        """
        Parse a single OID with data returned from a switch through some "get" function
        Returns True if we parse the OID!
        """
        dprint("Comware Parsing OID %s" % oid)

        if self._parse_mibs_comware_poe(oid, val):
            return True
        if self._parse_mibs_comware_config(oid, val):
            return True
        if self._parse_mibs_comware_vlan(oid, val):
            return True
        if self._parse_mibs_comware_if_type(oid, val):
            return True
        # call the generic base parser
        return SnmpConnector._parse_oid(self, oid, val)

    def _get_vlan_data(self):
        """
        Implement an override of vlan parsing to read Comware specific MIB
        """
        dprint("Comware _get_vlan_data()\n")
        # first, call the standard vlan reader
        SnmpConnector._get_vlan_data(self)

        # now read some Comware specific items.
        # some Comware switches do not report vlan names in Q-Bridge mib
        # so read HH3C version
        if self._get_branch_by_name('hh3cdot1qVlanName', True, self._parse_mibs_comware_vlan) < 0:
            dprint("Comware hh3cdot1qVlanName returned error!")
            return False

        # read the COmware port type:
        if self._get_branch_by_name('hh3cifVLANType', True, self._parse_mibs_comware_if_type) < 0:
            dprint("Comware hh3cifVLANType returned error!")
            return False

        # for each vlan, PortList bitmap of untagged ports
        """  NOT PARSED YET:
        if self._get_branch_by_name('hh3cdot1qVlanPorts') < 0:
            dprint("Comware hh3cdot1qVlanPorts returned error!")
            return False
        """

        # tagged vlan types are next
        # if not self._get_branch_by_name('hh3cifVLANTrunkAllowListLow'):
        #    dprint("Comware Low VLAN PortList FALSE")
        #    return False
        # next, read vlan names
        # if not self._get_branch_by_name('hh3cifVLANTrunkAllowListHigh'):
        #    dprint("Comware High VLAN PortList FALSE")
        #    return False
        return True

    def _get_vendor_data(self):
        """
        Implement the get_vendor_data() class from the base object
        """
        dprint("Comware _get_vendor_data()")
        self._get_branch_by_name('hh3cCfgLog', True, self._parse_mibs_comware_config)

    def set_interface_untagged_vlan(self, if_index, old_vlan_id, new_vlan_id):
        """
        As an example, Override the VLAN change, this is done Comware specific using the Comware VLAN MIB
        Return -1 if invalid interface, or value of _set() call
        """
        dprint("Comware set_interface_untagged_vlan()")
        iface = self.get_interface_by_index(if_index)
        new_vlan = self.get_vlan_by_id(new_vlan_id)
        if iface and new_vlan:
            if iface.is_tagged:
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
                for vlan in iface.vlans:
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
                low_oid = ("%s.%s" % (snmp_mib_variables['hh3cifVLANTrunkAllowListLow'], str(iface.port_id)),
                           OctetString(hexValue=low_vlan_list.to_hex_string()))

                # next High-VLANs (2049-4096) on this port:
                # Comware needs bits in opposite order inside each byte! (go figure)
                high_vlan_list.reverse_bits_in_bytes()
                high_oid = ("%s.%s" % (snmp_mib_variables['hh3cifVLANTrunkAllowListHigh'], str(iface.port_id)),
                            OctetString(hexValue=high_vlan_list.to_hex_string()))

                # finally, set untagged vlan:  dot1qPvid
                pvid_oid = ("%s.%s" % (snmp_mib_variables['dot1qPvid'], str(iface.port_id)),
                            Gauge32(new_vlan_id))

                # now send them all as an atomic set():
                # get the PySNMP helper to do the work with the OctetString() BitMaps:
                pysnmp = pysnmpHelper(self.switch)
                (error_status, details) = pysnmp.set_multiple([low_oid, high_oid, pvid_oid])
                if error_status:
                    self.error.status = True
                    self.error.description = "Error in setting vlan on tagged port!"
                    self.error.details = details
                    return -1

            else:
                # regular access mode untagged port:
                # create a PortList to represent the bits that are in the new vlan.
                # we need byte size from number of ports:
                max_port_id = self._get_max_qb_port_id()
                #bytecount = (max_port_id / 8) + 1
                bytecount = int(len(self.qb_port_to_ifindex) / 8) + 1
                portlist = PortList()
                # initialize with "00" bytes
                portlist.from_byte_count(bytecount)
                # now set bit to 1 for the port_id (interfaces):
                portlist[int(iface.port_id)] = 1
                # now loop to find other existing ports on this vlan:
                for (index, intface) in self.interfaces.items():
                    if intface.port_id > -1:
                        # untagged or tagged port on this new vlanId?
                        if (intface.untagged_vlan == new_vlan_id) or (new_vlan_id in intface.vlans):
                            portlist[intface.port_id] = 1
                    else:
                        # no switchport? "should" not happen for a valid switch port interface
                        warning = "Warning: %s - no port_id found in set_interface_untagged_vlan(Comware)!" % intface.name
                        self._add_warning(warning)
                # send to the switch!
                # Comware needs bits in opposite order inside each byte! (go figure)
                portlist.reverse_bits_in_bytes()
                # get the PySNMP helper to do the work with this BitMap:
                # note that to_hex_string() is same as .__str__ representation,
                # but we use it for extra clarity!
                octet_string = OctetString(hexValue=portlist.to_hex_string())
                pysnmp = pysnmpHelper(self.switch)
                (error_status, details) = pysnmp.set("%s.%s" % (snmp_mib_variables['hh3cdot1qVlanPorts'], new_vlan_id), octet_string)
                if error_status:
                    self.error.status = True
                    self.error.description = "Error in setting vlan on access port!"
                    self.error.details = details
                    return -1

            # now trick the next switch view into showing this as the vlan on the interface
            # without the need to re-read SNMP data! We could also just read it here :-)
            # self._parse_oid_and_cache(QBRIDGE_VLAN_IFACE_UNTAGGED_PVID + "." + str(if_index), str(new_vlan_id), 'u')

            # now we need to reread the interface to VLAN mib part
            self._get_port_vlan_data()
            # and force data to be added to session cache again!
            self._set_http_session_cache()
            return 0
        # interface not found, return False!
        return -1

    def _parse_mibs_comware_config(self, oid, val):
        """
        Parse Comware specific ConfigMan MIB
        Mostly entries under 'hh3cCfgLog'
        """
        sub_oid = oid_in_branch(hh3cCfgRunModifiedLast, oid)
        if sub_oid:
            ago = str(datetime.timedelta(seconds=(int(val) / 100)))
            self.add_vendor_data("Configuration", "Running Last Modified", ago)
            return True

        sub_oid = oid_in_branch(hh3cCfgRunSavedLast, oid)
        if sub_oid:
            ago = str(datetime.timedelta(seconds=(int(val) / 100)))
            self.add_vendor_data("Configuration", "Running Last Saved", ago)
            return True

        sub_oid = oid_in_branch(hh3cCfgStartModifiedLast, oid)
        if sub_oid:
            ago = str(datetime.timedelta(seconds=(int(val) / 100)))
            self.add_vendor_data("Configuration", "Startup Last Saved", ago)
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
        """
        dprint("_parse_mibs_comware_poe() %s, len = %d, type = %s" % (str(oid), len(val), str(type(val))))
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
        """
        vlan_id = int(oid_in_branch(hh3cdot1qVlanName, oid))
        if vlan_id > 0:
            if vlan_id in self.vlans.keys():
                # some Comware switches only report "VLAN xxxx", skip that!
                if not val.startswith('VLAN '):
                    self.vlans[vlan_id].name = val
            return True
        return False

    def _parse_mibs_comware_if_type(self, oid, val):
        """
        Parse Comware specific Interface Type MIB
        """
        if_index = int(oid_in_branch(hh3cifVLANType, oid))
        if if_index:
            dprint("Comware if_index %s VLAN TYPE %s" % (if_index, val))
            if if_index in self.interfaces.keys():
                if int(val) == HH3C_IF_MODE_TRUNK:
                    self.interfaces[if_index].is_tagged = True
            return True
        return False

    def _get_poe_data(self):
        """
        Get PoE data, first via the standard PoE MIB,
        then by calling the Comware extended HH3C-POWER-ETH MIB
        """
        SnmpConnector._get_poe_data(self)
        # now get HP specific info from HP-IFC-POE-MIB first
        retval = self._get_branch_by_name('hh3cPsePortCurrentPower', True, self._parse_mibs_comware_poe)
        if retval < 0:
            self._add_warning("Error getting 'PoE-Port-Current-Power' (hh3cPsePortCurrentPower)")
        return 1

    def _map_poe_port_entries_to_interface(self):
        """
        This function maps the "pethPsePortEntry" indices that are stored in self.poe_port_entries{}
        to interface ifIndex values, so we can store them with the interface and display as needed.
        For Comware IRF stack, the mapping appears to be <pse#>.<port#>, where
        PSE# = 1 + (3 x stack member number)
        """
        dprint("_map_poe_port_entries_to_interface(Comware)\n")
        for (pe_index, port_entry) in self.poe_port_entries.items():
            # we take the ending part of "7.12", where 7=PSE#, and 12=port!
            (pse_module, port) = port_entry.index.split('.')
            # calculate the stack member number from PSE#
            member = ((int(pse_module) - 1) / 3)
            # generate the interface ending, for above 7.12 ==> 2/0/12
            # interface appears to be port - ((member-1)*65)
            portnum = int(port) - ((member - 1) * 65)
            end = "%d/0/%d" % (member, portnum)
            count = len(end)
            for (if_index, iface) in self.interfaces.items():
                if iface.name[-count:] == end:
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

    def can_change_interface_vlan(self):
        """
        Return True if we can change a vlan on an interface, False if not
        """
        # at this time, we use SSH/Netmiko for this, so we need a Netmiko profile!
        if self.switch.netmiko_profile:
            return True
        return False

    def can_save_config(self):
        """
        If True, this instance can save the running config to startup
        Ie. "write mem / save" is implemented via an SNMP interfaces
        """
        return True

    def save_running_config(self):
        """
        HP/3COM interface to save the current config to startup via SNMP
        For details on how this works, see
        http://www.h3c.com.hk/products___solutions/technology/system_management/configuration_example/200912/656452_57_0.htm
        or Google the H3C file
        "Configuration_Examples_for_Configuration_File_Management_Using_SNMP.pdf"
        see page 11!
        Returns 0 is this succeeds, -1 on failure. self.error() will be set in that case
        """
        dprint("save_running_config(Comware)")

        # According to the
        # run the Operations row status to find free slot to write to:
        retval = self._get_branch_by_name('hh3cCfgOperateRowStatus', True, self._parse_mibs_comware_configfile)
        if retval < 0:
            self._add_warning("Error reading 'Config File MIB' (hh3cCfgOperateRowStatus)")
            return 1

        # now figure out where we need to write to
        row_place = self.active_config_rows + 1
        # set_multiple() needs a list of tuples(oid, value, type)
        retval = self._set_multiple([
            ("%s.%s" % (hh3cCfgOperateType, row_place), HH3C_running2Startup, 'i'),
            ("%s.%s" % (hh3cCfgOperateRowStatus, row_place), HH3C_createAndGo, 'i')
        ])
        if retval < 0:
            self._add_warning("Error saving via SNMP (hh3cCfgOperateRowStatus)")
            return -1
        return 0

    def _parse_mibs_comware_configfile(self, oid, val):
        """
        Parse Comware specific ConfigMan MIB
        """
        dprint("_parse_mibs_comware_configfile(Comware)")
        sub_oid = oid_in_branch(hh3cCfgOperateRowStatus, oid)
        if sub_oid:
            if int(sub_oid) > self.active_config_rows:
                self.active_config_rows = int(sub_oid)
            return True
