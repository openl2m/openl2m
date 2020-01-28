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
SNMP related constants.
"""
SNMP_TRUE = 1
SNMP_FALSE = 2

"""
SNMP MIB variables names and their string numeric value. EasySNMP uses the formal notation starting with ".""
"""
# a good place for some more info at:
# http://cric.grenoble.cnrs.fr/Administrateurs/Outils/MIBS/?oid=1.3.6.1.2.1
# and also  https://www.alvestrand.no/objectid/1.3.6.1.2.1.html

snmp_mib_variables = {}

#
# SYSTEM RELATED
#
SYS_MIB = '.1.3.6.1.2.1.1'
snmp_mib_variables['system'] = SYS_MIB

SYS_DESCR = '.1.3.6.1.2.1.1.1.0'
snmp_mib_variables['sysDescr'] = SYS_DESCR

SYS_OBJECTID = '.1.3.6.1.2.1.1.2.0'
snmp_mib_variables['sysObjectID'] = SYS_OBJECTID

SYS_UPTIME = '.1.3.6.1.2.1.1.3.0'
snmp_mib_variables['sysUpTime'] = SYS_UPTIME

SYS_CONTACT = '.1.3.6.1.2.1.1.4.0'
snmp_mib_variables['sysContact'] = SYS_CONTACT

SYS_NAME = '.1.3.6.1.2.1.1.5.0'
snmp_mib_variables['sysName'] = SYS_NAME

SYS_LOCATION = '.1.3.6.1.2.1.1.6.0'
snmp_mib_variables['sysLocation'] = SYS_LOCATION

snmp_mib_variables['sysServices'] = '.1.3.6.1.2.1.1.7.0'

#
# INTERFACE RELATED
#
IF_NUMBER = '.1.3.6.1.2.1.2.1.0'   # interface count on device
snmp_mib_variables['ifNumber'] = IF_NUMBER

#
# OLD "Interfaces" part of MIB-2, for HighSpeed, see ifMIB extensions at .31
INTERFACES_MIB = '.1.3.6.1.2.1.2.2.1'  # see also: https://www.alvestrand.no/objectid/1.3.6.1.2.1.2.2.1.html
snmp_mib_variables['ifTable'] = INTERFACES_MIB

IF_INDEX = '.1.3.6.1.2.1.2.2.1.1'   # https://www.alvestrand.no/objectid/1.3.6.1.2.1.2.2.1.1.html
snmp_mib_variables['ifIndex'] = IF_INDEX

IF_DESCR = '.1.3.6.1.2.1.2.2.1.2'  # the OLD interface name, see IFMIB_NAME below
snmp_mib_variables['ifDescr'] = IF_DESCR

IF_TYPE = '.1.3.6.1.2.1.2.2.1.3'
snmp_mib_variables['ifType'] = IF_TYPE

# Enumeration, see https://www.iana.org/assignments/ianaiftype-mib/ianaiftype-mib
IF_TYPE_ETHERNET = 6    # Ethernet-like (ethernetCsmacd)
IF_TYPE_LOOPBACK = 24   # interface Loopback X (softwareLoopback)
IF_TYPE_VIRTUAL = 53    # interface Vlan X (proprietary virtual/internal)
IF_TYPE_LAGG = 161      # IEEE 802.3ad Link Aggregate

# the list of interfaces visible to a regular user!
visible_interfaces = {
    IF_TYPE_ETHERNET: True,
    IF_TYPE_LAGG: True,
}

IF_MTU = '.1.3.6.1.2.1.2.2.1.4'
snmp_mib_variables['ifMtu'] = IF_MTU

IF_SPEED = '.1.3.6.1.2.1.2.2.1.5'
snmp_mib_variables['ifSpeed'] = IF_SPEED

IF_PHYS_ADDR = '.1.3.6.1.2.1.2.2.1.6'
snmp_mib_variables['ifPhysAddress'] = IF_PHYS_ADDR

IF_ADMIN_STATUS = '.1.3.6.1.2.1.2.2.1.7'
snmp_mib_variables['ifAdminStatus'] = IF_ADMIN_STATUS

IF_ADMIN_STATUS_UP = 1
IF_ADMIN_STATUS_DOWN = 2

IF_OPER_STATUS = '.1.3.6.1.2.1.2.2.1.8'
snmp_mib_variables['ifOperStatus'] = IF_OPER_STATUS

IF_OPER_STATUS_UP = 1
IF_OPER_STATUS_DOWN = 2

"""
Currently not used, best served from a Network Management application:

IF_LAST_CHANGE = '.1.3.6.1.2.1.2.2.1.9'
snmp_mib_variables['ifLastChange'] =  IF_LAST_CHANGE

