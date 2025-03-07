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
import netaddr

# various global constants used throughout the various connector methods:
# some of these are the equivalent of the snmp mib counterparts!

# Enumeration, see https://www.iana.org/assignments/ianaiftype-mib/ianaiftype-mib
IF_TYPE_NONE = 0
IF_TYPE_OTHER = 1  # None of the following :-)
IF_TYPE_ETHERNET = 6  # Ethernet-like (ethernetCsmacd)
IF_TYPE_LOOPBACK = 24  # interface Loopback X (softwareLoopback)
IF_TYPE_VIRTUAL = 53  # interface Vlan X (proprietary virtual/internal)
IF_TYPE_L3IPVLAN = 136  # IP vlan interface (used by Arista)
IF_TYPE_TUNNEL = 131  # generic Tunnel interface
IF_TYPE_MPLS_TUNNEL = 150  # MPLS Tunnel Virtual Interface
IF_TYPE_LAGG = 161  # IEEE 802.3ad Link Aggregate
IF_TYPE_MCAST = 1025  # undefined by IEEE, but used by OpenL2M to indicate various multicast virtual interfaces
# for reporting, create generic list of virtual interfaces:
VIRTUAL_INTERFACES = [IF_TYPE_LOOPBACK, IF_TYPE_VIRTUAL, IF_TYPE_TUNNEL, IF_TYPE_MCAST]

# duplex settings, from the snmp dot3StatsDuplexStatus object.
IF_DUPLEX_UNKNOWN = 1
IF_DUPLEX_HALF = 2
IF_DUPLEX_FULL = 3
duplex_name = {
    IF_DUPLEX_UNKNOWN: "Unknown",
    IF_DUPLEX_HALF: "Half",
    IF_DUPLEX_FULL: "Full",
}

LACP_IF_TYPE_NONE = 0  # not port of LACP aggregation
LACP_IF_TYPE_MEMBER = 1  # this is a physical port and member
LACP_IF_TYPE_AGGREGATOR = 2  # this is an aggregator port (Port-Channel or Bridge-Aggregation)

# the list of interfaces visible to a regular user!
visible_interfaces = {
    IF_TYPE_ETHERNET: True,
    IF_TYPE_LAGG: True,
}

ENTITY_CLASS_CHASSIS = 3  # chassis(3) - the physical device, eg the 1U switch in a stack
ENTITY_CLASS_MODULE = 9  # module(9) - a module or blade in a chassis
ENTITY_CLASS_STACK = 11  # stack(11)
ENTITY_CLASS_NAME = {}
ENTITY_CLASS_NAME[ENTITY_CLASS_CHASSIS] = 'Chassis'
ENTITY_CLASS_NAME[ENTITY_CLASS_MODULE] = 'Module'
ENTITY_CLASS_NAME[ENTITY_CLASS_STACK] = 'Stack'

# GVRP related
GVRP_ENABLED = 1
GVRP_DISABLED = 2

# LLDP related
LLDP_CHASSIS_TYPE_NONE = 0
LLDP_CHASSIC_TYPE_COMP = 1  # chassisComponent(1)
LLDP_CHASSIC_TYPE_ALIAS = 2  # interfaceAlias(2), ifAlias from IF-MIB
LLDP_CHASSIC_TYPE_PORT = 3  # portComponent(3)
LLDP_CHASSIC_TYPE_ETH_ADDR = 4  # macAddress(4), standard Ethernet address
LLDP_CHASSIC_TYPE_NET_ADDR = 5  # networkAddress(5), first byte is address type, next bytes are address.
# see https://www.iana.org/assignments/address-family-numbers/address-family-numbers.xhtml
IANA_TYPE_OTHER = 0
IANA_TYPE_IPV4 = 1
IANA_TYPE_IPV6 = 2
LLDP_CHASSIC_TYPE_IFNAME = 6  # interfaceName(6), ifName from IF-MIB
LLDP_CHASSIC_TYPE_LOCAL = 7  # local(7) - a string locally assigned, likely a name.

# Capabilities as announced via lldp bits in SNMP data, translated to integer.
# see also switches.connect.snmp.constants
LLDP_CAPABILITIES_OTHER = 128  # other(0),
LLDP_CAPABILITIES_REPEATER = 64  # repeater(1),
LLDP_CAPABILITIES_BRIDGE = 32  # bridge(2),
LLDP_CAPABILITIES_WLAN = 16  # wlanAccessPoint(3),
LLDP_CAPABILITIES_ROUTER = 8  # router(4),
LLDP_CAPABILITIES_PHONE = 4  # telephone(5)
LLDP_CAPABILITIES_DOCSIS = 2  # docsisCableDevice(6),
LLDP_CAPABILITIES_STATION = 1  # stationOnly(7)
LLDP_CAPABILITIES_NONE = 0

