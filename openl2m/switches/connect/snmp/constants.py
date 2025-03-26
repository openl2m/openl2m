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

# here we defined mappings from SNMP Enterprise Id to Company Name
# specific entries for supported vendors are in their implementation
# directories, eg. vendors/procurve/constants.py, vendors/cisco/constants.py...
#
ENTERPRISE_ID_D_LINK = 171
ENTERPRISE_ID_ALLIED_TELESIS = 207
ENTERPRISE_ID_INTEL = 343
ENTERPRISE_ID_EXTREME = 1916
ENTERPRISE_ID_ASUSTEK = 2623
ENTERPRISE_ID_LINKSYS = 3955
ENTERPRISE_ID_BROADCOM = 4413
ENTERPRISE_ID_NETGEAR = 4526
ENTERPRISE_ID_EXTREME2 = 6307
ENTERPRISE_ID_UBIQUITY = 7377
# generic Net-SNMP installed snmpd
ENTERPRISE_ID_NETSNMP = 8072
ENTERPRISE_ID_TP_LINK = 11863
ENTERPRISE_ID_FORTINET = 12356
ENTERPRISE_ID_MIKROTIK = 14988
# a test cheap test switch used
ENTERPRISE_ID_PLANET = 10456
ENTERPRISE_ID_TRENDNET = 28866

enterprise_id_info = {}
enterprise_id_info[ENTERPRISE_ID_D_LINK] = 'D-Link'
enterprise_id_info[ENTERPRISE_ID_ALLIED_TELESIS] = 'Allied Telesis'
enterprise_id_info[ENTERPRISE_ID_INTEL] = 'Intel Corp.'
enterprise_id_info[ENTERPRISE_ID_EXTREME] = 'Extreme'
enterprise_id_info[ENTERPRISE_ID_ASUSTEK] = 'ASUSTek'
enterprise_id_info[ENTERPRISE_ID_LINKSYS] = 'Linksys'
enterprise_id_info[ENTERPRISE_ID_BROADCOM] = 'Broadcom'
enterprise_id_info[ENTERPRISE_ID_NETGEAR] = 'Netgear'
enterprise_id_info[ENTERPRISE_ID_EXTREME2] = 'Extreme(Ipanema)'
enterprise_id_info[ENTERPRISE_ID_UBIQUITY] = 'Ubiquity'
enterprise_id_info[ENTERPRISE_ID_NETSNMP] = 'Generic Net-SNMP'
enterprise_id_info[ENTERPRISE_ID_TP_LINK] = 'TP-Link'
enterprise_id_info[ENTERPRISE_ID_FORTINET] = 'Fortinet'
enterprise_id_info[ENTERPRISE_ID_MIKROTIK] = 'Mikrotik'
enterprise_id_info[ENTERPRISE_ID_PLANET] = 'PLANET Technology Corp.'
enterprise_id_info[ENTERPRISE_ID_TRENDNET] = 'TRENDnet'

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
system = '.1.3.6.1.2.1.1'
snmp_mib_variables['system'] = system

sysDescr = '.1.3.6.1.2.1.1.1.0'
snmp_mib_variables['sysDescr'] = sysDescr

sysObjectID = '.1.3.6.1.2.1.1.2.0'
snmp_mib_variables['sysObjectID'] = sysObjectID

sysUpTime = '.1.3.6.1.2.1.1.3.0'
snmp_mib_variables['sysUpTime'] = sysUpTime

sysContact = '.1.3.6.1.2.1.1.4.0'
snmp_mib_variables['sysContact'] = sysContact

sysName = '.1.3.6.1.2.1.1.5.0'
snmp_mib_variables['sysName'] = sysName

sysLocation = '.1.3.6.1.2.1.1.6.0'
snmp_mib_variables['sysLocation'] = sysLocation

snmp_mib_variables['sysServices'] = '.1.3.6.1.2.1.1.7.0'

#
# INTERFACE RELATED
#
ifNumber = '.1.3.6.1.2.1.2.1.0'  # interface count on device
snmp_mib_variables['ifNumber'] = ifNumber

#
# OLD "Interfaces" part of MIB-2, for HighSpeed, see ifMIB extensions at .31
ifTable = '.1.3.6.1.2.1.2.2.1'  # see also: https://www.alvestrand.no/objectid/1.3.6.1.2.1.2.2.1.html
snmp_mib_variables['ifTable'] = ifTable

ifIndex = '.1.3.6.1.2.1.2.2.1.1'  # https://www.alvestrand.no/objectid/1.3.6.1.2.1.2.2.1.1.html
snmp_mib_variables['ifIndex'] = ifIndex

ifDescr = '.1.3.6.1.2.1.2.2.1.2'  # the OLD interface name, see ifName below
snmp_mib_variables['ifDescr'] = ifDescr

ifType = '.1.3.6.1.2.1.2.2.1.3'
snmp_mib_variables['ifType'] = ifType

ifMtu = '.1.3.6.1.2.1.2.2.1.4'
snmp_mib_variables['ifMtu'] = ifMtu

ifSpeed = '.1.3.6.1.2.1.2.2.1.5'
snmp_mib_variables['ifSpeed'] = ifSpeed

ifPhysAddress = '.1.3.6.1.2.1.2.2.1.6'
snmp_mib_variables['ifPhysAddress'] = ifPhysAddress

ifAdminStatus = '.1.3.6.1.2.1.2.2.1.7'
snmp_mib_variables['ifAdminStatus'] = ifAdminStatus

IF_ADMIN_STATUS_UP = 1
IF_ADMIN_STATUS_DOWN = 2

ifOperStatus = '.1.3.6.1.2.1.2.2.1.8'
snmp_mib_variables['ifOperStatus'] = ifOperStatus

IF_OPER_STATUS_UP = 1
IF_OPER_STATUS_DOWN = 2

"""
Currently not used, best served from a Network Management application:

ifLastChange = '.1.3.6.1.2.1.2.2.1.9'
snmp_mib_variables['ifLastChange'] =  ifLastChange

ifInOctets = '.1.3.6.1.2.1.2.2.1.10'
snmp_mib_variables['ifInOctets'] = ifInOctets

ifInUcastPkts = '.1.3.6.1.2.1.2.2.1.11'
snmp_mib_variables['ifInUcastPkts'] = ifInUcastPkts

ifInNUcastPkts = '.1.3.6.1.2.1.2.2.1.12'
snmp_mib_variables['ifInNUcastPkts'] = ifInNUcastPkts

ifInDiscards = '.1.3.6.1.2.1.2.2.1.13'
snmp_mib_variables['ifInDiscards'] = ifInDiscards

ifInErrors = '.1.3.6.1.2.1.2.2.1.14'
snmp_mib_variables['ifInErrors'] = ifInErrors

ifInUnknownProtos = '.1.3.6.1.2.1.2.2.1.15'
snmp_mib_variables['ifInUnknownProtos'] = ifInUnknownProtos

ifOutOctets = '.1.3.6.1.2.1.2.2.1.16'
snmp_mib_variables['ifOutOctets'] = ifOutOctets

ifOutUcastPkts = '.1.3.6.1.2.1.2.2.1.17'
snmp_mib_variables['ifOutUcastPkts'] = ifOutUcastPkts

ifOutNUcastPkts = '.1.3.6.1.2.1.2.2.1.18'
snmp_mib_variables['ifOutNUcastPkts'] = ifOutNUcastPkts

ifOutDiscards = '.1.3.6.1.2.1.2.2.1.19'
snmp_mib_variables['ifOutDiscards'] = ifOutDiscards

ifOutErrors = '.1.3.6.1.2.1.2.2.1.20'
snmp_mib_variables['ifOutErrors'] = ifOutErrors

#not sure we care about these:
ifOutQLen = '.1.3.6.1.2.1.2.2.1.19'
snmp_mib_variables['ifOutQLen'] = ifOutQLen

ifSpecific = '.1.3.6.1.2.1.2.2.1.20'
snmp_mib_variables['ifSpecific'] =  ifSpecific
"""