IF_IN_OCTETS = '.1.3.6.1.2.1.2.2.1.10'
snmp_mib_variables['ifInOctets'] = IF_IN_OCTETS'

IF_IN_UCAST_PKTS = '.1.3.6.1.2.1.2.2.1.11'
snmp_mib_variables['ifInUcastPkts'] = IF_IN_UCAST_PKTS

IF_IN_NUCAST_PKTS = '.1.3.6.1.2.1.2.2.1.12'
snmp_mib_variables['ifInNUcastPkts'] = IF_IN_NUCAST_PKTS

IF_IN_DISCARDS = '.1.3.6.1.2.1.2.2.1.13'
snmp_mib_variables['ifInDiscards'] = IF_IN_DISCARDS

IF_IN_ERRORS = '.1.3.6.1.2.1.2.2.1.14'
snmp_mib_variables['ifInErrors'] = IF_IN_ERRORS

IF_IN_UNKNOWN_PROTOS = '.1.3.6.1.2.1.2.2.1.15'
snmp_mib_variables['ifInUnknownProtos'] = IF_IN_UNKNOWN_PROTOS

IF_OUT_OCTETS = '.1.3.6.1.2.1.2.2.1.16'
snmp_mib_variables['ifOutOctets'] = IF_OUT_OCTETS

IF_OUT_UCAST_PKTS = '.1.3.6.1.2.1.2.2.1.17'
snmp_mib_variables['ifOutUcastPkts'] = IF_OUT_UCAST_PKTS

IF_OUT_NUCAST_PKTS = '.1.3.6.1.2.1.2.2.1.18'
snmp_mib_variables['ifOutNUcastPkts'] = IF_OUT_NUCAST_PKTS

IF_OUT_DISCARDS = '.1.3.6.1.2.1.2.2.1.19'
snmp_mib_variables['ifOutDiscards'] = '.1.3.6.1.2.1.2.2.1.19'

IF_OUT_ERRORS = '.1.3.6.1.2.1.2.2.1.20'
snmp_mib_variables['ifOutErrors'] = IF_OUT_DISCARDS

#not sure we care about these:
IF_OUT_QLEN = '.1.3.6.1.2.1.2.2.1.19'
snmp_mib_variables['ifOutQLen'] = IF_OUT_QLEN

