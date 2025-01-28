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

from switches.connect.snmp.constants import snmp_mib_variables, enterprise_id_info

# Cisco specific constants
ENTERPRISE_ID_CISCO = 9
enterprise_id_info[ENTERPRISE_ID_CISCO] = 'Cisco'

# the various snmp driver mib types we can detect:
CISCO_DEVICE_TYPE_UNKNOWN_MIB = 0
CISCO_DEVICE_TYPE_VTP_MIB = 1
CISCO_DEVICE_TYPE_SB_MIB = 2
cisco_device_types = {}
cisco_device_types[CISCO_DEVICE_TYPE_UNKNOWN_MIB] = "Unknown (MIB ?)"
cisco_device_types[CISCO_DEVICE_TYPE_VTP_MIB] = "Catalyst (VTP MIB)"
cisco_device_types[CISCO_DEVICE_TYPE_SB_MIB] = "CBS (SB MIB)"

# CDP MIB:
# https://mibs.observium.org/mib/CISCO-CDP-MIB/
# Normall, Cisco device support the standard LLDP mib as well!
#
# ciscoCdpMIB = '.1.3.6.1.4.1.9.9.23'

# CISCO-SYSLOG-MIB
# http://www.circitor.fr/Mibs/Html/C/CISCO-SYSLOG-MIB.php
ciscoSyslogMIB = '.1.3.6.1.4.1.9.9.41'

# here is the config:
ciscoSyslogMIBObjects = '.1.3.6.1.4.1.9.9.41.1'
snmp_mib_variables['ciscoSyslogMIBObjects'] = ciscoSyslogMIBObjects

clogHistTableMaxLength = '.1.3.6.1.4.1.9.9.41.1.2.1'
snmp_mib_variables['clogHistTableMaxLength'] = clogHistTableMaxLength

clogHistMsgsFlushed = '.1.3.6.1.4.1.9.9.41.1.2.2'
snmp_mib_variables['clogHistMsgsFlushed'] = clogHistMsgsFlushed

# here are the messages:
clogHistoryTable = '.1.3.6.1.4.1.9.9.41.1.2.3'
snmp_mib_variables['clogHistoryTable'] = clogHistoryTable
clogHistIndex = '.1.3.6.1.4.1.9.9.41.1.2.3.1.1'
snmp_mib_variables['clogHistIndex'] = clogHistIndex
clogHistFacility = '.1.3.6.1.4.1.9.9.41.1.2.3.1.2'
snmp_mib_variables['clogHistFacility'] = clogHistFacility
clogHistSeverity = '.1.3.6.1.4.1.9.9.41.1.2.3.1.3'
snmp_mib_variables['clogHistSeverity'] = clogHistSeverity
clogHistMsgName = '.1.3.6.1.4.1.9.9.41.1.2.3.1.4'
snmp_mib_variables['clogHistMsgName'] = clogHistMsgName
clogHistMsgText = '.1.3.6.1.4.1.9.9.41.1.2.3.1.5'
snmp_mib_variables['clogHistMsgText'] = clogHistMsgText
clogHistTimestamp = '.1.3.6.1.4.1.9.9.41.1.2.3.1.6'
snmp_mib_variables['clogHistTimestamp'] = clogHistTimestamp

# most Cisco switches support this:
# http://www.circitor.fr/Mibs/Html/C/CISCO-CONFIG-MAN-MIB.php

ciscoConfigManMIBObjects = '.1.3.6.1.4.1.9.9.43.1'
snmp_mib_variables['ciscoConfigManMIBObjects'] = ciscoConfigManMIBObjects

ccmHistory = '.1.3.6.1.4.1.9.9.43.1.1'
snmp_mib_variables['ccmHistory'] = ccmHistory

# these values are the value of sysUpTime for the event, i.e. ticks in 1/100th of a second:
ccmHistoryRunningLastChanged = '.1.3.6.1.4.1.9.9.43.1.1.1'
snmp_mib_variables['ccmHistoryRunningLastChanged'] = ccmHistoryRunningLastChanged

ccmHistoryRunningLastSaved = '.1.3.6.1.4.1.9.9.43.1.1.2'
snmp_mib_variables['ccmHistoryRunningLastSaved'] = ccmHistoryRunningLastSaved

ccmHistoryStartupLastChanged = '.1.3.6.1.4.1.9.9.43.1.1.3'
snmp_mib_variables['ccmHistoryStartupLastChanged'] = ccmHistoryStartupLastChanged


# VTP MIB:
# https://mibs.observium.org/mib/CISCO-VTP-MIB/
#
# ciscoVtpMIB = .1.3.6.1.4.1.9.9.46
#
# Note: older style Cisco device use this MIB for vlans, port vlan changes, etc.
# newer style use the 'standard' Q-Bridge or CiscoSB mibs.
#