##############################################
# IP-MIB contains various IP address entries #
# see https://mibs.observium.org/mib/IP-MIB  #
#                                            #
# ip = ".1.3.6.1.2.1.4"                      #
##############################################

#
# the IP address(es) of the switch
#
ipAddrTable = '.1.3.6.1.2.1.4.20'
snmp_mib_variables['ipAddrTable'] = ipAddrTable

# and the sub-entities:
ipAdEntAddr = '.1.3.6.1.2.1.4.20.1.1'
snmp_mib_variables['ipAdEntAddr'] = ipAdEntAddr

ipAdEntIfIndex = '.1.3.6.1.2.1.4.20.1.2'
snmp_mib_variables['ipAdEntIfIndex'] = ipAdEntIfIndex

ipAdEntNetMask = '.1.3.6.1.2.1.4.20.1.3'
snmp_mib_variables['ipAdEntNetMask'] = ipAdEntNetMask

#
# ARP Table related, using the modern Entries#
#
# the older ipNetToMedia tables:
ipNetToMediaTable = '.1.3.6.1.2.1.4.22'
snmp_mib_variables['ipNetToMediaTable'] = ipNetToMediaTable

ipNetToMediaIfIndex = '.1.3.6.1.2.1.4.22.1.1'
snmp_mib_variables['ipNetToMediaIfIndex'] = ipNetToMediaIfIndex

ipNetToMediaPhysAddress = '.1.3.6.1.2.1.4.22.1.2'
snmp_mib_variables['ipNetToMediaPhysAddress'] = ipNetToMediaPhysAddress

# ipNetToMediaNetAddress is the 'arp' table,
ipNetToMediaNetAddress = '.1.3.6.1.2.1.4.22.1.3'
snmp_mib_variables['ipNetToMediaNetAddress'] = ipNetToMediaNetAddress

#
# IP-MIB IPv6 interface info
#
# ipv6InterfaceTable = ".1.3.6.1.2.1.4.30"
# ipv6InterfaceEntry = ".1.3.6.1.2.1.4.30.1"
# snmp_mib_variables['ipv6InterfaceEntry'] = ipv6InterfaceEntry

# ipv6InterfaceIfIndex = ".1.3.6.1.2.1.4.30.1.1"
# snmp_mib_variables['ipv6InterfaceIfIndex'] = ipv6InterfaceIfIndex

# ipv6InterfaceReasmMaxSize 	octets	.1.3.6.1.2.1.4.30.1.2

# this is the interface IPv6 address:
ipv6InterfaceIdentifier = ".1.3.6.1.2.1.4.30.1.3"
snmp_mib_variables['ipv6InterfaceIdentifier'] = ipv6InterfaceIdentifier

#
# the newer ipAddressTable, from the IP-MIB:
# https://www.rfc-editor.org/rfc/rfc4293
# https://cric.grenoble.cnrs.fr/Administrateurs/Outils/MIBS/?oid=1.3.6.1.2.1.4.34
#
ipAddressTable = '.1.3.6.1.2.1.4.34'
ipAddressEntry = '.1.3.6.1.2.1.4.34.1'
# and the entries is this table are index via <address-type>.<length>.<ip-address> = <field value>
# see the INDEX definition, not that ipAddressAddr = <length>.<ip-address>
# ipAddressEntry OBJECT-TYPE
#     SYNTAX     IpAddressEntry
#     MAX-ACCESS not-accessible
#     STATUS     current
#     DESCRIPTION
#            "An address mapping for a particular interface."
#     INDEX { ipAddressAddrType, ipAddressAddr }
#     ::= { ipAddressTable 1 }


# The address type of ipAddressAddr.
ipAddressType = '.1.3.6.1.2.1.4.34.1.1'
# value is InetAddressType, defined in INET-ADDRESS-MIB
# ipv4(1)     An IPv4 address as defined by the InetAddressIPv4 textual convention.
# ipv6(2)     An IPv6 address as defined by the InetAddressIPv6 textual convention.
# we define these as IANA_TYPE_IPV4 and IANA_TYPE_IPV6, see switches.connect.constants.py

# The IP address to which this entry's addressing information pertains.
ipAddressAddr = '.1.3.6.1.2.1.4.34.1.2'

# this is what we want: the ip address for an interface:
# The index value that uniquely identifies the interface to which this entry is applicable.
ipAddressIfIndex = '.1.3.6.1.2.1.4.34.1.3'
snmp_mib_variables['ipAddressIfIndex'] = ipAddressIfIndex
# this is ipAddressIfIndex.<address-type>.<length>.<ip-address> = <if-index>
# eg: .1.3.6.1.2.1.4.34.1.3.1.4.10.96.2.33 = INTEGER: 16777716
# ipv4 (1) address, length 4, ip=10.96.2.33 is on if-index 16777716

# The type of address. broadcast(3) is not a valid value for IPv6 addresses (RFC 3513).
ipAddressType = '.1.3.6.1.2.1.4.34.1.4'
# unicast(1),
# anycast(2),
# broadcast(3)
IP_ADDRESS_TYPE_UNICAST = 1
IP_ADDRESS_TYPE_ANYCAST = 2
IP_ADDRESS_TYPE_BROADCAST = 3

# A pointer to the row in the prefix table to which this address belongs. May be { 0 0 } if there is no such row.
# this contains bot the IP4/6 address, the ifIndex where it is from, and the PrefixLength!
ipAddressPrefix = '.1.3.6.1.2.1.4.34.1.5'
snmp_mib_variables['ipAddressPrefix'] = ipAddressPrefix
# this returns ipAddressPrefixOrigin.<ifIndex>.<add type>.<addr lenght>.<IP info in dotted decimal>.<prefix-length>
ipAddressPrefixOrigin = ".1.3.6.1.2.1.4.32.1.5"

# The origin of the address.
ipAddressOrigin = '.1.3.6.1.2.1.4.34.1.6'
# value is "IpAddressOriginTC": in IP-MIB defined as :
# SYNTAX     INTEGER {
#     other(1),
#     manual(2),
#     dhcp(4),
#     linklayer(5),
#     random(6)
# }

# other entries not used:
#
# # The status of the address, describing if the address can be used for communication.
# # In the absence of other information, an IPv4 …
# ipAddressStatus = '.1.3.6.1.2.1.4.34.1.7'

# # The value of sysUpTime at the time this entry was created.
# ipAddressCreated = '.1.3.6.1.2.1.4.34.1.8'

# # The value of sysUpTime at the time this entry was last updated.
# ipAddressLastChanged = '.1.3.6.1.2.1.4.34.1.9'

# # The status of this conceptual row.
# # The RowStatus TC requires that this DESCRIPTION clause states under which circumstances other …
# ipAddressRowStatus = '.1.3.6.1.2.1.4.34.1.10'

# # The storage type for this conceptual row.
# ipAddressStorageType = '.1.3.6.1.2.1.4.34.1.11'


#
# the newer ipNetToPhysical tables:
ipNetToPhysicalEntry = '.1.3.6.1.2.1.4.35.1'
snmp_mib_variables['ipNetToPhysicalEntry'] = ipNetToPhysicalEntry

# many do not implement the folowing 3:
ipNetToPhysicalIfIndex = '.1.3.6.1.2.1.4.35.1.1'
snmp_mib_variables['ipNetToPhysicalIfIndex'] = ipNetToPhysicalIfIndex

ipNetToPhysicalNetAddressType = '.1.3.6.1.2.1.4.35.1.2'
snmp_mib_variables['ipNetToPhysicalNetAddressType'] = ipNetToPhysicalNetAddressType

ipNetToPhysicalNetAddress = '.1.3.6.1.2.1.4.35.1.3'
snmp_mib_variables['ipNetToPhysicalNetAddress'] = ipNetToPhysicalNetAddress