IF_SPECIFIC = '.1.3.6.1.2.1.2.2.1.20'
snmp_mib_variables['ifSpecific'] =  IF_SPECIFIC
"""


#
# the IP address(es) of the switch
#
IP_ADDRESS_ENTRY = '.1.3.6.1.2.1.4.20'
snmp_mib_variables['ipAddrTable'] = IP_ADDRESS_ENTRY

# and the sub-entities:
IP_ADDRESS_ADDR = '.1.3.6.1.2.1.4.20.1.1'
snmp_mib_variables['ipAdEntAddr'] = IP_ADDRESS_ADDR

IP_ADDRESS_IFINDEX = '.1.3.6.1.2.1.4.20.1.2'
snmp_mib_variables['ipAdEntIfIndex'] = IP_ADDRESS_IFINDEX

IP_ADDRESS_NETMASK = '.1.3.6.1.2.1.4.20.1.3'
snmp_mib_variables['ipAdEntNetMask'] = IP_ADDRESS_NETMASK

#
# ARP Table related, using the modern Entries#
#
# the older ipNetToMedia tables:
IP_NET_TO_MEDIA_MIB = '.1.3.6.1.2.1.4.22'
snmp_mib_variables['ipNetToMediaTable'] = IP_NET_TO_MEDIA_MIB

IP_NET_TO_MEDIA_IFINDEX = '.1.3.6.1.2.1.4.22.1.1'
snmp_mib_variables['ipNetToMediaIfIndex'] = IP_NET_TO_MEDIA_IFINDEX

IP_NET_TO_MEDIA_PHYSADDR = '.1.3.6.1.2.1.4.22.1.2'
snmp_mib_variables['ipNetToMediaPhysAddress'] = IP_NET_TO_MEDIA_PHYSADDR

# ipNetToMediaNetAddress is the 'arp' table,
IP_NET_TO_MEDIA_NETADDR = '.1.3.6.1.2.1.4.22.1.3'
snmp_mib_variables['ipNetToMediaNetAddress'] = IP_NET_TO_MEDIA_NETADDR

#
# the newer ipNetToPhysical tables:
IP_NET_TO_PHYSICAL = '.1.3.6.1.2.1.4.35.1'
snmp_mib_variables['ipNetToPhysicalEntry'] = IP_NET_TO_PHYSICAL

IP_NET_TO_PHYSICAL_IFINDEX = '.1.3.6.1.2.1.4.35.1.1'
snmp_mib_variables['ipNetToPhysicalIfIndex'] = IP_NET_TO_PHYSICAL_IFINDEX

IP_NET_TO_PHYSICAL_NET_ADDR_TYPE = '.1.3.6.1.2.1.4.35.1.2'
snmp_mib_variables['ipNetToPhysicalNetAddressType'] = IP_NET_TO_PHYSICAL_NET_ADDR_TYPE

IP_NET_TO_PHYSICAL_NET_ADDR = '.1.3.6.1.2.1.4.35.1.3'
snmp_mib_variables['ipNetToPhysicalNetAddress'] = IP_NET_TO_PHYSICAL_NET_ADDR

IP_NET_TO_PHYSICAL_NET_PHYSADDR = '.1.3.6.1.2.1.4.35.1.4'
snmp_mib_variables['ipNetToPhysicalPhysAddress'] = IP_NET_TO_PHYSICAL_NET_PHYSADDR

#

dot3StatsDuplexStatus = '.1.3.6.1.2.1.10.7.2.1.19'
snmp_mib_variables['dot3StatsDuplexStatus'] = dot3StatsDuplexStatus

#
# BRIDGE MIB RELATED
#
BRIDGE_MIB = '.1.3.6.1.2.1.17'   # orignal Bridge-MIB, including Ethernet-to-Interface mappings
snmp_mib_variables['dot1dBridge'] = BRIDGE_MIB

# base settings about the 802.1q config:
dot1qBase = '.1.3.6.1.2.1.17.7.1.1'
snmp_mib_variables['dot1qBase'] = dot1qBase

dot1qVlanVersionNumber = '.1.3.6.1.2.1.17.7.1.1.1'
snmp_mib_variables['dot1qVlanVersionNumber'] = dot1qVlanVersionNumber

dot1qMaxVlanId = '.1.3.6.1.2.1.17.7.1.1.2'
snmp_mib_variables['dot1qMaxVlanId'] = dot1qMaxVlanId

dot1qMaxSupportedVlans = '.1.3.6.1.2.1.17.7.1.1.3'
snmp_mib_variables['dot1qMaxSupportedVlans'] = dot1qMaxSupportedVlans

dot1qNumVlans = '.1.3.6.1.2.1.17.7.1.1.4'
snmp_mib_variables['dot1qNumVlans'] = dot1qNumVlans

dot1qGvrpStatus = '.1.3.6.1.2.1.17.7.1.1.5'
snmp_mib_variables['dot1qGvrpStatus'] = dot1qGvrpStatus
GVRP_ENABLED = 1
GVRP_DISABLED = 2

# dot1dBasePortIfIndex, this maps the port number to the ifIndex in MIB-II
BRIDGE_PORT_TO_INDEX_MAP = '.1.3.6.1.2.1.17.1.4.1.2'
snmp_mib_variables['dot1dBasePortIfIndex'] = BRIDGE_PORT_TO_INDEX_MAP

# Getting Ethernet addresses on ports:
# walk dot1dTpFdbAddress
BRIDGE_ACTIVE_ETH_ADDRESSES = '.1.3.6.1.2.1.17.4.3.1.1'
snmp_mib_variables['dot1dTpFdbAddress'] = BRIDGE_ACTIVE_ETH_ADDRESSES

# more useful is this, dot1dTpFdbPort. The 'sub-oid' values represent the ethernet address,
# return value is the 'port id', mapped below in
BRIDGE_ACTIVE_ETH_ADDRESSES_BY_PORT = '.1.3.6.1.2.1.17.4.3.1.2'
snmp_mib_variables['dot1dTpFdbPort'] = BRIDGE_ACTIVE_ETH_ADDRESSES_BY_PORT

#
# VLAN Q-BRIDGE RELATED
#
QBRIDGE_MIB = '.1.3.6.1.2.1.17.7'   # Expanded 802.1Q MIB, includes VLAN info, etc.
snmp_mib_variables['qBridgeMIB'] = QBRIDGE_MIB

QBRIDGE_VLAN_CURRENT_ENTRY = '.1.3.6.1.2.1.17.7.1.4.2.1'
snmp_mib_variables['dot1qVlanCurrentEntry'] = QBRIDGE_VLAN_CURRENT_ENTRY

# NOTE _ NOTE _ NOTE:
# The QBRIDGE_VLAN_CURRENT_* entries are READ-only
#


# List of all ports on a vlan as a hexstring (including native vlan)
"""
PortList ::= TEXTUAL-CONVENTION
    STATUS      current
    DESCRIPTION
        "Each octet within this value specifies a set of eight
        ports, with the first octet specifying ports 1 through
        8, the second octet specifying ports 9 through 16, etc.
        Within each octet, the most significant bit represents
        the lowest numbered port, and the least significant bit
        represents the highest numbered port.  Thus, each port
        of the bridge is represented by a single bit within the
        value of this object.  If that bit has a value of '1',
        then that port is included in the set of ports; the port
        is not included if its bit has a value of '0'."
    SYNTAX      OCTET STRING