# this is used to indate the type of data sent by lldpRemPortId
# see https://www.circitor.fr/Mibs/Html/L/LLDP-MIB.php#LldpChassisIdSubtype
# chassisComponent(1), interfaceAlias(2), portComponent(3), macAddress(4),
# networkAddress(5), interfaceName(6), local(7)
LLDP_PORT_SUBTYPE_CHASSIS_COMPONENT = 1
LLDP_PORT_SUBTYPE_INTERFACE_ALIAS = (2,)
LLDP_PORT_SUBTYPE_PORT_COMPONENT = 3
LLDP_PORT_SUBTYPE_MAC_ADDRESS = (4,)
LLDP_PORT_SUBTYPE_NETWORK_ADDRESS = 5
LLDP_PORT_SUBTYPE_INTERFACE_NAME = 6
LLDP_PORT_SUBTYPE_LOCAL = 7

# the various device types supported by the current Netmiko library (September 2024)
# see the netmiko source code "CLASS_MAPPER_BASE" variable in
# https://github.com/ktbyers/netmiko/blob/develop/netmiko/ssh_dispatcher.py
NETMIKO_DEVICE_TYPES = (
    ('a10', 'a10'),
    ('accedian', 'accedian'),
    ('alcatel_aos', 'alcatel_aos'),
    ('alcatel_sros', 'alcatel_sros'),
    ('apresia_aeos', 'apresia_aeos'),
    ('arista_eos', 'arista_eos'),
    ('aruba_aoscx', 'aruba_aoscx'),
    ('aruba_os', 'aruba_os'),
    ('avaya_ers', 'avaya_ers'),
    ('avaya_vsp', 'avaya_vsp'),
    ('brocade_fastiron', 'brocade_fastiron'),
    ('brocade_netiron', 'brocade_netiron'),
    ('brocade_nos', 'brocade_nos'),
    ('brocade_vdx', 'brocade_vdx'),
    ('brocade_vyos', 'brocade_vyos'),
    ('calix_b6', 'calix_b6'),
    ('checkpoint_gaia', 'checkpoint_gaia'),
    ('ciena_saos', 'ciena_saos'),
    ('cisco_asa', 'cisco_asa'),
    ('cisco_ios', 'cisco_ios'),
    ('cisco_nxos', 'cisco_nxos'),
    ('cisco_s300', 'cisco_s300'),
    ('cisco_tp', 'cisco_tp'),
    ('cisco_wlc', 'cisco_wlc'),
    ('cisco_xe', 'cisco_xe'),
    ('cisco_xr', 'cisco_xr'),
    ('cloudgenix_ion', 'cloudgenix_ion'),
    ('coriant', 'coriant'),
    ('dell_dnos9', 'dell_dnos9'),
    ('dell_force10', 'dell_force10'),
    ('dell_isilon', 'dell_isilon'),
    ('dell_os10', 'dell_os10'),
    ('dell_os6', 'dell_os6'),
    ('dell_os9', 'dell_os9'),
    ('dell_powerconnect', 'dell_powerconnect'),
    ('eltex', 'eltex'),
    ('endace', 'endace'),
    ('enterasys', 'enterasys'),
    ('extreme', 'extreme'),
    ('extreme_ers', 'extreme_ers'),
    ('extreme_exos', 'extreme_exos'),
    ('extreme_netiron', 'extreme_netiron'),
    ('extreme_nos', 'extreme_nos'),
    ('extreme_slx', 'extreme_slx'),
    ('extreme_vdx', 'extreme_vdx'),
    ('extreme_vsp', 'extreme_vsp'),
    ('extreme_wing', 'extreme_wing'),
    ('f5_linux', 'f5_linux'),
    ('f5_ltm', 'f5_ltm'),
    ('f5_tmsh', 'f5_tmsh'),
    ('flexvnf', 'flexvnf'),
    ('fortinet', 'fortinet'),
    ('generic_termserver', 'generic_termserver'),
    ('hp_comware', 'hp_comware'),
    ('hp_procurve', 'hp_procurve'),
    ('huawei', 'huawei'),
    ('huawei_vrpv8', 'huawei_vrpv8'),
    ('ipinfusion_ocnos', 'ipinfusion_ocnos'),
    ('juniper', 'juniper'),
    ('juniper_junos', 'juniper_junos'),
    ('linux', 'linux'),
    ('mellanox', 'mellanox'),
    ('mikrotik_routeros', 'mikrotik_routeros'),
    ('mikrotik_switchos', 'mikrotik_switchos'),
    ('mrv_lx', 'mrv_lx'),
    ('mrv_optiswitch', 'mrv_optiswitch'),
    ('netapp_cdot', 'netapp_cdot'),
    ('netscaler', 'netscaler'),
    ('oneaccess_oneos', 'oneaccess_oneos'),
    ('ovs_linux', 'ovs_linux'),
    ('paloalto_panos', 'paloalto_panos'),
    ('pluribus', 'pluribus'),
    ('quanta_mesh', 'quanta_mesh'),
    ('rad_etx', 'rad_etx'),
    ('ruckus_fastiron', 'ruckus_fastiron'),
    ('ubiquiti_edge', 'ubiquiti_edge'),
    ('ubiquiti_edgeswitch', 'ubiquiti_edgeswitch'),
    ('vyatta_vyos', 'vyatta_vyos'),
    ('vyos', 'vyos'),
)