# some start with this:
ipNetToPhysicalPhysAddress = '.1.3.6.1.2.1.4.35.1.4'
snmp_mib_variables['ipNetToPhysicalPhysAddress'] = ipNetToPhysicalPhysAddress
# from MIB:
#     INDEX       { ipNetToPhysicalIfIndex,
#                   ipNetToPhysicalNetAddressType,
#                   ipNetToPhysicalNetAddress }
# so the returned OID is
# ipNetToPhysicalPhysAddress.<if-index>.<address-type>.<length>."ip address in dotted format" = "mac address"

ipNetToPhysicalLastUpdated = '.1.3.6.1.2.1.4.35.1.5'

ipNetToPhysicalType = '.1.3.6.1.2.1.4.35.1.6'

ipNetToPhysicalState = '.1.3.6.1.2.1.4.35.1.7'

ipNetToPhysicalRowStatus = '.1.3.6.1.2.1.4.35.1.8'

#
# OLD, deprecated IPV6-MIB
# still used in some routers.
# see https://mibs.observium.org/mib/IPV6-MIB
#
# see also above IP-MIB older entries "ipv6InterfaceTable"
#
# ipv6MIB = ".1.3.6.1.2.1.55"
# ipv6MIBObjects  .1.3.6.1.2.1.55.1
# ipv6DefaultHopLimit .1.3.6.1.2.1.55.1.2
# ipv6Interfaces .1.3.6.1.2.1.55.1.3
# ipv6IfTableLastChange .1.3.6.1.2.1.55.1.4

# this sounds like it should have IPv6 interface info, but does not!
# ipv6IfTable .1.3.6.1.2.1.55.1.5

# ipv6IfStatsTable .1.3.6.1.2.1.55.1.6
# ipv6AddrPrefixTable .1.3.6.1.2.1.55.1.7

#
# this tables contain IPv6 info for device interfaces:
#
# ipv6AddrTable  .1.3.6.1.2.1.55.1.8
# ipv6AddrEntry  .1.3.6.1.2.1.55.1.8.1
# ipv6AddrAddress = ".1.3.6.1.2.1.55.1.8.1.1"

# this reads the IPv6 address, and the prefix length all in one:
ipv6AddrPfxLength = ".1.3.6.1.2.1.55.1.8.1.2"
snmp_mib_variables['ipv6AddrPfxLength'] = ipv6AddrPfxLength

# return value is .1.3.6.1.2.1.55.1.8.1.2.<ifIndex>.<ipv6 in 16 decimals> = <prefix-len>
# e.g.:
# .1.3.6.1.2.1.55.1.8.1.2.2153.38.32.1.5.240.18.0.0.0.0.0.0.0.0.0.17 = INTEGER: 128
# ifIndex 2153, 38 = 26h, 32 = 20h, etc. ==> 2620:0105:f012::11 / 128
# .1.3.6.1.2.1.55.1.8.1.2.2153.254.128.0.0.0.0.0.0.0.0.0.0.105.8.0.0 = INTEGER: 10  # Link-Local fe80::6908:0000/10

# ipv6AddrType  .1.3.6.1.2.1.55.1.8.1.3
# ipv6AddrAnycastFlag  .1.3.6.1.2.1.55.1.8.1.4
# ipv6AddrStatus  .1.3.6.1.2.1.55.1.8.1.5

# ipv6RouteNumber .1.3.6.1.2.1.55.1.9
# ipv6DiscardedRoutes .1.3.6.1.2.1.55.1.10
# ipv6RouteTable .1.3.6.1.2.1.55.1.11

# IPv6 "arp" aka Neighbor entries:
# ipv6NetToMediaTable = ".1.3.6.1.2.1.55.1.12"
ipv6NetToMediaEntry = ".1.3.6.1.2.1.55.1.12.1"
snmp_mib_variables['ipv6NetToMediaEntry'] = ipv6NetToMediaEntry


#
# from the IEEE802.3 stats mib:
#
# interface duplex status:
dot3StatsDuplexStatus = '.1.3.6.1.2.1.10.7.2.1.19'
snmp_mib_variables['dot3StatsDuplexStatus'] = dot3StatsDuplexStatus

#
# BRIDGE MIB RELATED
#
dot1dBridge = '.1.3.6.1.2.1.17'  # orignal Bridge-MIB, including Ethernet-to-Interface mappings
snmp_mib_variables['dot1dBridge'] = dot1dBridge

# dot1dBaseNumPorts is the number of bridge ports on the device
dot1dBaseNumPorts = '.1.3.6.1.2.1.17.1.2'
snmp_mib_variables['dot1dBaseNumPorts'] = dot1dBaseNumPorts


# dot1dBasePortIfIndex, this maps the switch port-id  to the ifIndex in MIB-II
dot1dBasePortIfIndex = '.1.3.6.1.2.1.17.1.4.1.2'
snmp_mib_variables['dot1dBasePortIfIndex'] = dot1dBasePortIfIndex

# Getting Ethernet addresses on ports:
# walk dot1dTpFdbAddress
dot1dTpFdbAddress = '.1.3.6.1.2.1.17.4.3.1.1'
snmp_mib_variables['dot1dTpFdbAddress'] = dot1dTpFdbAddress

# more useful is this, dot1dTpFdbPort. The 'sub-oid' values represent the ethernet address,
# return value is the 'port id', mapped below in
dot1dTpFdbPort = '.1.3.6.1.2.1.17.4.3.1.2'
snmp_mib_variables['dot1dTpFdbPort'] = dot1dTpFdbPort

dot1dTpFdbStatus = '.1.3.6.1.2.1.17.4.3.1.3'
snmp_mib_variables['dot1dTpFdbStatus'] = dot1dTpFdbStatus
FDB_STATUS_OTHER = 1
FDB_STATUS_INVALID = 2
FDB_STATUS_LEARNED = 3
FDB_STATUS_SELF = 4
FDB_STATUS_MGMT = 5

#
# VLAN Q-BRIDGE RELATED
#
qBridgeMIB = '.1.3.6.1.2.1.17.7'  # Expanded 802.1Q MIB, includes VLAN info, etc.
snmp_mib_variables['qBridgeMIB'] = qBridgeMIB

qBridgeMIBObjects = '.1.3.6.1.2.1.17.7.1'

#
# base settings about the 802.1q config:
#
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

#
# Transparant bridge (switch) forward tables
#
dot1qTp = '.1.3.6.1.2.1.17.7.1.2'

dot1qFdbTable = '.1.3.6.1.2.1.17.7.1.2.1'

dot1qTpFdbTable = '.1.3.6.1.2.1.17.7.1.2.2'
dot1qTpFdbEntry = '.1.3.6.1.2.1.17.7.1.2.2.1'

dot1qTpFdbAddress = '.1.3.6.1.2.1.17.7.1.2.2.1.1'  # A unicast MAC address for which the device has forwarding and/or filtering information.

# forwarding database information with mac address mapping to switch port id:
# dot1qTpFdbPort.<fdb-id>.<6 byte mac address> = port-id
dot1qTpFdbPort = '.1.3.6.1.2.1.17.7.1.2.2.1.2'
snmp_mib_variables['dot1qTpFdbPort'] = dot1qTpFdbPort
# similar, the status of the learned entry:
# dot1qTpFdbStatus.<fdb-id>.<6 byte mac address> = status
dot1qTpFdbStatus = '.1.3.6.1.2.1.17.7.1.2.2.1.3'
snmp_mib_variables['dot1qTpFdbStatus'] = dot1qTpFdbStatus
# see above at dot1dTpFdbStatus

##############################
# Current VLAN table entries #
##############################

dot1qVlanCurrentTable = '.1.3.6.1.2.1.17.7.1.4.2'
snmp_mib_variables['dot1qVlanCurrentTable'] = dot1qVlanCurrentTable

