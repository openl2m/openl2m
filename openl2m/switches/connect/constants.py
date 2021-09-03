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

# various global constants used throughout the various connector methods:
# some of these are the equivalent of the snmp mib counterparts!

# Enumeration, see https://www.iana.org/assignments/ianaiftype-mib/ianaiftype-mib
IF_TYPE_NONE = 0
IF_TYPE_ETHERNET = 6    # Ethernet-like (ethernetCsmacd)
IF_TYPE_LOOPBACK = 24   # interface Loopback X (softwareLoopback)
IF_TYPE_VIRTUAL = 53    # interface Vlan X (proprietary virtual/internal)
IF_TYPE_LAGG = 161      # IEEE 802.3ad Link Aggregate

# the list of interfaces visible to a regular user!
visible_interfaces = {
    IF_TYPE_ETHERNET: True,
    IF_TYPE_LAGG: True,
}

ENTITY_CLASS_CHASSIS = 3    # chassis(3) - the physical device, eg the 1U switch in a stack
ENTITY_CLASS_MODULE = 9     # module(9) - a module or blade in a chassis
ENTITY_CLASS_STACK = 11     # stack(11)
ENTITY_CLASS_NAME = {}
ENTITY_CLASS_NAME[ENTITY_CLASS_CHASSIS] = 'Chassis'
ENTITY_CLASS_NAME[ENTITY_CLASS_MODULE] = 'Module'
ENTITY_CLASS_NAME[ENTITY_CLASS_STACK] = 'Stack'

# GVRP related
GVRP_ENABLED = 1
GVRP_DISABLED = 2

# LLDP related
LLDP_CHASSIC_TYPE_COMP = 1      # chassisComponent(1)
LLDP_CHASSIC_TYPE_ALIAS = 2     # interfaceAlias(2), ifAlias from IF-MIB
LLDP_CHASSIC_TYPE_PORT = 3      # portComponent(3)
LLDP_CHASSIC_TYPE_ETH_ADDR = 4  # macAddress(4), standard Ethernet address
LLDP_CHASSIC_TYPE_NET_ADDR = 5  # networkAddress(5), first byte is address type, next bytes are address.
# see https://www.iana.org/assignments/address-family-numbers/address-family-numbers.xhtml
IANA_TYPE_IPV4 = 1
IANA_TYPE_IPV6 = 2
LLDP_CHASSIC_TYPE_IFNAME = 6    # interfaceName(6), ifName from IF-MIB
LLDP_CHASSIC_TYPE_LOCAL = 7    # local(7)

# Capabilities as announced via lldp bits in SNMP data, translated to integer:
LLDP_CAPABILITIES_OTHER = 128     # other(0),
LLDP_CAPABILITIES_REPEATER = 64  # repeater(1),
LLDP_CAPABILITIES_BRIDGE = 32    # bridge(2),
LLDP_CAPABILITIES_WLAN = 16      # wlanAccessPoint(3),
LLDP_CAPABILITIES_ROUTER = 8    # router(4),
LLDP_CAPABILITIES_PHONE = 4     # telephone(5)
LLDP_CAPABILITIES_DOCSIS = 2    # docsisCableDevice(6),
LLDP_CAPABILITIES_STATION = 1   # stationOnly(7)
LLDP_CAPABILITIES_NONE = 0

# PoE PowerSupply related
POE_PSE_STATUS_ON = 1
POE_PSE_STATUS_OFF = 2
POE_PSE_STATUS_FAULT = 3

# PoE port/interface related
POE_PORT_ADMIN_ENABLED = 1
POE_PORT_ADMIN_DISABLED = 2

POE_PORT_DETECT_DISABLED = 1     # '1' = disabled
POE_PORT_DETECT_SEARCHING = 2    # ’2’ = searching
POE_PORT_DETECT_DELIVERING = 3   # ’3’ = deliveringPower
POE_PORT_DETECT_FAULT = 4        # ’4’ = fault
POE_PORT_DETECT_TEST = 5         # ’5’ = test
POE_PORT_DETECT_OTHERFAULT = 6   # ’6’ = otherFault
poe_status_name = {}
poe_status_name[POE_PORT_DETECT_DISABLED] = 'Disabled'
poe_status_name[POE_PORT_DETECT_SEARCHING] = 'Searching'
poe_status_name[POE_PORT_DETECT_DELIVERING] = 'Delivering'
poe_status_name[POE_PORT_DETECT_FAULT] = 'Fault'
poe_status_name[POE_PORT_DETECT_TEST] = 'Test'
poe_status_name[POE_PORT_DETECT_OTHERFAULT] = 'Unknown Fault'

POE_PORT_PRIORITY_CRITICAL = 1   # '1' = Critical
POE_PORT_PRIORITY_HIGH = 2       # '2' = High
POE_PORT_PRIORITY_LOW = 3        # '3' = Low
poe_priority_name = {}
poe_priority_name[POE_PORT_PRIORITY_CRITICAL] = "Critical"
poe_priority_name[POE_PORT_PRIORITY_HIGH] = "High"
poe_priority_name[POE_PORT_PRIORITY_LOW] = "Low"

# status related to dynamic vlans
VLAN_STATUS_OTHER = 1
VLAN_STATUS_PERMANENT = 2
VLAN_STATUS_DYNAMIC = 3

# mostly used for Cisco vlans, to avoid the 1000-1003 range. This is "regular(1)" in the Cisco VTP mib
VLAN_TYPE_NORMAL = 1    # used to indicate 'normal' vlans,