# the vendors supported by our Napalm libraries.
# Note: if you add a vendor here, you will also need to add the proper commands
# to the napalm_commands dictionary in napalm/commands.py
NAPALM_DEVICE_TYPES = (
    ('', 'None'),
    ('eos', 'Arista EOS'),
    ('aoscx', 'Aruba AOS-CX'),
    ('ios', 'Cisco IOS'),
    ('iosxr', 'Cisco IOS-XR'),
    ('nxos_ssh', 'Cisco NX-OS SSH'),
    ('dellos10', 'Dell OS10'),
    ('procurve', 'HP Procurve'),
    ('junos', 'Juniper JunOS'),
)

# PoE PowerSupply related
POE_PSE_STATUS_ON = 1
POE_PSE_STATUS_OFF = 2
POE_PSE_STATUS_FAULT = 3
poe_pse_status_name = {
    POE_PSE_STATUS_ON: "On",
    POE_PSE_STATUS_OFF: "Off",
    POE_PSE_STATUS_FAULT: "Fault",
}

# PoE port/interface related
POE_PORT_ADMIN_ENABLED = 1
POE_PORT_ADMIN_DISABLED = 2
poe_admin_status_name = {
    POE_PORT_ADMIN_ENABLED: "Enabled",
    POE_PORT_ADMIN_DISABLED: "Disabled",
}

POE_PORT_DETECT_DISABLED = 1  # '1' = disabled
POE_PORT_DETECT_SEARCHING = 2  # ’2’ = searching
POE_PORT_DETECT_DELIVERING = 3  # ’3’ = deliveringPower
POE_PORT_DETECT_FAULT = 4  # ’4’ = fault
POE_PORT_DETECT_TEST = 5  # ’5’ = test
POE_PORT_DETECT_OTHERFAULT = 6  # ’6’ = otherFault
poe_status_name = {}
poe_status_name[POE_PORT_DETECT_DISABLED] = 'Disabled'
poe_status_name[POE_PORT_DETECT_SEARCHING] = 'Searching'
poe_status_name[POE_PORT_DETECT_DELIVERING] = 'Delivering'
poe_status_name[POE_PORT_DETECT_FAULT] = 'Fault'
poe_status_name[POE_PORT_DETECT_TEST] = 'Test'
poe_status_name[POE_PORT_DETECT_OTHERFAULT] = 'Unknown Fault'

POE_PORT_PRIORITY_CRITICAL = 1  # '1' = Critical
POE_PORT_PRIORITY_HIGH = 2  # '2' = High
POE_PORT_PRIORITY_LOW = 3  # '3' = Low
poe_priority_name = {}
poe_priority_name[POE_PORT_PRIORITY_CRITICAL] = "Critical"
poe_priority_name[POE_PORT_PRIORITY_HIGH] = "High"
poe_priority_name[POE_PORT_PRIORITY_LOW] = "Low"

# status related to dynamic vlans
VLAN_STATUS_OTHER = 1
VLAN_STATUS_PERMANENT = 2
VLAN_STATUS_DYNAMIC = 3
vlan_status_name = {}
vlan_status_name[VLAN_STATUS_OTHER] = "Other"
vlan_status_name[VLAN_STATUS_PERMANENT] = "Permanent"
vlan_status_name[VLAN_STATUS_DYNAMIC] = "Dynamic"

VLAN_ADMIN_ENABLED = 1
VLAN_ADMIN_DISABLED = 2
vlan_admin_name = {}
vlan_admin_name[VLAN_ADMIN_ENABLED] = "Enabled"
vlan_admin_name[VLAN_ADMIN_DISABLED] = "Disabled"

# mostly used for Cisco vlans, to avoid the 1000-1003 range. This is "regular(1)" in the Cisco VTP mib
VLAN_TYPE_NORMAL = 1  # used to indicate 'normal' vlans,

# special IP addresses:
IPV4_LINK_LOCAL = "169.254.0.0/16"
IPV4_PRIVATES = ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
IPV6_LINK_LOCAL = "fe80::/10"
IPV6_PRIVATE = "fc00::7"

IPV6_LINK_LOCAL_NETWORK = netaddr.IPNetwork(IPV6_LINK_LOCAL)