"""
"""
PORT VLAN INFO:
We READ the untagged vlan on a port from QBRIDGE_VLAN_IFACE_UNTAGGED_PVID
We READ bitmap port-on-vlan info from this read-only oid:
    dot1qVlanCurrentEgressPorts / QBRIDGE_VLAN_CURRENT_EGRESS_PORTS

We WRITE changes to the port-on-vlan bitmap to
    dot1qVlanStaticEgressPorts / QBRIDGE_VLAN_STATIC_EGRESS_PORTS

"""


# The set of ports that are transmitting traffic for this VLAN
# as either tagged or untagged frames.
# dot1qVlanCurrentEgressPorts - this is READ-ONLY !!!
QBRIDGE_VLAN_CURRENT_EGRESS_PORTS = '.1.3.6.1.2.1.17.7.1.4.2.1.4'     # followed by <time_index>.<vlanId>
snmp_mib_variables['dot1qVlanCurrentEgressPorts'] = QBRIDGE_VLAN_CURRENT_EGRESS_PORTS

# The set of ports that are transmitting traffic for this VLAN as untagged frames.
# dot1qVlanCurrentUntaggedPorts - READ-ONLY !!!
QBRIDGE_VLAN_CURRENT_UNTAGGED_PORTS = '.1.3.6.1.2.1.17.7.1.4.2.1.5'     # followed by <someIndex>.<vlanId>
snmp_mib_variables['dot1qVlanCurrentUntaggedPorts'] = QBRIDGE_VLAN_CURRENT_UNTAGGED_PORTS

# The vlan status, ie static, dynamic, etc.
# dot1qVlanStatus - READ-ONLY !!!
dot1qVlanStatus = '.1.3.6.1.2.1.17.7.1.4.2.1.6'             # followed by <someIndex>.<vlanId>
snmp_mib_variables['dot1qVlanStatus'] = dot1qVlanStatus

VLAN_STATUS_OTHER = 1
VLAN_STATUS_PERMANENT = 2
VLAN_STATUS_DYNAMIC = 3

CISCO_VLAN_TYPE_NORMAL = 1    # regular(1) in the Cisco VTP mib

QBRIDGE_VLAN_CURRENT_VLAN_CREATION_TIME = '.1.3.6.1.2.1.17.7.1.4.2.1.7'              # followed by <someIndex>.<vlanId>
snmp_mib_variables['dot1qVlanCreationTime'] = QBRIDGE_VLAN_CURRENT_VLAN_CREATION_TIME


###################################################################
#
# dot1qVlanStaticTable = 1.3.6.1.2.1.17.7.1.4.3
#
QBRIDGE_VLAN_STATIC_ENTRY = '.1.3.6.1.2.1.17.7.1.4.3.1'
snmp_mib_variables['dot1qVlanStaticTable'] = QBRIDGE_VLAN_STATIC_ENTRY

# Entries under dot1qVlanStaticTable.dot1qVlanStaticEntry  1.3.6.1.2.1.17.7.1.4.3.1
# This is dot1qVlanStaticName
# To get vlan names
# dot1qVlanStaticName = 1.3.6.1.2.1.17.7.1.4.3.1.1
QBRIDGE_VLAN_STATIC_NAME = '.1.3.6.1.2.1.17.7.1.4.3.1.1'
snmp_mib_variables['dot1qVlanStaticName'] = QBRIDGE_VLAN_STATIC_NAME

# VLAN set:
# set .1.3.6.1.2.1.17.7.1.4.3.1.2 for tagged ports and .1.3.6.1.2.1.17.7.1.4.3.1.4 for untagged.
# dot1qPvid.<port>
# dot1qVlanStaticEgressPorts.<vlanId>
# dot1qVlanStaticUntaggedPorts.<vlanId>

# VLAN_EGRESS_PORTS = QBRIDGENODES['dot1qVlanStaticEgressPorts']['oid']
# To WRITE!!! egress ports of a VLAN (tagged + untagged)
# dot1qVlanStaticEgressPorts - READ-WRITE !!!
# The set of ports that are permanently assigned to the egress list for this VLAN by management.
# this is what you change when you SET a new vlan on a port (based on the bitmap)
QBRIDGE_VLAN_STATIC_EGRESS_PORTS = '.1.3.6.1.2.1.17.7.1.4.3.1.2'    # followed by vlanId
snmp_mib_variables['dot1qVlanStaticEgressPorts'] = QBRIDGE_VLAN_STATIC_EGRESS_PORTS

# To get untagged ports of a VLAN, returns bitmap
# dot1qVlanStaticUntaggedPorts = 1.3.6.1.2.1.17.7.1.4.3.1.4
QBRIDGE_VLAN_STATIC_UNTAGGED_PORTS = '.1.3.6.1.2.1.17.7.1.4.3.1.4'          # followed by vlanId
snmp_mib_variables['dot1qVlanStaticUntaggedPorts'] = QBRIDGE_VLAN_STATIC_UNTAGGED_PORTS

# List of all available vlans on this switch as by the command "show vlans"
# VLAN_ROW_STATUS = QBRIDGENODES['dot1qVlanStaticRowStatus']['oid']
QBRIDGE_VLAN_STATIC_ROW_STATUS = '.1.3.6.1.2.1.17.7.1.4.3.1.5'           # followed by vlanId
snmp_mib_variables['dot1qVlanStaticRowStatus'] = QBRIDGE_VLAN_STATIC_ROW_STATUS

#####################################################

# Per Port VLAN data, dot1qPortVlanEntry
QBRIDGE_PORT_VLAN_ENTRY = '.1.3.6.1.2.1.17.7.1.4.5.1'
snmp_mib_variables['dot1qPortVlanEntry'] = QBRIDGE_PORT_VLAN_ENTRY

# The VLAN ID assigned to untagged frames,
# To get ports (and their respective vlans) / to untag port in a vlan
# dot1qPvid = 1.3.6.1.2.1.17.7.1.4.5.1.1
# indexed by dot1dBasePort, so we need to lookup in the table from
# dot1dBasePortIfIndex  or BRIDGE_PORT_TO_INDEX_MAP above !!!
QBRIDGE_PORT_VLAN_PVID = '.1.3.6.1.2.1.17.7.1.4.5.1.1'
snmp_mib_variables['dot1qPvid'] = QBRIDGE_PORT_VLAN_PVID


# GVRP port status related:
dot1qPortGvrpStatus = '.1.3.6.1.2.1.17.7.1.4.5.1.4'
snmp_mib_variables['dot1qPortGvrpStatus'] = dot1qPortGvrpStatus

# vlan status: defined above!

########################################################################
#
# ifMIB, extensions for higher speed, etc.
IFMIB_MIB = '.1.3.6.1.2.1.31'
snmp_mib_variables['ifMIB'] = IFMIB_MIB

#
# interface name
IFMIB_NAME = '.1.3.6.1.2.1.31.1.1.1.1'
snmp_mib_variables['ifName'] = IFMIB_NAME

# high speed, in units of 1 Mbps
IFMIB_HIGHSPEED = '.1.3.6.1.2.1.31.1.1.1.15'
snmp_mib_variables['ifHighSpeed'] = IFMIB_HIGHSPEED

IFMIB_CONNECTOR = '.1.3.6.1.2.1.31.1.1.1.17'   # if SNMP_TRUE, then Physical port, otherwize virtual
snmp_mib_variables['ifConnectorPresent'] = IFMIB_CONNECTOR

# alias, i.e. interface Descriptions
IFMIB_ALIAS = '.1.3.6.1.2.1.31.1.1.1.18'  # From IF-MIB
snmp_mib_variables['ifAlias'] = IFMIB_ALIAS

# interface stack, ie brdige aggregation, etc.
IFMIB_STACK_MIB = '.1.3.6.1.2.1.31.1.2.1'
snmp_mib_variables['ifStackEntry'] = IFMIB_STACK_MIB

IFMIB_STACK_HIGHER_LAYER = '.1.3.6.1.2.1.31.1.2.1.1'    # ifStackHigherLayer
snmp_mib_variables['ifStackHigherLayer'] = IFMIB_STACK_HIGHER_LAYER

IFMIB_STACK_LOWER_LAYER = '.1.3.6.1.2.1.31.1.2.1.2'    # ifStackLowerLayer
snmp_mib_variables['ifStackLowerLayer'] = IFMIB_STACK_LOWER_LAYER

IFMIB_STACK_STATUS = '.1.3.6.1.2.1.31.1.2.1.3'    # ifStackStatus
snmp_mib_variables['ifStackStatus'] = IFMIB_STACK_STATUS

# To get forbidden ports
# dot1qVlanForbiddenEgressPorts = 1.3.6.1.2.1.17.7.1.4.3.1.3</value>

# This object indicates the status of a vlan
# dot1qVlanStaticRowStatus = 1.3.6.1.2.1.17.7.1.4.3.1.5

#
# ENTITY MIB
#
"""
1.3.6.1.2.1.47.1.1.1.1.1 (entPhysicalIndex)
1.3.6.1.2.1.47.1.1.1.1.2 (entPhysicalDescr)
1.3.6.1.2.1.47.1.1.1.1.3 (entPhysicalVendorType)
1.3.6.1.2.1.47.1.1.1.1.4 (entPhysicalContainedIn)
1.3.6.1.2.1.47.1.1.1.1.6 (entPhysicalParentRelPos)
1.3.6.1.2.1.47.1.1.1.1.7 (entPhysicalName)
1.3.6.1.2.1.47.1.1.1.1.8 (entPhysicalHardwareRev)
1.3.6.1.2.1.47.1.1.1.1.9 (entPhysicalFirmwareRev)
1.3.6.1.2.1.47.1.1.1.1.10 (entPhysicalSoftwareRev)
1.3.6.1.2.1.47.1.1.1.1.11 (entPhysicalSerialNum)
1.3.6.1.2.1.47.1.1.1.1.12 (entPhysicalMfgName)
1.3.6.1.2.1.47.1.1.1.1.13 (entPhysicalModelName)
1.3.6.1.2.1.47.1.1.1.1.14 (entPhysicalAlias)
1.3.6.1.2.1.47.1.1.1.1.15 (entPhysicalAssetID)
1.3.6.1.2.1.47.1.1.1.1.16 (entPhysicalIsFRU)
1.3.6.1.2.1.47.1.1.1.1.17 (entPhysicalMfgDate)
1.3.6.1.2.1.47.1.1.1.1.18 (entPhysicalUris)
"""
entPhysicalIndex = '.1.3.6.1.2.1.47.1.1.1.1'
snmp_mib_variables['entPhysicalIndex'] = entPhysicalIndex

entPhysicalSerialNum = '.1.3.6.1.2.1.47.1.1.1.1.11'
snmp_mib_variables['entPhysicalSerialNum'] = entPhysicalSerialNum

entPhysicalSoftwareRev = '.1.3.6.1.2.1.47.1.1.1.1.10'    # entPhysicalSoftwareRev
snmp_mib_variables['entPhysicalSoftwareRev'] = entPhysicalSoftwareRev

entPhysicalModelName = '.1.3.6.1.2.1.47.1.1.1.1.13'    # entPhysicalModelName
snmp_mib_variables['entPhysicalModelName'] = entPhysicalModelName

entPhysicalClass = '.1.3.6.1.2.1.47.1.1.1.1.5'     # entPhysicalClass
snmp_mib_variables['entPhysicalClass'] = entPhysicalClass
"""
 other(1),
       unknown(2),
       chassis(3),
       backplane(4),
       container(5),     -- e.g., chassis slot or daughter-card holder
       powerSupply(6),
       fan(7),
       sensor(8),
       module(9),        -- e.g., plug-in card or daughter-card
       port(10),
       stack(11),        -- e.g., stack of multiple chassis entities
       cpu(12)
