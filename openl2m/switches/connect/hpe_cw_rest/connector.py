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
HPE Comware REST API Connector

This implements a REST api driver from Comware devices. This follows the API docs outlined
in the HPE Comware NetConf documentation.

TO DO:
- description set to empty string ''

"""
import base64
from datetime import timedelta
import json
import pprint
import socket
from typing import Dict, List

from django.http.request import HttpRequest
from rangeparser import RangeParser
# used to disable unknown SSL cert warnings:
import urllib3

from switches.connect.classes import Interface, Vlan, Transceiver, PoePort, NeighborDevice, StackMember
from switches.connect.restconnector import RESTConnector
from switches.connect.constants import (
    # VLAN_ADMIN_DISABLED,
    # POE_PORT_ADMIN_DISABLED,
    POE_PORT_ADMIN_ENABLED,
    IF_DUPLEX_UNKNOWN,
    IF_DUPLEX_HALF,
    IF_DUPLEX_FULL,
    # IF_TYPE_OTHER,
    # IF_TYPE_LOOPBACK,
    # IF_TYPE_VIRTUAL,
    # IF_TYPE_ETHERNET,
    IF_TYPE_LAGG,
    LACP_IF_TYPE_MEMBER,
    LACP_IF_TYPE_AGGREGATOR,
    POE_PSE_STATUS_ON,
    POE_PSE_STATUS_OFF,
    POE_PSE_STATUS_FAULT,
    # LLDP_CHASSIC_TYPE_ETH_ADDR,
    LLDP_CAPABILITIES_OTHER,
    LLDP_CAPABILITIES_REPEATER,
    LLDP_CAPABILITIES_BRIDGE,
    LLDP_CAPABILITIES_WLAN,
    LLDP_CAPABILITIES_ROUTER,
    LLDP_CAPABILITIES_PHONE,
    LLDP_CAPABILITIES_DOCSIS,
    LLDP_CAPABILITIES_STATION,
    # IANA_TYPE_OTHER,
    # IANA_TYPE_IPV4,
    # IANA_TYPE_IPV6,
)
from switches.models import Switch, SwitchGroup
# from switches.utils import time_duration, dprint
from switches.utils import dprint

API_VERSION = 1


class HPECwRestConnector(RESTConnector):
    """
    This implements an HPE Comware REST API connector object.
    """

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        # call the super class
        dprint("HPECwRestConnector __init__")
        super().__init__(request, group, switch)
        self.description = "HPE Comware REST API driver"
        self.vendor_name = "HPE/Aruba"
        # we can override the settings calculated from switch.read_only, group.ready_only and user.profile.read_only
        # but we should only do this to create a Read-Only driver!
        # self.read_only = True

        if switch.description:
            self.add_more_info("System", "Description", switch.description)

        self._set_base_url(base_url=f"https://{self.switch.primary_ip4}/api/v{API_VERSION}/")

        # this holds the custom REST api attributes
        self.token: str = ""                    # REST token after username/password login
        self.token_timeout: str = ""            # time token expires
        self.set_do_not_cache_attribute("token")

        self.port_index_to_if_index: Dict[
            int, str
        ] = {}  # this maps switchport "PortIndex" as key (int) to MIB-II IfIndex (str)

        # login and get a REST token
        if not self._open_device():
            raise Exception(self.error.description)

        # capabilities supported by this eAPI driver:
        self.can_change_admin_status = True
        self.can_change_vlan = True
        self.can_change_poe_status = True
        self.can_change_description = True
        self.can_save_config = True     # do we have the ability (or need) to execute a 'save config' or 'write memory' ?
        self.can_reload_all = True  # if true, we can reload all our data (and show a button on screen for this)
        self.can_edit_vlans = True  # if true, this driver can edit (create/delete) vlans on the device!
        self.can_set_vlan_name = True  # set to False if vlan create/delete cannot set/change vlan name!
        self.can_edit_tags = True  # True if this driver can edit 802.1q tagged vlans on interfaces
        self.can_allow_all = True  # if True, driver can perform equivalent of "vlan trunk allow all", additional to "allow x, y, z"

    #########################################
    # Comware REST API supporting functions #
    #########################################

    def _set_auth_headers(self, data_type="json"):
        #
        # set request headers with our API authentication token. We use JSON format as default
        #
        self.headers = {
            "X-Auth-Token": self.token,
            "Content-Type": f"application/{data_type}",
        }

    def _open_device(self) -> bool:
        """
        Once we have a token, REST API is stateless, so no need to open again...
        return True on success, False on failure, and will set self.error
        """
        dprint("API _open_device()")

        if self.token:
            dprint("  token available!")
            return True

        # do we have creds set?
        if not self.switch.netmiko_profile:
            self.error.status = True
            self.error.description = "Please configure a Credentials Profile to be able to connect to this device!"
            dprint("  _open_device: No Credentials!")
            return False

        # do we want to check SSL certificates?
        if not self.switch.netmiko_profile.verify_hostkey:
            dprint("  Cert warnings disabled in urllib3!")
            # disable unknown cert warnings
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            # or all warnings:
            urllib3.disable_warnings()

        return self.login()

    def _close_device(self) -> bool:
        """
        eAPI is stateless, just clear out token.
        """
        dprint("HPECwRestConnector._close_device()")
        self.token = ""
        self.token_timeout = ""
        return True

    def login(self):
        #
        # login is a POST to the server to get a REST token
        #
        dprint("HPECwRestConnector.login()")
        # set the authentication header to the base64 encoded string "username:password"
        auth_plain = f"{self.switch.netmiko_profile.username}:{self.switch.netmiko_profile.password}"
        # should this be UTF-8 encoded ?
        auth_base64 = base64.b64encode(auth_plain.encode("ascii")).decode("ascii")
        headers = {
            "Authorization": f"Basic {auth_base64}",
            # "Content-Type": "application/json",
        }

        # and try the "get-token" url
        try:
            self._post(path="Tokens", headers=headers, message="API LOGIN")
            data = json.loads(self.response.text)
            if "token-id" in data:
                self.token = data['token-id']
                self.token_timeout = data['expiry-time']
                dprint(f"  Found token: {self.token}")
                dprint(f"  Timeout: {self.token_timeout}")
                self._set_auth_headers()
                return True
            # Hmm? No token?
            dprint("ERROR: No login token found!")
            self.error.description = "Error getting login token!"
            self.error.details = "We're not sure what happened!"
            return False
        except Exception as err:
            dprint(f"ERROR: cannot login! - {err}")
            self.error.description = "Error establishing connection!"
            self.error.details = f"Cannot open REST session: {format(err)}"
            return False

    ##############################
    # OpenL2M specific functions #
    ##############################

    #
    # From the HPE Comware NetConf / REST API docs:
    #
    # GET is used to read various configurations and operational data from the device.
    # Data is returned in the body of the response.
    #
    # POST can only be used to create new objects or attributes, ie when they are NOT SET YET!
    # Data is sent in the body of the request.
    #
    # PUT will update with value, but NOT clear out! (ie you cannot set description="").
    # Data is send in the body of the request.
    # Success will return code 204 - No content.
    # You can repeatedly PUT with the same value!
    #
    # DELETE needs to be used to remove an object. It does NOT take request body data.
    #

    def get_my_basic_info(self) -> bool:
        """
        Get basic info via REST
        """
        dprint("HPECwRestConnector.get_my_basic_info()")
        self.hostname = self.switch.hostname

        if not self._open_device():
            return False  # self.error already set!

        facts = self._get(path="Device/Base")
        if facts:
            # dprint(f"FACT: {pprint.pformat(facts)}")
            self.add_more_info("System", "Hostname", facts["HostName"])
            self.add_more_info("System", "Model", facts["HostDescription"])
            self.add_more_info("System", "OID", facts["HostOid"])
            # uptime needs to be parsed. uptime ticks are in seconds
            self.add_more_info("System", "Uptime", str(timedelta(seconds=facts["Uptime"])))
            # add to database driver info:
            self.switch.hostname = facts["HostName"]
            self.set_driver_info(name="hostname", value=facts["HostName"])
            self.set_driver_info(name="snmp_oid", value=facts["HostOid"])

        #
        # some hardware info
        #
        hardware = self._get(path="Device/PhysicalEntities")
        if hardware:
            found_chassis = False
            # dprint(f"HARDWARE: {pprint.pformat(hardware)}")
            for hw in hardware["PhysicalEntities"]:
                match hw["Class"]:
                    # these class numbers match the ENTITY MIB values!
                    case 3:     # 3 = Frame, i.e. the whole chassis
                        # IRF stacks show up as multiple chassis, add to system and hardware section:
                        if not found_chassis:
                            self.add_more_info("System", "Model Short", hw["Model"])
                            self.add_more_info("System", "Model Name", hw["Name"])
                            self.add_more_info("System", "Serial", hw["SerialNumber"])
                            self.add_more_info("System", "OS Version", hw["SoftwareRev"])
                            # add to driver info:
                            self.set_driver_info(name="model", value=hw["Model"])
                            self.set_driver_info(name="os_version", value=hw["SoftwareRev"])
                            self.set_driver_info(name="serial_number", value=hw["SerialNumber"])
                            found_chassis = True
                            # and add as stack member
                            s = StackMember(id=hw["PhysicalIndex"], type=3)
                            s.serial = hw["SerialNumber"]
                            s.model = hw["Name"]
                            s.version = hw["SoftwareRev"]
                            s.info = f"OID: {hw['VendorType']}"
                            s.description = hw["Description"]
                            self.stack_members[hw["PhysicalIndex"]] = s
                        else:
                            # IRF stacks show up as multiple chassis, add as stack member
                            s = StackMember(id=hw["PhysicalIndex"], type=3)
                            s.serial = hw["SerialNumber"]
                            s.model = hw["Name"]
                            s.version = hw["SoftwareRev"]
                            s.info = f"OID: {hw['VendorType']}"
                            s.description = hw["Description"]
                            self.stack_members[hw["PhysicalIndex"]] = s
                    case 11:    # IRF fabric indicator
                        s = StackMember(id=hw["PhysicalIndex"], type=11)
                        s.description = "HPE IRF"
                        self.stack_members[hw["PhysicalIndex"]] = s

        #
        # get vlan info
        #
        # Note: this api call also returns information about the interfaces active on each vlan!
        # we will use this later to find 802.1q tagged info
        #
        vlans = self._get(path="VLAN/VLANs")
        if vlans:
            # vlans is a list of dict() for each vlan
            for vlan in vlans["VLANs"]:
                # dprint(f"\nVLAN: {pprint.pformat(vlan)}")
                # create OpenL2M Vlan() object!
                v = Vlan(id=int(vlan['ID']))
                v.name = vlan["Name"]
                v.description = vlan["Description"]
                self.add_vlan(v)

        #
        # get interface information
        #
        # Note: varies values for up/down, type, etc. are defined in the Comware NetConf documentation
        #
        interfaces = self._get(path="Ifmgr/Interfaces")
        if interfaces:
            for i in interfaces["Interfaces"]:
                # dprint(f"\nINTERFACE: {pprint.pformat(i)}")

                # as all other references in the API use the IfIndex,
                # we use 'IfIndex' as the key to this interface, ie. NOT the name!
                iface = Interface(i['IfIndex'])
                iface.name = i['Name']

                if int(i['AdminStatus']) == 1:  # 1=up, 2=down
                    iface.admin_status = True
                else:
                    iface.admin_status = False

                if int(i['OperStatus']) == 1:
                    iface.oper_status = True
                else:
                    iface.oper_status = False

                if "ActualSpeed" in i:
                    try:
                        iface.speed = int(int(i["ActualSpeed"]) / 1000)   # in Bps !
                    except Exception:
                        dprint(f"Note: Invalid speed: {i['ActualSpeed']}")

                if "ConfigDuplex" in i:
                    match int(i["ConfigDuplex"]):
                        case 1:     # Full
                            iface.duplex = IF_DUPLEX_FULL
                        case 2:     # Half
                            iface.duplex = IF_DUPLEX_HALF
                        case _:     # should not happen!
                            iface.duplex = IF_DUPLEX_UNKNOWN

                if "Description" in i:
                    iface.description = i["Description"]

                if "PortLayer" in i and int(i["PortLayer"]) == 2:     # 2 = layer 3 - routed
                    # Note: we also will read "IPV4ADDRESS/Ipv4Addresses" and "IPV6ADDRESS/Ipv6Addresses"
                    # to get interface addresses. This reads both IPv4 and IPv6
                    dprint("  Routed Mode!")
                    iface.is_routed = True
                    if "InetAddressIPV4" in i:
                        # set ipv4 info
                        iface.add_ip4_network(address=i["InetAddressIPV4"], netmask=i["InetAddressIPV4Mask"])

                    # IPv6 not available on some devices (Comware 7 - No?, Comware 9 - Yes ?) See also above.
                    if "InetAddressIPV6" in i:
                        # set ipv6 info
                        iface.add_ip6_network(address=i["InetAddressIPV6"], prefix_len=i["InetAddressIPV6PrefixLength"])

                if "ifType" in i:
                    iface.type = int(i["ifType"])

                if "PortIndex" in i:
                    # this is the "switchport" port-id, meaning this is a real physical port!
                    # this is what is to map Ethernet addresses to an interface,
                    # as that is tracked by the physical switchport, and NOT the "logical" interface
                    # this is identical to the SNMP Q-Bridge port-id !
                    iface.port_id = int(i["PortIndex"])
                    # also add this info to easily map PortIndex to IfIndex:
                    self.port_index_to_if_index[i["PortIndex"]] = i["IfIndex"]

                if "LinkType" in i:
                    match int(i["LinkType"]):
                        case 1:     # access
                            dprint("  Access Mode!")
                            iface.is_tagged = False
                            iface.untagged_vlan = int(i['PVID'])

                        case 2:
                            dprint("  Trunk Mode!")
                            iface.is_tagged = True
                            iface.untagged_vlan = int(i['PVID'])
                            # # tagged vlans to be parsed from 'permitted_vlans' and 'taggedvlan':
                            # if i['taggedvlan'] is not None:
                            #     parser = RangeParser()
                            #     tagged_vlans = parser.parse(i["taggedvlan"])
                            #     for vlan_id in tagged_vlans:
                            #         iface.add_tagged_vlan(vlan_id=vlan_id)

                        case 3:
                            dprint("  Hybrid Mode!")
                            iface.manageable = False
                            iface.unmanage_reason = "Access denied: interface in Hybrid mode!"

                        case _:
                            dprint(f"UNKNOWN Link-Type: {i['Linktype']}")
                            iface.manageable = False
                            iface.unmanage_reason = f"Access denied: unknown interface mode! (LinkType {i['Linktype']})"

                        # case _:
                        #

                if "ConfigMTU" in i:
                    iface.mtu = int(i["ConfigMTU"])

                # done, add this interface to the list...
                self.add_interface(iface)

            #
            # get PoE data
            #

            # PowerSupplies
            PSEs = self._get(path="PoE/PSEs")
            if PSEs:
                for pse in PSEs["PSEs"]:
                    # dprint(f"\nPOE PSE: {pprint.pformat(pse)}")
                    # create a PoePSE() for OpenL2M use:
                    # "PowerLimit" is in mW, ie divide by 1000 for W
                    if "PowerLimit" in pse:
                        ps = self.add_poe_powersupply(id=pse["PSEID"], power_available=int(pse["PowerLimit"]) / 1000)
                        ps.power_consumed = int(pse["CurrentPower"]) / 1000
                        match int(pse["OperStatus"]):
                            case 1:
                                ps.status = POE_PSE_STATUS_ON
                            case 2:
                                ps.status = POE_PSE_STATUS_OFF
                            case 3:
                                ps.status = POE_PSE_STATUS_FAULT
                        ps.power_consumed = int(pse["AveragePower"]) / 1000
                        # some drivers have this easily available:
                        ps.model = pse["Model"]
                        # ps.name = ""
                        # ps.description = ""
                        # ps.part_number = ""
                        # ps.serial = ""
                    else:   # older API entry ?
                        dprint("Unknow API data returned?")
                        dprint(f"PSE Info: {pprint.pformat(pse)}")


            # PoE Ports
            # Note: this API point on gives ports that are using PoE,
            # NOT ports that are capable of PoE!
            PoEPorts = self._get(path="PoE/Ports")
            if PoEPorts:
                for port in PoEPorts["Ports"]:
                    dprint(f"\nPOE-PORT: {pprint.pformat(port)}")
                    # get the interface from IfIndex:
                    iface = self.get_interface_by_key(key=port['IfIndex'])
                    if iface:
                        if "AdminEnable" in port:
                            admin_status = port["AdminEnable"]
                        else:
                            admin_status = POE_PORT_ADMIN_ENABLED
                        poe = PoePort(index=port["IfIndex"], admin_status=admin_status)
                        # set various values found:
                        poe.pse_id = int(port["PSEID"])                     # need for port PoE enable/disable
                        if "CurrentPower" in port:
                            # old style does NOT have CurrentPower if no PoE served...
                            poe.power_consumption_supported = True
                            poe.power_consumed = int(port["CurrentPower"])      # power consumed in milliWatt
                            poe.power_available = int(port["PowerLimit"])       # power available in milliWatt
                            poe.max_power_consumed = int(port["PeakPower"])     # max power drawn since PoE reset, in milliWatt
                            # "DetectionStatus" matches the SNMP POE mib definitions
                            poe.detect_status = int(port["DetectionStatus"])
                        # and assign to interface:
                        iface.poe_entry = poe

            #
            # get LACP/Port-Channel ports
            #

            # first get the LACP Groups, to find Bridge or Route aggregates
            laggs = self._get(path="LAGG/LAGGGroups")
            if laggs:
                # build dict with type and aggregate interface info
                lag_master_info = {}
                for lag in laggs["LAGGGroups"]:
                    # dprint(f"\nLACP-INTERFACE: {pprint.pformat(lag)}")
                    lag_iface = self.get_interface_by_key(key=lag["IfIndex"])
                    if lag_iface:
                        lag_iface.type = IF_TYPE_LAGG
                        lag_iface.lacp_type = LACP_IF_TYPE_AGGREGATOR
                        # store aggregation interface:
                        lag_master_info[lag["GroupId"]] = lag_iface

                # now find the members, and map to an aggregate interface
                lacp_members = self._get(path="LAGG/LAGGMembers")
                if lacp_members:
                    for member in lacp_members["LAGGMembers"]:
                        # dprint(f"\nLAGG-MEMBER: {pprint.pformat(member)}")
                        # a possible LAGG interface ?
                        if member["GroupId"] in lag_master_info:
                            # get this interface
                            member_iface = self.get_interface_by_key(key=member["IfIndex"])
                            if member_iface:
                                dprint(f"    found Interface() for '{member_iface.name}'")
                                member_iface.lacp_type = LACP_IF_TYPE_MEMBER
                                member_iface.lacp_master_name = lag_master_info[member["GroupId"]].name
                                member_iface.lacp_master_index = int(member["GroupId"])   # needs to be an integer!
                                # add to list of port-channel
                                lag_master_info[member["GroupId"]].lacp_members[member["IfIndex"]] = member_iface.name
                            else:   # should not happen.
                                err_str = f"ERROR: cannot find LACP member interface for index {member['IfIndex']} for LAGG {member['GroupId']}"
                                dprint(err_str)
                                self.add_warning(err_str)

            #
            # get interface IPv4 and IPv6 addresses
            #
            dprint("--- Reading interface IPv4 from 'IPV4ADDRESS/Ipv4Addresses' api ---")
            addresses = self._get(path="IPV4ADDRESS/Ipv4Addresses")
            if addresses:
                for a in addresses["Ipv4Addresses"]:
                    # dprint(f"\nADDRESS: {pprint.pformat(a)}")
                    iface = self.get_interface_by_key(key=a["IfIndex"])
                    if iface:
                        iface.add_ip4_network(address=a["Ipv4Address"], netmask=a["Ipv4Mask"])

            dprint("--- Reading interface IPv6 from 'IPV6ADDRESS/Ipv6Addresses' api ---")
            addresses = self._get(path="IPV6ADDRESS/Ipv6Addresses")
            if addresses:
                for a in addresses["Ipv6Addresses"]:
                    # dprint(f"\nADDRESS: {pprint.pformat(a)}")
                    iface = self.get_interface_by_key(key=a["IfIndex"])
                    if iface:
                        iface.add_ip6_network(address=a["Ipv6Address"], prefix_len=a["Ipv6PrefixLength"])

            #
            # Deprecated - see below
            #
            # now read the tagged vlans on ports from the vlan call to "VLAN/VLANs" above:
            # note: we have already found the untagged vlan in the interface call above,
            # thus we don't read "AccessPortList" and "UntaggedPortList",
            # but we are only looking at "TaggedPortList".
            # And, this uses the switch port, NOT the InterfaceIndex!
            # dprint("--- Reading tagged vlans from 'VLAN/VLANs' api ---")
            # if vlans:
            #     # vlans is a list of dict() for each vlan
            #     for vlan in vlans["VLANs"]:
            #         dprint(f"\nVLAN: {pprint.pformat(vlan)}")
            #         if "TaggedPortList" in vlan:
            #             # expand the range to individual port numbers:
            #             parser = RangeParser()
            #             tagged_ports = parser.parse(vlan["TaggedPortList"])
            #             for port in tagged_ports:
            #                 iface = self._get_interface_by_port_id(port_id=port)
            #                 if iface:
            #                     iface.add_tagged_vlan(vlan_id=int(vlan["ID"]))

            # we are reading 802.1Q Trunk/Tagged vlans from "VLAN/TrunkInterfaces",
            # as this has more detailed info, specifically shows if the PVID is permitted as tagged.abs
            dprint("--- Reading tagged vlans from 'VLAN/TrunkInterfaces' api ---")
            interfaces = self._get(path="VLAN/TrunkInterfaces")
            if interfaces:
                for i in interfaces["TrunkInterfaces"]:
                    # dprint(f"\nINTERFACE: {pprint.pformat(i)}")
                    if "PermitVlanList" in i:   # better be there :-)
                        # expand the range to individual port numbers:
                        parser = RangeParser()
                        tagged_vlans = parser.parse(i["PermitVlanList"])
                        iface = self.get_interface_by_key(key=i["IfIndex"])
                        if iface:
                            for vlan_id in tagged_vlans:
                                iface.add_tagged_vlan(vlan_id=vlan_id)

            #
            # get IRF ports
            #
            irf_ports = self._get("IRF/IRFPorts")
            if irf_ports:
                for irf in irf_ports["IRFPorts"]:
                    # dprint(f"\nIRF-PORT: {pprint.pformat(irf)}")
                    # are IRF interfaces defined ?
                    if "Interface" in irf:
                        if_info = irf["Interface"][0]
                        # dprint("IF_INFO=")
                        dprint(if_info)
                        # get the interface
                        irf_iface = self.get_interface_by_name(name=if_info["IfName"])
                        if irf_iface:
                            # note that we don't care about IRF port type!
                            irf_iface.manageable = False
                            irf_iface.unmanage_reason = "Access denied: interface in IRF (stacking) mode!"

            #
            # get optical transceiver data
            #
            dprint("\n\n--- OPTICS ---\n")
            transceivers = self._get(path="Device/Transceivers")
            if transceivers:
                for optics in transceivers["Transceivers"]:
                    # dprint(f"\nOPTICS: {pprint.pformat(optics)}")
                    iface = self.get_interface_by_key(key=optics['IfIndex'])
                    if iface:
                        # dprint("   found Interface()")
                        trx = Transceiver()
                        trx.type = optics["TransceiverType"]
                        trx.vendor = optics["VendorName"]
                        trx.serial = optics["SerialNumber"]
                        dprint(f"\nOptics info:\n{i}\n")
                        match int(optics['FiberDiameterType']):
                            case 1:     # 9 micron, ie SM
                                trx.wavelength = int(optics["WaveLength"])   # likely 1310
                            case 2:     # 50 micron, ie MM
                                trx.wavelength = int(optics["WaveLength"])   # likely 850
                            case 3:     # 62.5 micron, ie MM
                                trx.wavelength = int(optics["WaveLength"])   # likely 850
                            case 4:     # copper
                                trx.wavelength = 0
                        # note used:
                        # trx.description: str = ""
                        # trx.connector: str = ""  # 'LC', SC', etc.
                        iface.transceiver = trx

        # save driver info
        self.save_driver_info()

        return True

    def get_my_vrfs(self):
        #
        # read VRF info
        #
        vrfs = self._get(path="L3vpn/L3vpnVRF")
        if vrfs:
            # dprint(f"\n\nVRFs:\n{pprint.pformat(vrfs)}\n")
            for vrf in vrfs["L3vpnVRF"]:
                # dprint(f"\nVRF:\n{pprint.pformat(vrf)}")
                # Note: this does NOT return the default routing table as a vrf!
                v = self.get_vrf_by_name(name=vrf["VRF"])
                if "Description" in vrf:
                    v.set_description(description=vrf["Description"])
                # 'semi' vrf's such as Mgmt do not have an RD:
                if "RD" in vrf:
                    v.set_rd(rd=vrf["RD"])
                if "Ipv4RoutingLimit" in vrf:
                    v.set_ipv4()
                if "Ipv6RoutingLimit" in vrf:
                    v.set_ipv6()
                v.set_active_interfaces(count=int(vrf["AssociatedInterfaceCount"]))
                # to find member interfaces, we need to store the VrfIndex field:
                v.set_index(index=int(vrf["VrfIndex"]))

            # get the interfaces in the VRFs
            vrf_members = self._get(path="L3vpn/L3vpnIf")
            if vrf_members:
                for member in vrf_members["L3vpnIf"]:
                    # dprint(f"\nVRF Member:\n{pprint.pformat(member)}\n")
                    # find the interface and assign to VRF:
                    iface = self.get_interface_by_key(member["IfIndex"])
                    if iface:
                        iface.vrf_name = member["VRF"]
                        vrf = self.get_vrf_by_name(name=member["VRF"])
                        if vrf:
                            vrf.add_interface(if_name=iface.name)

    def get_my_client_data(self) -> bool:
        """
        read mac addressess, and lldp neigbor info.
        return True on success, False on error and set self.error variables
        """
        dprint("HPECwRestConnector.get_my_client_data()")

        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        #
        # get Layer 2 MAC/ETHERNET info
        #
        dprint("\n\n--- MAC tables ---")
        macs = self._get(path="MAC/MacUnicastTable")
        if macs:
            # dprint(pprint.pformat(macs))
            for mac in macs["MacUnicastTable"]:
                # dprint(f"\nEthernet: {pprint.pformat(mac)}")
                # add this to the known addressess:
                # this uses PortIndex, which needs to be mapped to IfIndex
                if mac["PortIndex"] in self.port_index_to_if_index:
                    # FIX THIS =====>>>
                    # if_index = self.port_index_to_if_index[mac["PortIndex"]]
                    iface = self._get_interface_by_port_id(port_id=mac["PortIndex"])
                    if iface:
                        iface.add_learned_ethernet_address(eth_address=mac["MacAddress"], vlan_id=mac["VLANID"])
                        self.eth_addr_count += 1
                else:
                    # this appears to happen on Aggregate interfaces:
                    # dprint(f"WARNING: ethernet PortIndex {mac['PortIndex']} unknown, trying PortName...")
                    if "PortName" in mac:
                        iface = self.get_interface_by_name(name=mac["PortName"])
                        if iface:
                            dprint("  Ethernet adding from PortName !")
                            iface.add_learned_ethernet_address(eth_address=mac["MacAddress"], vlan_id=mac["VLANID"])
                            self.eth_addr_count += 1

        #
        # get IPV4 ARP data
        #
        dprint("\n\n--- IPv4 ARP tables ---")
        arps = self._get(path="ARP/ArpTable")
        if arps:
            # dprint(pprint.pformat(arps))
            for arp in arps["ArpTable"]:
                # dprint(f"\nARP: {pprint.pformat(arp)}")
                # some devices return an "IfName", but not all!
                # some devices ARP return a "VrfIndex", we can then map a VLAN to a VRF.
                vrf_name = ""
                if "VrfIndex" in arp:
                    dprint("  Looking for VRF!")
                    vrf = self.get_vrf_by_index(index=int(arp["VrfIndex"]))
                    if vrf:
                        dprint("  Found VRF: {vrf.name}")
                        vrf_name = vrf.name

                # some entries have vlan id:
                vlan_id = -1
                if "VLANID" in arp:
                    vlan_id = int(arp["VLANID"])

                # IfIndex is the field that maps to the interface
                if_index = arp["IfIndex"]
                # except if "PortIndex" exists, then this field points to the physical port
                # where this eth was heard
                if "PortIndex" in arp:
                    if arp["PortIndex"] in self.port_index_to_if_index:
                        if_index = self.port_index_to_if_index[arp["PortIndex"]]

                # find the Interface() from the "IfIndex" field, ie. the Interface().key
                iface = self.get_interface_by_key(key=if_index)
                if iface:
                    dprint(f"  Found interface {iface.name}")
                    eth = iface.add_learned_ethernet_address(
                        eth_address=arp["MacAddress"],
                        ip4_address=arp["Ipv4Address"],
                        vlan_id=vlan_id,
                        vrf_name=vrf_name,
                    )
                    if vrf:
                        dprint("  Trying to adding VRF to VLAN {eth.vlan_id}")
                        vlan = self.get_vlan_by_id(eth.vlan_id)
                        if vlan:
                            dprint("  Found Vlan()!")
                            vlan.vrf_name = vrf.name
                else:
                    dprint(f"ARP ERROR: Cannot find interface for index {arp['IfIndex']}")

        #
        # get IPV6 ND (aka Neighbors)
        #
        dprint("\n\n--- IPv6 ND tables ---")
        ipv6nd = self._get(path="ND/NDTable")
        if ipv6nd:
            for nd in ipv6nd["NDTable"]:
                # dprint(f"\nND = {pprint.pformat(nd)}")
                # some devices return an "IfName", but not all!
                # Note: this also has "VrfIndex", not used at present.
                if "IfName" in nd:
                    self.add_learned_ethernet_address(
                        if_name=nd["IfName"],
                        eth_address=nd["MacAddress"],
                        # vlan_id=vlan_id,
                        ip6_address=nd["Ipv6Address"],
                    )
                else:
                    # find the Interface() from the "IfIndex" field, ie. the Interface().key
                    iface = self.get_interface_by_key(key=nd["IfIndex"])
                    if iface:
                        iface.add_learned_ethernet_address(eth_address=nd["MacAddress"], ip6_address=nd["Ipv6Address"])

        #
        # LLDP neighbors
        #

        # these 2 entries below don't have a lot of info
        # they return the basic "NeighborIndex", which is unique per interface
        # this string is used as a index into the Interface.lldp dictionary for each interface.
        dprint("\n\n--- LLDP - CDP Neighbors ---")
        neighbors = self._get(path="LLDP/CDPNeighbors")
        if neighbors:
            for nb in neighbors["CDPNeighbors"]:
                # dprint(f"\nCDP: {pprint.pformat(nb)}")
                self.parse_neighbor(nb=nb)

        dprint("\n\n--- LLDP - LLDP Neighbors ---")
        neighbors = self._get(path="LLDP/LLDPNeighbors")
        if neighbors:
            for nb in neighbors["LLDPNeighbors"]:
                # dprint(f"\nLLDP: {pprint.pformat(nb)}")
                self.parse_neighbor(nb=nb)

        # this call adds some more details about the ports and description of the remote system
        # it also includes the same "NeighborIndex" as above
        dprint("\n\n--- LLDP - LLDP Neighbor Basics ---")
        neighbors = self._get(path="LLDP/NbBasicInfos")
        if neighbors:
            for nb in neighbors["NbBasicInfos"]:
                # dprint(f"\nLLDP: {pprint.pformat(nb)}")
                self.parse_neighbor_basics(nb=nb)

        # Capabilities and Management Address endpoints also have mapping back to the entries above!
        dprint("\n\n--- LLDP - LLDP Neighbor SysCaps ---")
        neighbors = self._get(path="LLDP/NbSysCaps")
        if neighbors:
            for nb in neighbors["NbSysCaps"]:
                # dprint(f"\nLLDP: {pprint.pformat(nb)}")
                self.parse_neighbor_syscaps(nb=nb)

        dprint("\n\n--- LLDP - LLDP Neighbors Addresses ---")
        neighbors = self._get(path="LLDP/NbManageAddresses")
        if neighbors:
            for nb in neighbors["NbManageAddresses"]:
                # dprint(f"\nLLDP: {pprint.pformat(nb)}")
                self.parse_neighbor_management(nb=nb)

        return True

    def parse_neighbor(self, nb):
        #
        # parse LLDP or CDP data, this is the initial data from /LLDPNeighbors or /CDPNeighbors
        #

        # get an OpenL2M NeighborDevice()
        # Note: "NeighborIndex" is unique PER INTERFACE, and can be used as the index
        # it is also the key to match with more data from "LLDP/NbBasicInfos", "LLDP/NbSysCaps" and "LLDP/NbManageAddresses"
        neighbor = NeighborDevice(lldp_index=nb["NeighborIndex"])
        neighbor.set_chassis_string(nb["ChassisId"])
        neighbor.set_sys_name(nb["SystemName"])
        neighbor.port_name = nb["PortId"]
        # add neighbor to interface:
        iface = self.get_interface_by_key(key=nb["IfIndex"])
        if iface:
            iface.add_neighbor(neighbor=neighbor)
            self.neighbor_count += 1

    def parse_neighbor_basics(self, nb):
        #
        # parse LLDP Basic Info data
        # add to data from initial /LLDPNeighbors
        #

        # find existing OpenL2M NeighborDevice()
        iface = self.get_interface_by_key(key=nb["IfIndex"])
        if iface:
            # now find existing NeighborDevice()
            neighbor = iface.get_neighbor(index=nb["NeighborIndex"])
            if neighbor:
                # nb["ChassisId"] and SystemName were already set in /LLDPNeighbors call.
                # neighbor.set_sys_name(nb["SystemName"])
                neighbor.set_sys_description(nb["SystemDesc"])
                # PortDesc is the LOCAL port description, NOT remote device!
                # neighbor.port_name = nb["PortDesc"]
            else:
                dprint(f"WARNING: neighbor for index {nb['NeighborIndex']} NOT FOUND!")

    def parse_neighbor_syscaps(self, nb):
        #
        # parse LLDP NbSysCaps data
        # add to data from inital LLDP/LLDPNeighbors
        #

        # find existing OpenL2M NeighborDevice()
        iface = self.get_interface_by_key(key=nb["IfIndex"])
        if iface:
            # now find existing NeighborDevice()
            neighbor = iface.get_neighbor(index=nb["NeighborIndex"])
            if neighbor:
                # nb["ChassisId"] and SystemName were already set in /LLDPNeighbors call.
                # neighbor.set_sys_name(nb["SystemName"])
                for capability, enabled in nb["Enable"].items():
                    if enabled:
                        match capability:
                            case 'Bridge':
                                neighbor.set_capability(LLDP_CAPABILITIES_BRIDGE)
                            case 'CustomerBridge':
                                neighbor.set_capability(LLDP_CAPABILITIES_BRIDGE)
                            case 'DocsisCableDevice':
                                neighbor.set_capability(LLDP_CAPABILITIES_DOCSIS)
                            case 'Other':
                                neighbor.set_capability(LLDP_CAPABILITIES_OTHER)
                            case 'Repeater':
                                neighbor.set_capability(LLDP_CAPABILITIES_REPEATER)
                            case 'Router':
                                neighbor.set_capability(LLDP_CAPABILITIES_ROUTER)
                            case 'ServiceBridge':
                                neighbor.set_capability(LLDP_CAPABILITIES_BRIDGE)
                            case 'StationOnly':
                                neighbor.set_capability(LLDP_CAPABILITIES_STATION)
                            # case 'TPMR':
                            #     neighbor.set_capability(LLDP_CAPABILITIES_???
                            case 'Telephone':
                                neighbor.set_capability(LLDP_CAPABILITIES_PHONE)
                            case 'WLANAccessPoint':
                                neighbor.set_capability(LLDP_CAPABILITIES_WLAN)
            else:
                dprint(f"WARNING: neighbor for index {nb['NeighborIndex']} NOT FOUND!")

    def parse_neighbor_management(self, nb):
        #
        # parse LLDP NbManageAddresses data
        # add to data from initial LLDP/LLDPNeighbors
        #

        #
        # NOTE: lldp remote device address parsing is NOT functional yet...
        #

        # find existing OpenL2M NeighborDevice()
        iface = self.get_interface_by_key(key=nb["IfIndex"])
        if iface:
            # now find existing NeighborDevice()
            neighbor = iface.get_neighbor(index=nb["NeighborIndex"])
            if neighbor:
                # the "Address" is base64 encoded
                try:
                    # decode the Base64 string into bytes
                    raw_bytes = base64.b64decode(nb["Address"])
                    # now figure out what type of address:
                    match nb["SubType"]:
                        # these are defined in the NetConf documentation:
                        case 1:
                            neighbor.management_address_v4 = socket.inet_ntoa(raw_bytes)
                        case 2:
                            neighbor.management_address_v6 = socket.inet_ntop(socket.AF_INET6, raw_bytes)
                        case _:
                            # unlikely to happen:
                            dprint(f"Unknown Management Address type {nb['SubType']} = base64({nb['Address']})")
                except Exception as err:
                    dprint(f"ERROR decoding LLDP remote address {nb['Address']} - {err}")

    #
    # set interface admin status (up/down)
    #
    def set_interface_admin_status(self, interface: Interface, new_state: bool) -> bool:
        """
        Set the interface to the requested state (up or down)

        Args:
            interface = Interface() object for the requested port
            new_state = True / False  (enabled/disabled)

        Returns:
            return True on success, False on error and set self.error variables
        """
        # interface.admin_status = new_state
        dprint(f"HPECwRestConnector.set_interface_admin_status() for {interface.name} to {bool(new_state)}")

        # status values: 1=up, 2=down
        if new_state:
            status = 1
        else:
            status = 2

        # query string parameters
        params = {
            "index": f"IfIndex={interface.key}",
        }
        # body data
        data = {
            "IfIndex": int(interface.key),
            "AdminStatus": status,
        }
        try:
            resp = self._put(path="Ifmgr/Interfaces", params=params, data=json.dumps(data))
            if resp:
                # all OK, now do the book keeping
                super().set_interface_admin_status(interface=interface, new_state=new_state)
                return True
            # error ?
            self.error.status = True
            self.error.description = "Error changing interface state!"
            self.error.details = "We're not sure what happened (?)"
            return False
        except Exception as err:
            self.error.status = True
            self.error.description = "Error changing interface state!"
            self.error.details = format(err)
            return False

    #
    # set interface description
    #
    def set_interface_description(self, interface: Interface, description: str) -> bool:
        """
        Set the interface description (aka. description) to the string

        Args:
            interface = Interface() object for the requested port
            description = a string with the requested text

        Returns:
            return True on success, False on error and set self.error variables
        """
        # interface.admin_status = new_state
        dprint(f"HPECwRestConnector.set_interface_description() for {interface.name} to '{description}'")

        if not description:
            # don't know yet how to handle deleting description!
            self.error.status = True
            self.error.description = "Clearing description is NOT implemented yet!"
            self.error.details = ""
            return False

        # query string parameters
        params = {
            "index": f"IfIndex={interface.key}",
        }
        # body data
        data = {
            "IfIndex": int(interface.key),
            "Description": description,
        }

        try:
            resp = self._put(path="Ifmgr/Interfaces", params=params, data=json.dumps(data))
            if resp:
                # all OK, now do the book keeping
                super().set_interface_description(interface=interface, description=description)
                return True
            # error ?
            self.error.status = True
            self.error.description = "Error setting description!"
            self.error.details = "We're not sure what happened (?)"
            return False
        except Exception as err:
            self.error.status = True
            self.error.description = "Error setting description!"
            self.error.details = format(err)
            return False

    def set_interface_poe_status(self, interface: Interface, new_state: int) -> bool:
        """
        set the interface Power-over-Ethernet status as given
        interface = Interface() object for the requested port

        Args:
            interface: the Interface to modify
            new_state = POE_PORT_ADMIN_ENABLED or POE_PORT_ADMIN_DISABLED

        Returns:
            True on success, False on error and set self.error variables
        """
        dprint(f"HPECwRestConnector.set_interface_poe_status() for {interface.name} to {new_state}")

        if not interface.poe_entry:
            # this should never happen!
            dprint("PoE change requested, but interface does not support PoE!!!")
            self.error.status = True
            self.error.description = "PoE change requested, but interface does not support PoE!!!"
            self.error.details = ""
            return False

        if interface.poe_entry.pse_id < 0:
            # this should never happen!
            dprint("PoE change requested, but invalid Power Suply ID found!")
            self.error.status = True
            self.error.description = "PoE change requested, but invalid Power Suply ID found!"
            self.error.details = ""
            return False

        # query string parameters, needs 2 index parameters!
        params = {
            "index": f"IfIndex={interface.key};PSEID={interface.poe_entry.pse_id}",
        }

        # set status values
        if new_state == POE_PORT_ADMIN_ENABLED:
            status = True
            status_name = "ON"
        else:
            status = False
            status_name = "OFF"

        # body data
        data = {
            "IfIndex": int(interface.key),
            "PSEID": int(interface.poe_entry.pse_id),
            "AdminEnable": status,   # True=PoE enabled, False=disabled
        }

        # go set PoE state
        try:
            resp = self._put(path="PoE/Ports", params=params, data=json.dumps(data))
            if resp:
                # all OK, now do the book keeping
                super().set_interface_poe_status(interface, new_state)
                return True
            # error ?
            self.error.status = True
            self.error.description = f"Error setting PoE state to {status_name}!"
            self.error.details = "We're not sure what happened (?)"
            return False
        except Exception as err:
            self.error.status = True
            self.error.description = f"Error setting PoE to {status_name}!"
            self.error.details = format(err)
            return False

    def set_interface_untagged_vlan(self, interface: Interface, new_vlan_id: int) -> bool:
        """
        Override the VLAN change
        return True on success, False on error and set self.error variables
        """
        dprint(
            f"HPECwRestConnector().set_interface_untagged_vlan() port {interface.name} to {new_vlan_id} ({type(new_vlan_id)})"
        )

        # validate new vlan
        new_vlan = self.get_vlan_by_id(new_vlan_id)
        if not new_vlan:
            self.error.status = True
            self.error.description = f"Cannot find Vlan object for vlan {new_vlan_id} for port '{interface.name}'"
            self.error.details = ""
            return False

        # the REST APi does not appear to "care" wether interface is untagged or tagged. Just set PVID !

        # query string parameters
        params = {
            "index": f"IfIndex={interface.key}",
        }

        # body data
        data = {
            "IfIndex": int(interface.key),
            "PVID": new_vlan_id,     # valid vlan id's
        }

        try:
            resp = self._put(path="Ifmgr/Interfaces", params=params, data=json.dumps(data))
            if resp:
                # all OK, now do the book keeping
                super().set_interface_untagged_vlan(interface=interface, new_vlan_id=new_vlan_id)
                return True
            # error ?
            self.error.status = True
            self.error.description = f"Error setting vlan {new_vlan_id}!"
            self.error.details = "We're not sure what happened (?)"
            return False
        except Exception as err:
            self.error.status = True
            self.error.description = f"Error setting vlan to {new_vlan_id}!"
            self.error.details = format(err)
            return False

    def set_interface_vlans(self, interface: Interface, untagged_vlan: int, tagged_vlans: List[int], allow_all: bool = False) -> bool:
        """
        Set the interface to the untagged and tagged vlans.

        Args:
            interface = Interface() object for the requested port
            untagged_vlan = an integer with the requested untagged vlan
            tagged_vlans = a List() of integer vlan id's that should be allowed as 802.1q tagged vlans.

        Returns:
            True on success, False on error and set self.error variables
        """
        dprint(
            f"HPECwRestConnector.set_interface_vlans() for {interface.name} to untagged {untagged_vlan}, tagged {tagged_vlans}, allow_all={allow_all}"
        )

        # query string parameters
        params = {
            "index": f"IfIndex={interface.key}",
        }

        # body data - the base settings
        data = {
            "IfIndex": int(interface.key),
            "PVID": untagged_vlan,     # valid vlan id's
        }

        if not tagged_vlans and not allow_all:
            # no tagged vlan, ie "access mode".
            dprint("ACCESS mode set vlan")
            mode = "access"
            if interface.is_tagged:
                # change mode as well
                dprint("  Changing to ACCESS")
                data['LinkType'] = 1    # 1 = Access
            else:
                dprint("Already Access mode!")
        else:
            # trunk mode, setup mode and native vlan:
            dprint("TAGGED mode set vlans")
            mode = "tagged"
            if not interface.is_tagged:
                # change mode as well
                dprint("  Changing to TRUNK")
                data['LinkType'] = 2    # 2 = Trunk
            else:
                dprint("Already Trunk mode!")

        # and make the API call for the Access/Trunk setting:
        try:
            dprint(f"Setting Mode to {mode}")
            resp = self._put(path="Ifmgr/Interfaces", params=params, data=json.dumps(data))
            if resp:
                dprint("  mode set OK!")
                # mode set OK. If tagged, add this interface to desired vlans:
                if allow_all or len(tagged_vlans):
                    dprint("Adding VLANs to TRUNK.")
                    trunk_vlan_list = []
                    for vlan_id in self.vlans:
                        dprint(f"Checking vlan_id {vlan_id} = {type(vlan_id)}")
                        if allow_all or vlan_id in tagged_vlans:
                            dprint(f"CW REST TRUNK SET: TRUNK ADDING Vlan {vlan_id}")
                            # for api call, we need a comma-separated list, created using .join(), so we need str() !
                            trunk_vlan_list.append(str(vlan_id))

                    # now use "VLAN/TrunkInterfaces" api endpoint to set trunk vlans.
                    # query parameters has index to interface
                    params = {
                        "index": f"IfIndex={interface.key}",
                    }

                    # body data has the list of allowed vlans
                    data = {
                        "IfIndex": int(interface.key),
                        "PermitVlanList": ','.join(trunk_vlan_list),
                    }

                    try:
                        success = self._put(path="VLAN/TrunkInterfaces", params=params, data=json.dumps(data))
                        if not success:
                            # not sure what happened!
                            self.error.status = True
                            self.error.description = "Error adding vlans to trunk! Interface is now in UNKNOWN state!"
                            self.error.details = ""
                            return False
                    except Exception as err:
                        self.error.status = True
                        self.error.description = "Error adding vlans to trunk! Interface is now in UNKNOWN state!"
                        self.error.details = format(err)
                        return False
                # all OK, now do the book keeping
                dprint("Calling Bookkeeping...")
                super().set_interface_vlans(interface=interface, untagged_vlan=untagged_vlan, tagged_vlans=tagged_vlans, allow_all=allow_all)
                return True
            # error ?
            self.error.status = True
            self.error.description = f"Error setting untagged vlan and {mode} mode!"
            self.error.details = "We're not sure what happened (?)"
            return False
        except Exception as err:
            self.error.status = True
            self.error.description = f"Error setting untagged vlan and {mode} mode"
            self.error.details = format(err)
            return False

    def vlan_create(self, vlan_id: int, vlan_name: str) -> bool:
        """
        Create a new vlan on this device. Upon success, this then needs to call the base class for book keeping!

        Args:
            id (int): the vlan id
            name (str): the name of the vlan

        Returns:
            True on success, False on error and set self.error variables.
        """
        dprint(f"HPECwRestConnector.vlan_create() for vlan {vlan_id} = '{vlan_name}'")

        # NO query string parameters

        # new vlan attributes in POST body data
        data = {
            "ID": vlan_id,
            "Name": vlan_name,
        }

        try:
            # create requires a HTTP POST
            success = self._post(path="VLAN/VLANs", data=json.dumps(data))
            if success:
                # all OK, now do the book keeping
                super().vlan_create(vlan_id=vlan_id, vlan_name=vlan_name)
                return True
            # error ?
            self.error.status = True
            self.error.description = "Error creating vlan!"
            self.error.details = f"We're not sure what happened (?) Http return code {self.response.status_code}"
            return False
        except Exception as err:
            self.error.status = True
            self.error.description = "Error creating vlan!"
            self.error.details = format(err)
            return False

    def vlan_edit(self, vlan_id: int, vlan_name: str) -> bool:
        """
        Edit the vlan name. Upon success, this then needs to call the base class for book keeping!

        Args:
            id (int): the vlan id to edit
            name (str): the new name of the vlan

        Returns:
            True on success, False on error and set self.error variables.
        """
        dprint(f"HPECwRestConnector.vlan_edit() for vlan {vlan_id} = '{vlan_name}'")

        vlan = self.get_vlan_by_id(vlan_id)
        if not vlan:
            self.error.status = True
            self.error.description = f"Vlan {vlan_id} does not exist!"
            self.error.details = ""
            return False

        # edit is a PUT with a query string with the VLAN ID as index
        params = {
            "index": f"ID={vlan_id}",
        }

        # and body data with the updated values.
        data = {
            "ID": vlan_id,
            "Name": vlan_name,
            # "Description": not supported...,
        }

        try:
            # create requires a HTTP POST
            success = self._put(path="VLAN/VLANs", params=params, data=json.dumps(data))
            if success:
                # all OK, now do the book keeping
                super().vlan_edit(vlan_id=vlan_id, vlan_name=vlan_name)
                return True
            # error ?
            self.error.status = True
            self.error.description = "Error editing vlan!"
            self.error.details = f"We're not sure what happened (?) Http return code {self.response.status_code}"
            return False
        except Exception as err:
            self.error.status = True
            self.error.description = "Error editing vlan!"
            self.error.details = format(err)
            return False

    def vlan_delete(self, vlan_id: int) -> bool:
        """
        Delete the vlan. Upon success, this then needs to call the base class for book keeping!

        Args:
            id (int): the vlan id to delete

        Returns:
            True on success, False on error and set self.error variables.
        """
        dprint(f"HPECwRestConnector.vlan_delete() for vlan {vlan_id}")

        vlan = self.get_vlan_by_id(vlan_id)
        if not vlan:
            self.error.status = True
            self.error.description = f"Vlan {vlan_id} does not exist!"
            self.error.details = ""
            return False

        # this is a simple HTTP DELETE call, with vlan ID as query string parameter
        params = {
            "index": f"ID={vlan_id}",
        }
        try:
            success = self._delete(path="VLAN/VLANs", params=params)
            if success:
                # all OK, now do the book keeping
                super().vlan_delete(vlan_id=vlan_id)
                return True
            # error ?
            self.error.status = True
            self.error.description = "Error deleting vlan!"
            self.error.details = f"We're not sure what happened (?) Http return code {self.response.status_code}"
            return False
        except Exception as err:
            self.error.status = True
            self.error.description = "Error deleting vlan!"
            self.error.details = format(err)
            return False

    def save_running_config(self) -> bool:
        """
        save the current config to startup. Note this uses SSH (Netmiko), as this is NOT supported via the REST API.

        Returns:
            (bool) - True if this succeeds, False on failure. self.error() will be set in that case
        """
        dprint("HPECwRestConnector().save_running_config()")

        # Not implemented in API, so run the save command with _execute_command(), which uses Netmiko / SSH
        return self._execute_command(command="save force")

    #
    # support functions
    #
    def _get_interface_by_port_id(self, port_id: int):
        """Get an Interface() object from a given switch port id (int)"""
        dprint(f"HPECwRestConnector._get_interface_by_port_id() for port_id={port_id}")

        try:
            return self.get_interface_by_key(key=self.port_index_to_if_index[port_id])
        except Exception as e:
            dprint(f"Error finding interface for port '{port_id}': {e}")
        return None