# used to probe VTP mib existance:
vtpVersion = '.1.3.6.1.4.1.9.9.46.1.1.1'
snmp_mib_variables['vtpVersion'] = vtpVersion

# the vlan state, ie shows the list of vlans
vtpVlanState = '.1.3.6.1.4.1.9.9.46.1.3.1.1.2.1'
snmp_mib_variables['vtpVlanState'] = vtpVlanState

# and the type, see types below
vtpVlanType = '.1.3.6.1.4.1.9.9.46.1.3.1.1.3.1'
snmp_mib_variables['vtpVlanType'] = vtpVlanType

CISCO_VLAN_TYPE_NORMAL = 1  # regular(1)
CISCO_VLAN_TYPE_FDDI = 2  # fddi(2)
CISCO_VLAN_TYPE_TOKENRING = 3  # tokenRing(3)
CISCO_VLAN_TYPE_FDDINET = 4  # fddiNet(4)
CISCO_VLAN_TYPE_TRNET = 5  # trNet(5)

vtpVlanName = '.1.3.6.1.4.1.9.9.46.1.3.1.1.4.1'
snmp_mib_variables['vtpVlanName'] = vtpVlanName
# VTP trunk ports start at .1.3.6.1.4.1.9.9.46.1.6
# details about ports start at .1.3.6.1.4.1.9.9.46.1.6.1.1

# the vlans in a trunk port, using the switchport bitmap format:
vlanTrunkPortVlansEnabled = '.1.3.6.1.4.1.9.9.46.1.6.1.1.4'
snmp_mib_variables['vlanTrunkPortVlansEnabled'] = vlanTrunkPortVlansEnabled

# native/untagged vlan on a trunk port
vlanTrunkPortNativeVlan = '.1.3.6.1.4.1.9.9.46.1.6.1.1.5'
snmp_mib_variables['vlanTrunkPortNativeVlan'] = vlanTrunkPortNativeVlan

vlanTrunkPortDynamicState = '.1.3.6.1.4.1.9.9.46.1.6.1.1.13'
snmp_mib_variables['vlanTrunkPortDynamicState'] = vlanTrunkPortDynamicState
VTP_TRUNK_STATE_ON = 1
VTP_TRUNK_STATE_OFF = 2
VTP_TRUNK_STATE_DESIRED = 3
VTP_TRUNK_STATE_AUTO = 4
VTP_TRUNK_STATE_NO_NEGOTIATE = 5

# actual trunk status, result of the vlanTrunkPortDynamicState and the ifOperStatus of the trunk port itself
# ie when port is down, this shows DISABLED!!!
vlanTrunkPortDynamicStatus = '.1.3.6.1.4.1.9.9.46.1.6.1.1.14'
snmp_mib_variables['vlanTrunkPortDynamicStatus'] = vlanTrunkPortDynamicStatus
VTP_PORT_TRUNK_ENABLED = 1
VTP_PORT_TRUNK_DISABLED = 2

# the high-numbered vlans 1024-2047 in a trunk port, using the switchport bitmap format:
vlanTrunkPortVlansEnabled2k = '.1.3.6.1.4.1.9.9.46.1.6.1.1.17'
snmp_mib_variables['vlanTrunkPortVlansEnabled2k'] = vlanTrunkPortVlansEnabled2k

# the high-numbered vlans 2048-3071 in a trunk port, using the switchport bitmap format:
vlanTrunkPortVlansEnabled3k = '.1.3.6.1.4.1.9.9.46.1.6.1.1.18'
snmp_mib_variables['vlanTrunkPortVlansEnabled3k'] = vlanTrunkPortVlansEnabled3k

# the high-numbered vlans 3072-4095 in a trunk port, using the switchport bitmap format:
vlanTrunkPortVlansEnabled4k = '.1.3.6.1.4.1.9.9.46.1.6.1.1.19'
snmp_mib_variables['vlanTrunkPortVlansEnabled4k'] = vlanTrunkPortVlansEnabled4k

# Cisco VLAN Membership mib - on older devices only
# https://mibs.observium.org/mib/CISCO-VLAN-MEMBERSHIP-MIB/
# https://circitor.fr/Mibs/Html/CISCO-VLAN-MEMBERSHIP-MIB.php
#
# ciscoVlanMembershipMIB = '.1.3.6.1.4.1.9.9.68'
#
# this is the untagged or native vlan for a Cisco switch port
# this will NOT show ports in trunk mode!!!
vmVlan = '.1.3.6.1.4.1.9.9.68.1.2.2.1.2'
snmp_mib_variables['vmVlan'] = vmVlan

# this is the Cisco "Voice" Vlan
vmVoiceVlanId = '.1.3.6.1.4.1.9.9.68.1.5.1.1.1'
snmp_mib_variables['vmVoiceVlanId'] = vmVoiceVlanId