"""
ENTITY_CLASS_CHASSIS = 3    # chassis(3) - the physical device, eg the 1U switch in a stack
ENTITY_CLASS_MODULE = 9     # module(9) - a module or blade in a chassis
ENTITY_CLASS_STACK = 11     # stack(11)
ENTITY_CLASS_NAME = {}
ENTITY_CLASS_NAME[ENTITY_CLASS_CHASSIS] = 'Chassis'
ENTITY_CLASS_NAME[ENTITY_CLASS_MODULE] = 'Module'
ENTITY_CLASS_NAME[ENTITY_CLASS_STACK] = 'Stack'

#
# POE RELATED
#
# ALL of these are followed by devId.ifIndex, where devId is stack member
POE_MIB = '.1.3.6.1.2.1.105'
snmp_mib_variables['powerEthernetMIB'] = POE_MIB

#
# the pethMainPseEntry table entries with device-level PoE info
#
POE_PSE_ENTRY = '.1.3.6.1.2.1.105.1.3.1.1'
snmp_mib_variables['pethMainPseEntry'] = POE_PSE_ENTRY

POE_PSE_MAXPOWER = '.1.3.6.1.2.1.105.1.3.1.1.2'     # followed by devId.index, where devId is stack member
snmp_mib_variables['pethMainPsePower'] = POE_PSE_MAXPOWER

POE_PSE_OPERSTATUS = '.1.3.6.1.2.1.105.1.3.1.1.3'     # followed by devId.index, where devId is stack member
snmp_mib_variables['pethMainPseOperStatus'] = POE_PSE_OPERSTATUS

POE_PSE_STATUS_ON = 1
POE_PSE_STATUS_OFF = 2
POE_PSE_STATUS_FAULT = 3

POE_PSE_POWER_USED = '.1.3.6.1.2.1.105.1.3.1.1.4'     # followed by devId.index, where devId is stack member
snmp_mib_variables['pethMainPseConsumptionPower'] = POE_PSE_POWER_USED

POE_PSE_THRESHOLD = '.1.3.6.1.2.1.105.1.3.1.1.5'     # followed by devId.index, where devId is stack member
snmp_mib_variables['pethMainPseUsageThreshold'] = POE_PSE_THRESHOLD

#
# the pethPsePortEntry tables with port-level PoE info
#
POE_PORT_ENTRY = '.1.3.6.1.2.1.105.1.1.1'
snmp_mib_variables['pethPsePortEntry'] = POE_PORT_ENTRY

POE_PORT_ADMINSTATUS = '.1.3.6.1.2.1.105.1.1.1.3'      # followed by devId.ifIndex, where devId is stack member
snmp_mib_variables['pethPsePortAdminEnable'] = POE_PORT_ADMINSTATUS
POE_PORT_ADMIN_ENABLED = 1
POE_PORT_ADMIN_DISABLED = 2

POE_PORT_DETECTSTATUS = '.1.3.6.1.2.1.105.1.1.1.6'      # followed by devId.ifIndex, where devId is stack member
snmp_mib_variables['pethPsePortDetectionStatus'] = POE_PORT_DETECTSTATUS
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

POE_PORT_PRIORITY = '.1.3.6.1.2.1.105.1.1.1.7'     # followed by devId.ifIndex, where devId is stack member
snmp_mib_variables['pethPsePortPowerPriority'] = POE_PORT_PRIORITY
POE_PORT_PRIORITY_CRITICAL = 1   # '1' = Critical
POE_PORT_PRIORITY_HIGH = 2       # '2' = High
POE_PORT_PRIORITY_LOW = 3        # '3' = Low

POE_PORT_DESCR = '.1.3.6.1.2.1.105.1.1.1.9'     # followed by devId.ifIndex, where devId is stack member
snmp_mib_variables['pethPsePortType'] = POE_PORT_DESCR


# IEEE also has a Dot1Q MIB:
# see also https://mibs.observium.org/mib/IEEE8021-Q-BRIDGE-MIB/
ieee8021QBridgeMib = '.1.3.111.2.802.1.1.4'

ieee8021QBridgeMvrpEnabledStatus = '.1.3.111.2.802.1.1.4.1.1.1.1.6'
snmp_mib_variables['ieee8021QBridgeMvrpEnabledStatus'] = ieee8021QBridgeMvrpEnabledStatus

#
# LLDP related#
#
# local port:
# (lldpLocPortEntry)
LLDP_MIB = '.1.0.8802.1.1.2.1'    # start of lldpObjects
snmp_mib_variables['lldpObjects'] = LLDP_MIB

# local system data at  .1.0.8802.1.1.2.1.3
# lldpLocSysCapSupported, local capabilities supported, see bitmap below
LLDP_LOCAL_CAP = '.1.0.8802.1.1.2.1.3.5.0'
snmp_mib_variables['lldpLocSysCapSupported'] = LLDP_LOCAL_CAP

# lldpLocSysCapEnabled, local capabilities enabled, see bitmap below
LLDP_LOCAL_CAP_EN = '.1.0.8802.1.1.2.1.3.6.0'
snmp_mib_variables['lldpLocSysCapEnabled'] = LLDP_LOCAL_CAP_EN

# lldpLocPortTable
LLDP_LOCAL_PORT_ENTRY = '.1.0.8802.1.1.2.1.3.7'
snmp_mib_variables['lldpLocPortTable'] = LLDP_LOCAL_PORT_ENTRY

# remote system data at .1.0.8802.1.1.2.1.4
# lldpRemEntry
LLDP_REMOTE_ENTRIES = '.1.0.8802.1.1.2.1.4.1.1'
snmp_mib_variables['lldpRemEntry'] = LLDP_REMOTE_ENTRIES

# LLDP_REM_TIMEMARK =       '.1.0.8802.1.1.2.1.4.1.1.1'  # NOT USED
# this does not appear to be implemented in most gear.
# This would mean that the interface ID is based on Dot1Q port map, or IFMIB-ifIndex
LLDP_REMOTE_LOCAL_PORT = '.1.0.8802.1.1.2.1.4.1.1.2'
snmp_mib_variables['lldpRemLocalPortNum'] = '.1.0.8802.1.1.2.1.4.1.1.2'

# the following are indexed by  <remote-device-random-id>.<port-id>.1
LLDP_REMOTE_INDEX = '.1.0.8802.1.1.2.1.4.1.1.3'
snmp_mib_variables['lldpRemIndex'] = LLDP_REMOTE_INDEX

LLDP_REMOTE_CHASSIS_TYPE = '.1.0.8802.1.1.2.1.4.1.1.4'
snmp_mib_variables['lldpRemChassisIdSubtype'] = LLDP_REMOTE_CHASSIS_TYPE
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

LLDP_REMOTE_CHASSIS_ID = '.1.0.8802.1.1.2.1.4.1.1.5'
snmp_mib_variables['lldpRemChassisId'] = LLDP_REMOTE_CHASSIS_ID

LLDP_REMOTE_PORT_ID = '.1.0.8802.1.1.2.1.4.1.1.7'
snmp_mib_variables['lldpRemPortId'] = LLDP_REMOTE_PORT_ID

LLDP_REMOTE_PORT_DESCR = '.1.0.8802.1.1.2.1.4.1.1.8'
snmp_mib_variables['lldpRemPortDesc'] = LLDP_REMOTE_PORT_DESCR

LLDP_REMOTE_SYS_NAME = '.1.0.8802.1.1.2.1.4.1.1.9'
snmp_mib_variables['lldpRemSysName'] = LLDP_REMOTE_SYS_NAME

LLDP_REMOTE_SYS_DESCR = '.1.0.8802.1.1.2.1.4.1.1.10'
snmp_mib_variables['lldpRemSysDesc'] = LLDP_REMOTE_SYS_DESCR

# capabilities, see entry for "LldpSystemCapabilitiesMap" at
# http://www.ieee802.org/1/files/public/MIBs/LLDP-MIB-200505060000Z.txt
LLDP_REMOTE_SYS_CAP = '.1.0.8802.1.1.2.1.4.1.1.11'   # lldpRemSysCapSupported bitmap!
snmp_mib_variables['lldpRemSysCapSupported'] = LLDP_REMOTE_SYS_CAP

LLDP_REMOTE_SYS_CAP_EN = '.1.0.8802.1.1.2.1.4.1.1.12'   # lldpRemSysCapEnabled bitmap!
snmp_mib_variables['lldpRemSysCapEnabled'] = LLDP_REMOTE_SYS_CAP_EN

# Capabilities bits. Note this is IN NETWORK ORDER, ie low order bit first!!!
LLDP_CAPA_BITS_OTHER = 0x80     # other(0),
LLDP_CAPA_BITS_REPEATER = 0x40  # repeater(1),
LLDP_CAPA_BITS_BRIDGE = 0x20    # bridge(2),
LLDP_CAPA_BITS_WLAN = 0x10      # wlanAccessPoint(3),
LLDP_CAPA_BITS_ROUTER = 0x08    # router(4),
LLDP_CAPA_BITS_PHONE = 0x04     # telephone(5)
LLDP_CAPA_BITS_DOCSIS = 0x02    # docsisCableDevice(6),
LLDP_CAPA_BITS_STATION = 0x01   # stationOnly(7)


#
# LACP MIB
#
# see also
# http://cric.grenoble.cnrs.fr/Administrateurs/Outils/MIBS/?oid=1.2.840.10006.300.43.1.2.1.1
# https://stackoverflow.com/questions/14960157/how-to-map-portchannel-to-interfaces-via-snmp
#

# all info about LACP ports
LACP_PORT_ENTRY = '.1.2.840.10006.300.43.1.2.1.1'
snmp_mib_variables['dot3adAggPortEntry'] = LACP_PORT_ENTRY

# specifically, what interfaces are members, i.e.:
# LACP_PORT_SELECTED_AGG_ID.<member interface ifIndex> = <lacp virtual interface ifIndex>
LACP_PORT_SELECTED_AGG_ID = '.1.2.840.10006.300.43.1.2.1.1.12'
snmp_mib_variables['dot3adAggPortSelectedAggID'] = LACP_PORT_SELECTED_AGG_ID

# The identifier value of the Aggregator that this Aggregation Port is currently attached to.
# Zero indicates that the Aggregation Port is not currently attached to an Aggregator. This value is read-only.
# LACP_PORT_ATTACHED_AGG_ID.<member interface ifIndex> = <lacp virtual interface ifIndex>
LACP_PORT_ATTACHED_AGG_ID = '.1.2.840.10006.300.43.1.2.1.1.13'
snmp_mib_variables['dot3adAggPortAttachedAggID'] = LACP_PORT_ATTACHED_AGG_ID



#
# VENDOR SPECIFIC Entries, see also vendors/vendors.py
#

# System Object ID: Vendor ID is the first number after this:
ENTERPRISE_ID_BASE = '.1.3.6.1.4.1'
snmp_mib_variables['enterprises'] = ENTERPRISE_ID_BASE