dot1qVlanCurrentEntry = '.1.3.6.1.2.1.17.7.1.4.2.1'
snmp_mib_variables['dot1qVlanCurrentEntry'] = dot1qVlanCurrentEntry

dot1qVlanTimeMark = '.1.3.6.1.2.1.17.7.1.4.2.1.1'  # A TimeFilter for this entry. See the TimeFilter textual convention to see how this works.
snmp_mib_variables['dot1qVlanTimeMark'] = dot1qVlanTimeMark

dot1qVlanIndex = '.1.3.6.1.2.1.17.7.1.4.2.1.2'  # The VLAN-ID or other identifier refering to this VLAN.
snmp_mib_variables['dot1qVlanIndex'] = dot1qVlanIndex

dot1qVlanFdbId = '.1.3.6.1.2.1.17.7.1.4.2.1.3'  # The Filtering Database used by this VLAN. This is one of the dot1qFdbId values in the dot1qFdbTable.
snmp_mib_variables['dot1qVlanFdbId'] = dot1qVlanFdbId

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

PORT VLAN INFO:

NOTE _ NOTE _ NOTE:
    The qBridge Current_* entries are READ-only

We READ the untagged vlan on a port from:
    dot1qPvid

We READ bitmap port-on-vlan info from this read-only oid:
    dot1qVlanCurrentEgressPorts

We WRITE changes to the port-on-vlan bitmap to
    dot1qVlanStaticEgressPorts
"""

# The set of ports that are transmitting traffic for this VLAN
# as either tagged or untagged frames.
# dot1qVlanCurrentEgressPorts - this is *** READ-ONLY !!! ***
dot1qVlanCurrentEgressPorts = '.1.3.6.1.2.1.17.7.1.4.2.1.4'  # followed by <time_index>.<vlanId>
snmp_mib_variables['dot1qVlanCurrentEgressPorts'] = dot1qVlanCurrentEgressPorts

# The set of ports that are transmitting traffic for this VLAN as untagged frames.
# dot1qVlanCurrentUntaggedPorts - READ-ONLY !!!
dot1qVlanCurrentUntaggedPorts = '.1.3.6.1.2.1.17.7.1.4.2.1.5'  # followed by <someIndex>.<vlanId>
snmp_mib_variables['dot1qVlanCurrentUntaggedPorts'] = dot1qVlanCurrentUntaggedPorts

# The vlan status, ie static, dynamic, etc.
# dot1qVlanStatus - READ-ONLY !!!
dot1qVlanStatus = '.1.3.6.1.2.1.17.7.1.4.2.1.6'  # followed by <someIndex>.<vlanId>
snmp_mib_variables['dot1qVlanStatus'] = dot1qVlanStatus

dot1qVlanCreationTime = '.1.3.6.1.2.1.17.7.1.4.2.1.7'  # followed by <someIndex>.<vlanId>
snmp_mib_variables['dot1qVlanCreationTime'] = dot1qVlanCreationTime


#############################
# Static VLAN table entries #
#############################

dot1qVlanStaticTable = '.1.3.6.1.2.1.17.7.1.4.3'

dot1qVlanStaticTableEntry = '.1.3.6.1.2.1.17.7.1.4.3.1'
snmp_mib_variables['dot1qVlanStaticTableEntry'] = dot1qVlanStaticTableEntry

# Entries under dot1qVlanStaticTable.dot1qVlanStaticEntry
# This is dot1qVlanStaticName, used to get vlan names
dot1qVlanStaticName = '.1.3.6.1.2.1.17.7.1.4.3.1.1'
snmp_mib_variables['dot1qVlanStaticName'] = dot1qVlanStaticName
VLAN_NAME_MAX_LEN = 32  # per Q-Bridge MIB object definition

# VLAN set:
# set .1.3.6.1.2.1.17.7.1.4.3.1.2 for tagged ports and .1.3.6.1.2.1.17.7.1.4.3.1.4 for untagged.
# dot1qPvid.<port>
# dot1qVlanStaticEgressPorts.<vlanId>
# dot1qVlanStaticUntaggedPorts.<vlanId>

# VLAN_EGRESS_PORTS = ['dot1qVlanStaticEgressPorts']['oid']
# To WRITE!!! egress ports of a VLAN (tagged + untagged)
# dot1qVlanStaticEgressPorts - READ-WRITE !!!
# The set of ports that are permanently assigned to the egress list for this VLAN by management.
# this is what you change when you SET a new vlan on a port (based on the bitmap)
dot1qVlanStaticEgressPorts = '.1.3.6.1.2.1.17.7.1.4.3.1.2'  # followed by vlanId
snmp_mib_variables['dot1qVlanStaticEgressPorts'] = dot1qVlanStaticEgressPorts

# To get untagged ports of a VLAN, returns bitmap
# dot1qVlanStaticUntaggedPorts = 1.3.6.1.2.1.17.7.1.4.3.1.4
dot1qVlanStaticUntaggedPorts = '.1.3.6.1.2.1.17.7.1.4.3.1.4'  # followed by vlanId
snmp_mib_variables['dot1qVlanStaticUntaggedPorts'] = dot1qVlanStaticUntaggedPorts

# List of all available vlans on this switch as by the command "show vlans"
# VLAN_ROW_STATUS = ['dot1qVlanStaticRowStatus']['oid']
dot1qVlanStaticRowStatus = '.1.3.6.1.2.1.17.7.1.4.3.1.5'  # followed by vlanId
snmp_mib_variables['dot1qVlanStaticRowStatus'] = dot1qVlanStaticRowStatus
vlan_createAndGo = 4
vlan_createAndWait = 5
vlan_destroy = 6

#####################################################

# Per Port VLAN data, dot1qPortVlanEntry
dot1qPortVlanEntry = '.1.3.6.1.2.1.17.7.1.4.5.1'
snmp_mib_variables['dot1qPortVlanEntry'] = dot1qPortVlanEntry

# The VLAN ID assigned to untagged frames,
# To get ports (and their respective vlans) / to untag port in a vlan
# dot1qPvid = 1.3.6.1.2.1.17.7.1.4.5.1.1
# indexed by dot1dBasePort, so we need to lookup in the table from
# dot1dBasePortIfIndex  or dot1dBasePortIfIndex above !!!
dot1qPvid = '.1.3.6.1.2.1.17.7.1.4.5.1.1'
snmp_mib_variables['dot1qPvid'] = dot1qPvid


# GVRP port status related:
dot1qPortGvrpStatus = '.1.3.6.1.2.1.17.7.1.4.5.1.4'
snmp_mib_variables['dot1qPortGvrpStatus'] = dot1qPortGvrpStatus

# vlan status: defined above!

########################################################################
#
# ifMIB, extensions for higher speed, etc.
ifMIB = '.1.3.6.1.2.1.31'
snmp_mib_variables['ifMIB'] = ifMIB

# ifXTable, the more modern interface information
# .1.3.6.1.2.1.31.1.1 (ifXTable)
# contains entries of
# 1.3.6.1.2.1.31.1.1.1 (ifXEntry)
#
# interface name
ifName = '.1.3.6.1.2.1.31.1.1.1.1'
snmp_mib_variables['ifName'] = ifName

# high speed, in units of 1 Mbps
ifHighSpeed = '.1.3.6.1.2.1.31.1.1.1.15'
snmp_mib_variables['ifHighSpeed'] = ifHighSpeed

ifConnectorPresent = '.1.3.6.1.2.1.31.1.1.1.17'  # if SNMP_TRUE, then Physical port, otherwize virtual
snmp_mib_variables['ifConnectorPresent'] = ifConnectorPresent

# description, i.e. interface Descriptions
ifAlias = '.1.3.6.1.2.1.31.1.1.1.18'  # From IF-MIB
snmp_mib_variables['ifAlias'] = ifAlias

# ifStackTable, containing 'sub-interface' information
# .1.3.6.1.2.1.31.1.2 (ifStackTable)
# contains entries of ifStackEntry:

# interface stack, ie bridge aggregation, etc.
ifStackEntry = '.1.3.6.1.2.1.31.1.2.1'
snmp_mib_variables['ifStackEntry'] = ifStackEntry

ifStackHigherLayer = '.1.3.6.1.2.1.31.1.2.1.1'  # ifStackHigherLayer
snmp_mib_variables['ifStackHigherLayer'] = ifStackHigherLayer

ifStackLowerLayer = '.1.3.6.1.2.1.31.1.2.1.2'  # ifStackLowerLayer
snmp_mib_variables['ifStackLowerLayer'] = ifStackLowerLayer

ifStackStatus = '.1.3.6.1.2.1.31.1.2.1.3'  # ifStackStatus
snmp_mib_variables['ifStackStatus'] = ifStackStatus

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
1.3.6.1.2.1.47.1.1.1.1.5 (entPhysicalClass)
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

entPhysicalEntry = '.1.3.6.1.2.1.47.1.1.1.1'
snmp_mib_variables['entPhysicalEntry'] = entPhysicalEntry

entPhysicalIndex = '.1.3.6.1.2.1.47.1.1.1.1.1'
snmp_mib_variables['entPhysicalIndex'] = entPhysicalIndex

entPhysicalDescr = '.1.3.6.1.2.1.47.1.1.1.1.2'
snmp_mib_variables['entPhysicalDescr'] = entPhysicalDescr

entPhysicalClass = '.1.3.6.1.2.1.47.1.1.1.1.5'  # entPhysicalClass
snmp_mib_variables['entPhysicalClass'] = entPhysicalClass

entPhysicalSerialNum = '.1.3.6.1.2.1.47.1.1.1.1.11'
snmp_mib_variables['entPhysicalSerialNum'] = entPhysicalSerialNum

entPhysicalSoftwareRev = '.1.3.6.1.2.1.47.1.1.1.1.10'  # entPhysicalSoftwareRev
snmp_mib_variables['entPhysicalSoftwareRev'] = entPhysicalSoftwareRev

entPhysicalModelName = '.1.3.6.1.2.1.47.1.1.1.1.13'  # entPhysicalModelName
snmp_mib_variables['entPhysicalModelName'] = entPhysicalModelName

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

#
# POE RELATED
#
# ALL of these are followed by devId.ifIndex, where devId is stack member
powerEthernetMIB = '.1.3.6.1.2.1.105'
snmp_mib_variables['powerEthernetMIB'] = powerEthernetMIB

#
# the pethMainPseEntry table entries with device-level PoE info
#
pethMainPseEntry = '.1.3.6.1.2.1.105.1.3.1.1'
snmp_mib_variables['pethMainPseEntry'] = pethMainPseEntry

pethMainPsePower = '.1.3.6.1.2.1.105.1.3.1.1.2'  # followed by devId.index, where devId is stack member
snmp_mib_variables['pethMainPsePower'] = pethMainPsePower  # in Watts

pethMainPseOperStatus = '.1.3.6.1.2.1.105.1.3.1.1.3'  # followed by devId.index, where devId is stack member
snmp_mib_variables['pethMainPseOperStatus'] = pethMainPseOperStatus  # on=1, off=2, faulty=3

pethMainPseConsumptionPower = '.1.3.6.1.2.1.105.1.3.1.1.4'  # followed by devId.index, where devId is stack member
snmp_mib_variables['pethMainPseConsumptionPower'] = pethMainPseConsumptionPower  # in Watts

pethMainPseUsageThreshold = '.1.3.6.1.2.1.105.1.3.1.1.5'  # followed by devId.index, where devId is stack member
snmp_mib_variables['pethMainPseUsageThreshold'] = pethMainPseUsageThreshold  # in percent, e.g. 80 = 80%

#
# the pethPsePortEntry tables with port-level PoE info
#
pethPsePortEntry = '.1.3.6.1.2.1.105.1.1.1'
snmp_mib_variables['pethPsePortEntry'] = pethPsePortEntry

pethPsePortAdminEnable = '.1.3.6.1.2.1.105.1.1.1.3'  # followed by devId.ifIndex, where devId is stack member
snmp_mib_variables['pethPsePortAdminEnable'] = pethPsePortAdminEnable

pethPsePortDetectionStatus = '.1.3.6.1.2.1.105.1.1.1.6'  # followed by devId.ifIndex, where devId is stack member
snmp_mib_variables['pethPsePortDetectionStatus'] = pethPsePortDetectionStatus

pethPsePortPowerPriority = '.1.3.6.1.2.1.105.1.1.1.7'  # followed by devId.ifIndex, where devId is stack member
snmp_mib_variables['pethPsePortPowerPriority'] = pethPsePortPowerPriority

pethPsePortType = '.1.3.6.1.2.1.105.1.1.1.9'  # followed by devId.ifIndex, where devId is stack member
snmp_mib_variables['pethPsePortType'] = pethPsePortType


# SYSLOG-MSGS-MIB
syslogMsgMib = '.1.3.6.1.2.1.192'

syslogMsgObjects = '.1.3.6.1.2.1.192.1'
snmp_mib_variables['syslogMsgObjects'] = syslogMsgObjects

syslogMsgTableMaxSize = '.1.3.6.1.2.1.192.1.1.1'
snmp_mib_variables['syslogMsgTableMaxSize'] = syslogMsgTableMaxSize

syslogMsgTable = '.1.3.6.1.2.1.192.1.2'

"""
Note: the rest of the SYSLOG_MSG_MIB is meant to define OID's for sending
SNMP notifications (traps) with syslog messages, NOT to poll messages from snmp reads.