# Cisco Config Copy MIB
# http://www.circitor.fr/Mibs/Html/C/CISCO-CONFIG-COPY-MIB.php
ccCopySourceFileType = '.1.3.6.1.4.1.9.9.96.1.1.1.1.3'
snmp_mib_variables['ccCopySourceFileType'] = ccCopySourceFileType
runningConfig = 4

ccCopyDestFileType = '.1.3.6.1.4.1.9.9.96.1.1.1.1.4'
snmp_mib_variables['ccCopyDestFileType'] = ccCopyDestFileType
startupConfig = 3

ccCopyEntryRowStatus = '.1.3.6.1.4.1.9.9.96.1.1.1.1.14'
snmp_mib_variables['ccCopyEntryRowStatus'] = ccCopyEntryRowStatus
rowStatusActive = 1

ccCopyState = '.1.3.6.1.4.1.9.9.96.1.1.1.1.10'
snmp_mib_variables['ccCopyState'] = ccCopyState
copyStateWaiting = 1
copyStateRunning = 2
copyStateSuccess = 3
copyStateFailed = 4


# Cisco L2L3 Interface Config Mib
# http://www.circitor.fr/Mibs/Html/C/CISCO-L2L3-INTERFACE-CONFIG-MIB.php

cL2L3IfModeOper = '.1.3.6.1.4.1.9.9.151.1.1.1.1.2'
snmp_mib_variables['cL2L3IfModeOper'] = cL2L3IfModeOper
# routed(1), switchport(2)
CISCO_ROUTE_MODE = 1
CISCO_BRIDGE_MODE = 2

#
# Cisco new Extended POE mib
#
ciscoPowerEthernetExtMIB = '.1.3.6.1.4.1.9.9.402'
snmp_mib_variables['ciscoPowerEthernetExtMIB'] = ciscoPowerEthernetExtMIB

cpeExtPsePortPwrAllocated = '.1.3.6.1.4.1.9.9.402.1.2.1.7'
snmp_mib_variables['cpeExtPsePortPwrAllocated'] = cpeExtPsePortPwrAllocated

cpeExtPsePortPwrAvailable = '.1.3.6.1.4.1.9.9.402.1.2.1.8'
snmp_mib_variables['cpeExtPsePortPwrAvailable'] = cpeExtPsePortPwrAvailable

cpeExtPsePortPwrConsumption = '.1.3.6.1.4.1.9.9.402.1.2.1.9'
snmp_mib_variables['cpeExtPsePortPwrConsumption'] = cpeExtPsePortPwrConsumption

cpeExtPsePortMaxPwrDrawn = '.1.3.6.1.4.1.9.9.402.1.2.1.10'
snmp_mib_variables['cpeExtPsePortMaxPwrDrawn'] = cpeExtPsePortMaxPwrDrawn

# CISCO-STACK-MIB contains various mappings
ciscoStackMIB = '.1.3.6.1.4.1.9.5.1'
snmp_mib_variables['ciscoStackMIB'] = ciscoStackMIB
# this maps a Cisco port # to a standard if_index:
portIfIndex = '.1.3.6.1.4.1.9.5.1.4.1.1.11'
snmp_mib_variables['portIfIndex'] = portIfIndex


# OID to "write mem" via Snmp
ciscoWriteMem = '.1.3.6.1.4.1.9.2.1.54.0'
snmp_mib_variables['ciscoWriteMem'] = ciscoWriteMem


#
# Cisco SB devices, "Small Business" switches
# Only tested on CBS-350 switch.
#
# see https://mibs.observium.org/mib/CISCOSB-vlan-MIB/
# and https://github.com/librenms/librenms/blob/master/mibs/cisco/CISCOSB-vlan-MIB
# and all high-level entries at https://mibbrowser.online/mibdb_search.php?mib=CISCOSB-MIB

# see if the CISCOSB-vlan-MIB exists:
vlanMibVersion = '.1.3.6.1.4.1.9.6.1.101.48.1'
snmp_mib_variables['vlanMibVersion'] = vlanMibVersion

# vlan state, ie access, general, trunk
vlanPortModeState = '.1.3.6.1.4.1.9.6.1.101.48.22.1.1'
snmp_mib_variables['vlanPortModeState'] = vlanPortModeState
SB_VLAN_MODE_GENERAL = 10
SB_VLAN_MODE_ACCESS = 11
SB_VLAN_MODE_TRUNK = 12
sb_vlan_mode = {}
sb_vlan_mode[SB_VLAN_MODE_GENERAL] = "General"
sb_vlan_mode[SB_VLAN_MODE_ACCESS] = "Access"
sb_vlan_mode[SB_VLAN_MODE_TRUNK] = "Trunk"

# access mode ports set the vlan on this mib:
vlanAccessPortModeVlanId = '.1.3.6.1.4.1.9.6.1.101.48.62.1.1'
snmp_mib_variables['vlanAccessPortModeVlanId'] = vlanAccessPortModeVlanId
