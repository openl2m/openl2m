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

#
# Dell
#
ENTERPRISE_ID_DELL = 674
enterprise_id_info[ENTERPRISE_ID_DELL] = 'Dell Networking'

# interface mode:
agentPortSwitchportMode = '1.3.6.1.4.1.674.10895.5000.2.6132.1.1.1.2.13.1.26'
snmp_mib_variables['agentPortSwitchportMode'] = agentPortSwitchportMode
DELL_PORT_MODE_ACCESS = 1
DELL_PORT_MODE_TRUNK = 2
DELL_PORT_MODE_GENERAL = 3

# untagged aka native vlan id
"""Describes and Configures the VLAN ID of Trunk switch port.
Configures the Native VLAN Id for the port."""
agentPortNativeVlanID = '1.3.6.1.4.1.674.10895.5000.2.6132.1.1.1.2.13.1.46'
snmp_mib_variables['agentPortNativeVlanID'] = agentPortNativeVlanID

"""Describes and Configures the VLAN ID of access switch port.
A value of 0 indicates that  the switch port is not configured as
access port."""
agentPortAccessVlanID = '1.3.6.1.4.1.674.10895.5000.2.6132.1.1.1.2.13.1.43'
snmp_mib_variables['agentPortAccessVlanID'] = agentPortAccessVlanID

"""This field contains all the ports which include the VLAN for Trunk mode.
format is ProtectedPortList"""
agentVlanSwitchportTrunkStaticEgressPorts = '1.3.6.1.4.1.674.10895.5000.2.6132.1.1.1.2.23.1.1.1'
snmp_mib_variables['agentVlanSwitchportTrunkStaticEgressPorts'] = agentVlanSwitchportTrunkStaticEgressPorts

"""enable(1) will initiate an configuration save to nvram.
Status is returned by the object agentSaveConfigStatus."""
agentSaveConfig = '1.3.6.1.4.1.674.10895.5000.2.6132.1.1.1.3.1'
snmp_mib_variables['agentSaveConfig'] = agentSaveConfig
DELL_SAVE_ENABLE = 1

"""Indicates the current status of an save configuration request."""
agentSaveConfigStatus = '1.3.6.1.4.1.674.10895.5000.2.6132.1.1.1.3.11'
snmp_mib_variables['agentSaveConfigStatus'] = agentSaveConfigStatus
DELL_SAVING_NOT_INITIATED = 1
DELL_SAVING_IN_PROGRESS = 2
DELL_SAVING_COMPLETE = 3
DELL_SAVING_FAILED = 4