snmp_mib_variables['syslogMsgTable'] = syslogMsgTable
syslogMsgEntry = '.1.3.6.1.2.1.192.1.2.1'
syslogMsgIndex = '.1.3.6.1.2.1.192.1.2.1.1'
syslogMsgFacility = '.1.3.6.1.2.1.192.1.2.1.2'
syslogMsgSeverity = '.1.3.6.1.2.1.192.1.2.1.3'
syslogMsgVersion = '.1.3.6.1.2.1.192.1.2.1.4'
syslogMsgTimeStamp = '.1.3.6.1.2.1.192.1.2.1.5'
syslogMsgHostName = '.1.3.6.1.2.1.192.1.2.1.6'
syslogMsgAppName = '.1.3.6.1.2.1.192.1.2.1.7'
syslogMsgProcID	= '.1.3.6.1.2.1.192.1.2.1.8'
syslogMsgMsgID = '.1.3.6.1.2.1.192.1.2.1.9'
syslogMsgSDParams = '.1.3.6.1.2.1.192.1.2.1.10'
syslogMsgMsg = '.1.3.6.1.2.1.192.1.2.1.11'
"""


# IEEE also has a Dot1Q MIB:
# see also https://mibs.observium.org/mib/IEEE8021-Q-BRIDGE-MIB/
# or https://www.circitor.fr/Mibs/Html/I/IEEE8021-Q-BRIDGE-MIB.php
ieee8021QBridgeMib = '.1.3.111.2.802.1.1.4'

ieee8021QBridgeMvrpEnabledStatus = '.1.3.111.2.802.1.1.4.1.1.1.1.6'
snmp_mib_variables['ieee8021QBridgeMvrpEnabledStatus'] = ieee8021QBridgeMvrpEnabledStatus

# the ports currently active on all vlans, including dynamic.
# if multiple ports, then port is in trunk mode!
ieee8021QBridgeVlanCurrentEgressPorts = '.1.3.111.2.802.1.1.4.1.4.2.1.5'
snmp_mib_variables['ieee8021QBridgeVlanCurrentEgressPorts'] = ieee8021QBridgeVlanCurrentEgressPorts

# the untagged ports on all vlans (including dynamic.)
ieee8021QBridgeVlanCurrentUntaggedPorts = '.1.3.111.2.802.1.1.4.1.4.2.1.6'
snmp_mib_variables['ieee8021QBridgeVlanCurrentUntaggedPorts'] = ieee8021QBridgeVlanCurrentUntaggedPorts

# all existing vlans, static and dynamic:
ieee8021QBridgeVlanStatus = '.1.3.111.2.802.1.1.4.1.4.2.1.7'

#
# information about statically defined vlans:
#
ieee8021QBridgeVlanStaticTable = '.1.3.111.2.802.1.1.4.1.4.3'
snmp_mib_variables['ieee8021QBridgeVlanStaticTable'] = ieee8021QBridgeVlanStaticTable

# a vlan entry is below this:
ieee8021QBridgeVlanStaticEntry = '.1.3.111.2.802.1.1.4.1.4.3.1'
snmp_mib_variables['ieee8021QBridgeVlanStaticEntry'] = ieee8021QBridgeVlanStaticEntry

# various vlan attributes:
#
# vlan names:
ieee8021QBridgeVlanStaticName = '.1.3.111.2.802.1.1.4.1.4.3.1.3.1'
snmp_mib_variables['ieee8021QBridgeVlanStaticName'] = ieee8021QBridgeVlanStaticName

# this is the ports on staticly defined vlans only! (not dynamic vlans)
ieee8021QBridgeVlanStaticEgressPorts = '.1.3.111.2.802.1.1.4.1.4.3.1.4'
snmp_mib_variables['ieee8021QBridgeVlanStaticEgressPorts'] = ieee8021QBridgeVlanStaticEgressPorts

# this is the ports on staticly defined vlans only! (not dynamic vlans)
ieee8021QBridgeVlanStaticUntaggedPorts = '.1.3.111.2.802.1.1.4.1.4.3.1.6'
snmp_mib_variables['ieee8021QBridgeVlanStaticUntaggedPorts'] = ieee8021QBridgeVlanStaticUntaggedPorts

# the statically defined vlans on a device
ieee8021QBridgeVlanStaticRowStatus = '.1.3.111.2.802.1.1.4.1.4.3.1.7'
snmp_mib_variables['ieee8021QBridgeVlanStaticRowStatus'] = ieee8021QBridgeVlanStaticRowStatus

#
# Port VLAN table
# ieee8021QBridgePortVlanTable = '.1.3.111.2.802.1.1.4.1.4.5'
#

# Port VLAN entries are below this:
ieee8021QBridgePortVlanEntry = '.1.3.111.2.802.1.1.4.1.4.5.1'
snmp_mib_variables['ieee8021QBridgePortVlanEntry'] = ieee8021QBridgePortVlanEntry

# the PVID of a port is in the VlanEntry:.
# see also https://oidref.com/1.3.111.2.802.1.1.4.1.4.5.1.1
ieee8021QBridgePvid = '.1.3.111.2.802.1.1.4.1.4.5.1.1'
snmp_mib_variables['ieee8021QBridgePvid'] = ieee8021QBridgePvid

# possibly interesting:
# ieee8021QBridgePortMvrpEnabledStatus = '.1.3.111.2.802.1.1.4.1.4.5.1.4'


#
# LLDP related#
#
# local port:
# (lldpLocPortEntry)
lldpObjects = '.1.0.8802.1.1.2.1'  # start of lldpObjects
snmp_mib_variables['lldpObjects'] = lldpObjects

# local system data at  .1.0.8802.1.1.2.1.3
lldpLocalSystemData = '.1.0.8802.1.1.2.1.3'
snmp_mib_variables['lldpLocalSystemData'] = lldpLocalSystemData

lldpLocChassisIdSubtype = '.1.0.8802.1.1.2.1.3.1.0'
snmp_mib_variables['lldpLocChassisIdSubtype'] = lldpLocChassisIdSubtype

lldpLocChassisId = '.1.0.8802.1.1.2.1.3.2.0'
snmp_mib_variables['lldpLocChassisId'] = lldpLocChassisId

lldpLocSysName = '.1.0.8802.1.1.2.1.3.3.0'
snmp_mib_variables['lldpLocSysName'] = lldpLocSysName

lldpLocSysDesc = '.1.0.8802.1.1.2.1.3.4.0'
snmp_mib_variables['lldpLocSysDesc'] = lldpLocSysDesc

# lldpLocSysCapSupported, local capabilities supported, see bitmap below
lldpLocSysCapSupported = '.1.0.8802.1.1.2.1.3.5.0'
snmp_mib_variables['lldpLocSysCapSupported'] = lldpLocSysCapSupported

# lldpLocSysCapEnabled, local capabilities enabled, see bitmap below
lldpLocSysCapEnabled = '.1.0.8802.1.1.2.1.3.6.0'
snmp_mib_variables['lldpLocSysCapEnabled'] = lldpLocSysCapEnabled

# lldpLocPortTable
lldpLocPortTable = '.1.0.8802.1.1.2.1.3.7'
snmp_mib_variables['lldpLocPortTable'] = lldpLocPortTable

# remote system data at .1.0.8802.1.1.2.1.4
# lldpRemEntry
lldpRemEntry = '.1.0.8802.1.1.2.1.4.1.1'
snmp_mib_variables['lldpRemEntry'] = lldpRemEntry

# LLDP_REM_TIMEMARK =       '.1.0.8802.1.1.2.1.4.1.1.1'  # NOT USED
# this does not appear to be implemented in most gear.
# This would mean that the interface ID is based on Dot1Q port map, or IFMIB-ifIndex
lldpRemLocalPortNum = '.1.0.8802.1.1.2.1.4.1.1.2'
snmp_mib_variables['lldpRemLocalPortNum'] = lldpRemLocalPortNum

# the following are indexed by  <remote-device-random-id>.<port-id>.1
lldpRemIndex = '.1.0.8802.1.1.2.1.4.1.1.3'
snmp_mib_variables['lldpRemIndex'] = lldpRemIndex

lldpRemChassisIdSubtype = '.1.0.8802.1.1.2.1.4.1.1.4'
snmp_mib_variables['lldpRemChassisIdSubtype'] = lldpRemChassisIdSubtype
# note: the definitions of this chassis type are now in
# switches/connect/constants.py, around line 65

lldpRemChassisId = '.1.0.8802.1.1.2.1.4.1.1.5'
snmp_mib_variables['lldpRemChassisId'] = lldpRemChassisId

# this is used to indate the type of data sent by lldpRemPortId
# see https://www.circitor.fr/Mibs/Html/L/LLDP-MIB.php#LldpChassisIdSubtype
lldpRemPortIdSubType = '.1.0.8802.1.1.2.1.4.1.1.6'
snmp_mib_variables['lldpRemPortIdSubType'] = lldpRemPortIdSubType

lldpRemPortId = '.1.0.8802.1.1.2.1.4.1.1.7'
snmp_mib_variables['lldpRemPortId'] = lldpRemPortId

lldpRemPortDesc = '.1.0.8802.1.1.2.1.4.1.1.8'
snmp_mib_variables['lldpRemPortDesc'] = lldpRemPortDesc

lldpRemSysName = '.1.0.8802.1.1.2.1.4.1.1.9'
snmp_mib_variables['lldpRemSysName'] = lldpRemSysName

lldpRemSysDesc = '.1.0.8802.1.1.2.1.4.1.1.10'
snmp_mib_variables['lldpRemSysDesc'] = lldpRemSysDesc

# capabilities, see entry for "LldpSystemCapabilitiesMap" at
# http://www.ieee802.org/1/files/public/MIBs/LLDP-MIB-200505060000Z.txt
lldpRemSysCapSupported = '.1.0.8802.1.1.2.1.4.1.1.11'  # lldpRemSysCapSupported bitmap!
snmp_mib_variables['lldpRemSysCapSupported'] = lldpRemSysCapSupported

lldpRemSysCapEnabled = '.1.0.8802.1.1.2.1.4.1.1.12'  # lldpRemSysCapEnabled bitmap!
snmp_mib_variables['lldpRemSysCapEnabled'] = lldpRemSysCapEnabled

# Capabilities bits. Note this is IN NETWORK ORDER, ie low order bit first!!!
LLDP_CAPA_BITS_OTHER = 0x80  # other(0),
LLDP_CAPA_BITS_REPEATER = 0x40  # repeater(1),
LLDP_CAPA_BITS_BRIDGE = 0x20  # bridge(2),
LLDP_CAPA_BITS_WLAN = 0x10  # wlanAccessPoint(3),
LLDP_CAPA_BITS_ROUTER = 0x08  # router(4),
LLDP_CAPA_BITS_PHONE = 0x04  # telephone(5)
LLDP_CAPA_BITS_DOCSIS = 0x02  # docsisCableDevice(6),
LLDP_CAPA_BITS_STATION = 0x01  # stationOnly(7)

# the management address entries of the remove device:
# MIB base at lldpRemManAddrEntry
lldpRemManAddrEntry = '.1.0.8802.1.1.2.1.4.2.1'
snmp_mib_variables['lldpRemManAddrEntry'] = lldpRemManAddrEntry
#
# Note: most devices do not send .1, .2 or .3
#
# lldpRemManAddrSubtype is either IANA_TYPE_IPV4 or IPV6
# lldpRemManAddrSubtype = '.1.0.8802.1.1.2.1.4.2.1.1'
# snmp_mib_variables['lldpRemManAddrSubtype'] = lldpRemManAddrSubtype
#
# a string for the address, of type indicated by above lldpRemManAddrSubtype
# lldpRemManAddr = '.11.0.8802.1.1.2.1.4.2.1.2'
# snmp_mib_variables['lldpRemManAddr'] = lldpRemManAddr
#
# management address interface numbering method
lldpRemManAddrIfSubtype = '.1.0.8802.1.1.2.1.4.2.1.3'
snmp_mib_variables['lldpRemManAddrIfSubtype'] = lldpRemManAddrIfSubtype
LLDP_REM_MAN_ADDR_TYPE_UNKNOWN = 1  # unknown(1)
LLDP_REM_MAN_ADDR_TYPE_IFINDEX = 2  # ifIndex(2)
LLDP_REM_MAN_ADDR_TYPE_SYSTEMPORTNUMBER = 3  # systemPortNumber(3)
#
# these two don't add much:
#
# management address interface id
# lldpRemManAddrIfId = '.11.0.8802.1.1.2.1.4.2.1.4'
# snmp_mib_variables['lldpRemManAddrIfId'] = lldpRemManAddrIfId
# management address device OID:
# lldpRemManAddrOID = '.11.0.8802.1.1.2.1.4.2.1.5'
# snmp_mib_variables['	lldpRemManAddrOID'] = 	lldpRemManAddrOID


#
# LACP MIB
#
# see also
# http://cric.grenoble.cnrs.fr/Administrateurs/Outils/MIBS/?oid=1.2.840.10006.300.43.1.1
# https://stackoverflow.com/questions/14960157/how-to-map-portchannel-to-interfaces-via-snmp
#

dot3adAgg = '.1.2.840.10006.300.43.1.1'

#
# info about the aggregator interfaces (Bridge-Aggregate or Port-Channel)
#
# The current operational value of the Key for the Aggregator. The administrative Key value may differ from the
# operational Key value for the reasons discussed in 43.6.2. This is a 16-bit read-only value.
# The meaning of particular Key values is of local significance.
# Syntax: "LacpKey" (IEEE8023-LAG-MIB)
dot3adAggActorAdminKey = '.1.2.840.10006.300.43.1.1.1.1.6'
snmp_mib_variables['dot3adAggActorAdminKey'] = dot3adAggActorAdminKey
# operational key "index" when the aggregate interface is up (ie at least one port in "up" state!)
dot3adAggActorOperKey = '.1.2.840.10006.300.43.1.1.1.1.7'

#
# member ports information:
#
dot3adAggPortListEntry = '.1.2.840.10006.300.43.1.1.2.1'
dot3adAggPortListPorts = '.1.2.840.10006.300.43.1.1.2.1.1'

# all info about LACP ports
dot3adAggPortTable = '.1.2.840.10006.300.43.1.2.1'
dot3adAggPortEntry = '.1.2.840.10006.300.43.1.2.1.1'

# Mapping of LACP member back to Aggregator interface via the Admin or Operational key
#
# this is the administrative key, which maps back to the aggregator interface admin LacpKey found at dot3adAggActorAdminKey
# NOTE: this key is always present,
# whereas the Operations key (next item) is only set when the aggregate is up and the interface joined
dot3adAggPortActorAdminKey = '.1.2.840.10006.300.43.1.2.1.1.4'
snmp_mib_variables['dot3adAggPortActorAdminKey'] = dot3adAggPortActorAdminKey

# this is the administrative key, which maps back to the aggregator interface admin LacpKey found at dot3adAggActorAdminKey
# this is the operational key, which only maps back to the aggregator interface operational LacpKey found at dot3adAggOperAdminKey
# when the aggregate is up and the interface joined !!!
dot3adAggPortActorOperKey = '.1.2.840.10006.300.43.1.2.1.1.5'
snmp_mib_variables['dot3adAggPortActorOperKey'] = dot3adAggPortActorOperKey

# specifically, what interfaces are members, i.e.:
# dot3adAggPortSelectedAggID.<member interface ifIndex> = <lacp virtual interface ifIndex>
dot3adAggPortSelectedAggID = '.1.2.840.10006.300.43.1.2.1.1.12'
snmp_mib_variables['dot3adAggPortSelectedAggID'] = dot3adAggPortSelectedAggID

# The identifier value of the Aggregator that this Aggregation Port is currently attached to.
# Zero indicates that the Aggregation Port is not currently attached to an Aggregator. This value is read-only.
# dot3adAggPortAttachedAggID.<member interface ifIndex> = <lacp virtual interface ifIndex>
dot3adAggPortAttachedAggID = '.1.2.840.10006.300.43.1.2.1.1.13'
snmp_mib_variables['dot3adAggPortAttachedAggID'] = dot3adAggPortAttachedAggID

# The port number locally assigned to the Aggregation Port.
# The port number is communicated in LACPDUs as the Actor_Port. This value is read-only.
# a none-zero value means member of some LACP port
dot3adAggPortActorPort = '.1.2.840.10006.300.43.1.2.1.1.14'

# A string of 8 bits, "LacpState", corresponding to the current operational values of Actor_State as transmitted by the Actor in LACPDUs.
# The bit allocations are as defined in 30.7.2.1.20.
# This attribute value is read-only.
dot3adAggPortActorOperState = '.1.2.840.10006.300.43.1.2.1.1.21'

# A read-only Boolean value indicating whether the Aggregation Port is able to Aggregate (`TRUE')
# or is only able to operate as an Individual link (`FALSE').
# Syntax: TruthValue (SNMPv2-TC)
dot3adAggPortAggregateOrIndividual = '.1.2.840.10006.300.43.1.2.1.1.24'
snmp_mib_variables['dot3adAggPortAggregateOrIndividual'] = dot3adAggPortAggregateOrIndividual


#
# MPLS L3VPN related, aka "VRF" data
# in the MPLS-L3VPN-STD-MIB
# good reference is https://mibs.observium.org/mib/MPLS-L3VPN-STD-MIB/
#

# the start of the "VRF table":
# mplsL3VpnVrfTable = ".1.3.6.1.2.1.10.166.11.1.2.2"

# and all the "VRF" entries:
mplsL3VpnVrfEntry = ".1.3.6.1.2.1.10.166.11.1.2.2.1"
snmp_mib_variables['mplsL3VpnVrfEntry'] = mplsL3VpnVrfEntry
# the entries in each "row" of the table:
mplsL3VpnVrfName = ".1.3.6.1.2.1.10.166.11.1.2.2.1.1"
# mplsL3VpnVrfVpnId 		.1.3.6.1.2.1.10.166.11.1.2.2.1.2
mplsL3VpnVrfDescription = ".1.3.6.1.2.1.10.166.11.1.2.2.1.3"
mplsL3VpnVrfRD = ".1.3.6.1.2.1.10.166.11.1.2.2.1.4"
# mplsL3VpnVrfCreationTime 		.1.3.6.1.2.1.10.166.11.1.2.2.1.5
mplsL3VpnVrfOperStatus = ".1.3.6.1.2.1.10.166.11.1.2.2.1.6"
mplsL3VpnVrfActiveInterfaces = '.1.3.6.1.2.1.10.166.11.1.2.2.1.7'
# mplsL3VpnVrfAssociatedInterfaces 		.1.3.6.1.2.1.10.166.11.1.2.2.1.8
# mplsL3VpnVrfConfMidRteThresh 		.1.3.6.1.2.1.10.166.11.1.2.2.1.9
# mplsL3VpnVrfConfHighRteThresh 		.1.3.6.1.2.1.10.166.11.1.2.2.1.10
# mplsL3VpnVrfConfMaxRoutes 		.1.3.6.1.2.1.10.166.11.1.2.2.1.11
# mplsL3VpnVrfConfLastChanged 		.1.3.6.1.2.1.10.166.11.1.2.2.1.12
# mplsL3VpnVrfConfRowStatus 		.1.3.6.1.2.1.10.166.11.1.2.2.1.13
mplsL3VpnVrfConfAdminStatus = ".1.3.6.1.2.1.10.166.11.1.2.2.1.14"
# mplsL3VpnVrfConfStorageType 		.1.3.6.1.2.1.10.166.11.1.2.2.1.15

MPLS_VRF_STATE_ENABLED = 1
MPLS_VRF_STATE_DISABLED = 2


# the VRF IF Conf Table entries have the lists of interfaces that are part of a VRF
# indexed by VRF name (as oid string) with interface id, value is dependent on variable.
# mplsL3VpnIfConfTable = .1.3.6.1.2.1.10.166.11.1.2.1
mplsL3VpnIfConfEntry = ".1.3.6.1.2.1.10.166.11.1.2.1.1"
mplsL3VpnIfConfIndex = ".1.3.6.1.2.1.10.166.11.1.2.1.1.1"  # appears NOT used!

mplsL3VpnIfVpnClassification = ".1.3.6.1.2.1.10.166.11.1.2.1.1.2"
snmp_mib_variables['mplsL3VpnIfVpnClassification'] = mplsL3VpnIfVpnClassification
VPN_CLASSIFICATION_CARRIER = 1
VPN_CLASSIFICATION_ENTERPRISE = 2
VPN_CLASSIFICATION_INTERPROVIDER = 2
# E.g.:  .1.3.6.1.2.1.10.166.11.1.2.1.1.2.6.86.79.73.80.95.72.2156 = INTEGER: 2
# The VRF name of length 6, OID chars 86.79.73.80.95.72 is active on ifIndex 2156 with Vpn Classificaciton 2
# ie. VRF "VOIP_H" on ifIndex 2156

mplsL3VpnIfVpnRouteDistProtocol = ".1.3.6.1.2.1.10.166.11.1.2.1.1.3"
# Note: the value is a Bit Mask indicating the protocols in use:
L3VPN_ROUTE_DIST_PROTOCOL_NONE = 0
L3VPN_ROUTE_DIST_PROTOCOL_BGP_BIT = 1
L3VPN_ROUTE_DIST_PROTOCOL_OSPF_BIT = 2
L3VPN_ROUTE_DIST_PROTOCOL_RIP_BIT = 3
L3VPN_ROUTE_DIST_PROTOCOL_ISIS_BIT = 4
L3VPN_ROUTE_DIST_PROTOCOL_STATIC_BIT = 5
L3VPN_ROUTE_DIST_PROTOCOL_OTHER_BIT = 6

mplsL3VpnIfConfStorageType = ".1.3.6.1.2.1.10.166.11.1.2.1.1.4"
mplsL3VpnIfConfRowStatus = ".1.3.6.1.2.1.10.166.11.1.2.1.1.5"

#
# MAU (Media Access Unit) mib is the standard way of describing media types, ie. transceivers.
# See
# https://mibs.observium.org/mib/MAU-MIB/
# https://github.com/librenms/librenms/blob/master/mibs/IANA-MAU-MIB
#
# ifMauIfIndex = ".1.3.6.1.2.1.26.2.1.1.1"
#
ifMauType = ".1.3.6.1.2.1.26.2.1.1.3"
snmp_mib_variables['ifMauType'] = ifMauType

# and the type values are defined at:
# https://datatracker.ietf.org/doc/html/rfc3636
# https://www.iana.org/assignments/ianamau-mib/ianamau-mib
# these are show at the above ifMauType as ".1.3.6.1.2.1.26.4.<type-integer>"
MAU_TYPE_BASE = ".1.3.6.1.2.1.26.4."
MAU_TYPE_UNKNOWN = ".0.0"
# Here are the entries we mostly care about, organized by speed:
mau_types = {}
# mau_types[0] = "Unknown"
mau_types[23] = "1000BASE-LX(Hd)"
mau_types[24] = "1000BASE-LX"
mau_types[25] = "1000BASE-SX(Hd)"
mau_types[26] = "1000BASE-SX"
mau_types[27] = "1000BASE-CX(Hd)"
mau_types[28] = "1000BASE-CX"

mau_types[34] = "10GBASE-ER"
mau_types[35] = "10GBASE-LR"
mau_types[36] = "10GBASE-SR"

mau_types[93] = "25GBASE-SR"
mau_types[114] = "25GBASE-LR"
mau_types[115] = "25GBASE-ER"

mau_types[72] = "40GBASE-SR4"
mau_types[74] = "40GBASE-LR4"
mau_types[95] = "40GBASE-ER4"

mau_types[119] = "50GBASE-SR"
mau_types[120] = "50GBASE-FR"
mau_types[121] = "50GBASE-LR"
mau_types[122] = "50GBASE-ER"

mau_types[77] = "100GBASE-LR4"
mau_types[78] = "100GBASE-ER4"
mau_types[102] = "100GBASE-SR4"
mau_types[194] = "100GBASE-ZR"

mau_types[128] = "200GBASE-DR4"
mau_types[129] = "200GBASE-FR4"
mau_types[130] = "200GBASE-LR4"
mau_types[133] = "200GBASE-SR4"
mau_types[134] = "200GBASE-ER4"

mau_types[136] = "400GBASE-SR16"
mau_types[137] = "400GBASE-DR4"
mau_types[138] = "400GBASE-FR8"
mau_types[139] = "400GBASE-LR8"
mau_types[140] = "400GBASE-ER8"
mau_types[147] = "400GBASE-FR4"
mau_types[148] = "400GBASE-LR4-6"
mau_types[149] = "400GBASE-SR8"
mau_types[150] = "400GBASE-LR4.2"
mau_types[219] = "400GBASE-DR4-2"

mau_types[220] = "800GBASE-CR8"
mau_types[221] = "800GBASE-DR8"
mau_types[222] = "800GBASE-DR8-2"
mau_types[223] = "800GBASE-KR8"
mau_types[224] = "800GBASE-R"
mau_types[225] = "800GBASE-SR8"
mau_types[226] = "800GBASE-VR8"


#
# VENDOR SPECIFIC Entries, see vendor driver folder "constants.py"
#

# System Object ID: Vendor ID is the first number after this:
enterprises = '.1.3.6.1.4.1'
snmp_mib_variables['enterprises'] = enterprises
