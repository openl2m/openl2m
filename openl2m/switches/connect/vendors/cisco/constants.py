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

from switches.connect.constants import snmp_mib_variables
from switches.connect.vendors.constants import enterprise_id_info

# Cisco specific constants
ENTERPRISE_ID_CISCO = 9
enterprise_id_info[ENTERPRISE_ID_CISCO] = 'Cisco'

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
VTP_VLAN_STATE = '.1.3.6.1.4.1.9.9.46.1.3.1.1.2.1'
snmp_mib_variables['vtpVlanState'] = VTP_VLAN_STATE

VTP_VLAN_TYPE = '.1.3.6.1.4.1.9.9.46.1.3.1.1.3.1'
snmp_mib_variables['vtpVlanType'] = VTP_VLAN_TYPE

VLAN_TYPE_NORMAL = 1     # regular(1)
VLAN_TYPE_FDDI = 2       # fddi(2)
VLAN_TYPE_TOKENRING = 3  # tokenRing(3)
VLAN_TYPE_FDDINET = 4    # fddiNet(4)
VLAN_TYPE_TRNET = 5      # trNet(5)

VTP_VLAN_NAME = '.1.3.6.1.4.1.9.9.46.1.3.1.1.4.1'
snmp_mib_variables['vtpVlanName'] = VTP_VLAN_NAME
# VTP trunk ports start at .1.3.6.1.4.1.9.9.46.1.6
# details about ports start at .1.3.6.1.4.1.9.9.46.1.6.1.1

VTP_PORT_TRUNK_NATIVE_VLAN = '.1.3.6.1.4.1.9.9.46.1.6.1.1.5'
snmp_mib_variables['vlanTrunkPortNativeVlan'] = VTP_PORT_TRUNK_NATIVE_VLAN

VTP_PORT_TRUNK_DYNAMIC_STATE = '.1.3.6.1.4.1.9.9.46.1.6.1.1.13'
snmp_mib_variables['vlanTrunkPortDynamicState'] = VTP_PORT_TRUNK_DYNAMIC_STATE
VTP_TRUNK_STATE_ON = 1
VTP_TRUNK_STATE_OFF = 2
VTP_TRUNK_STATE_DESIRED = 3
VTP_TRUNK_STATE_AUTO = 4
VTP_TRUNK_STATE_NO_NEGOTIATE = 5

# actual trunk status, result of the vlanTrunkPortDynamicState and the ifOperStatus of the trunk port itself
# ie when port is down, this shows DISABLED!!!
VTP_PORT_TRUNK_DYNAMIC_STATUS = '.1.3.6.1.4.1.9.9.46.1.6.1.1.14'
snmp_mib_variables['vlanTrunkPortDynamicStatus'] = VTP_PORT_TRUNK_DYNAMIC_STATUS
VTP_PORT_TRUNK_ENABLED = 1
VTP_PORT_TRUNK_DISABLED = 2

# this is the untagged or native vlan for a Cisco switch port
# this will NOT show ports in trunk mode!!!
VTP_UNTAGGED_MEMBERSHIP_VLAN = '.1.3.6.1.4.1.9.9.68.1.2.2.1.2'
snmp_mib_variables['vmVlan'] = VTP_UNTAGGED_MEMBERSHIP_VLAN

# this is the Cisco "Voice" Vlan
CISCO_VOICE_VLAN = '.1.3.6.1.4.1.9.9.68.1.5.1.1.1'
snmp_mib_variables['vmVoiceVlanId'] = CISCO_VOICE_VLAN


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
CISCO_EXT_POE_MIB = '.1.3.6.1.4.1.9.9.402'
snmp_mib_variables['ciscoPowerEthernetExtMIB'] = CISCO_EXT_POE_MIB

CISCO_POE_PORT_POWER_ALLOCATED = '.1.3.6.1.4.1.9.9.402.1.2.1.7'
snmp_mib_variables['cpeExtPsePortPwrAllocated'] = CISCO_POE_PORT_POWER_ALLOCATED

CISCO_POE_PORT_POWER_AVAILABLE = '.1.3.6.1.4.1.9.9.402.1.2.1.8'
snmp_mib_variables['cpeExtPsePortPwrAvailable'] = CISCO_POE_PORT_POWER_AVAILABLE

CISCO_POE_PORT_POWER_CONSUMED = '.1.3.6.1.4.1.9.9.402.1.2.1.9'
snmp_mib_variables['cpeExtPsePortPwrConsumption'] = CISCO_POE_PORT_POWER_CONSUMED

CISCO_POE_PORT_MAX_POWER_CONSUMED = '.1.3.6.1.4.1.9.9.402.1.2.1.10'
snmp_mib_variables['cpeExtPsePortMaxPwrDrawn'] = CISCO_POE_PORT_MAX_POWER_CONSUMED

# CISCO-STACK-MIB contains various mappings
CISCO_STACK_MIB = '.1.3.6.1.4.1.9.5.1'
snmp_mib_variables['ciscoStackMIB'] = CISCO_STACK_MIB
# this maps a Cisco port # to a standard if_index:
CISCO_PORT_IF_INDEX = '.1.3.6.1.4.1.9.5.1.4.1.1.11'
snmp_mib_variables['portIfIndex'] = CISCO_PORT_IF_INDEX


# OID to "write mem" via Snmp
CISCO_WRITE_MEM = '.1.3.6.1.4.1.9.2.1.54.0'
snmp_mib_variables['ciscoWriteMem'] = CISCO_WRITE_MEM
