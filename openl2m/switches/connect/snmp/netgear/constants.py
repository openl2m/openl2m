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
# Netgear
#
ENTERPRISE_ID_NETGEAR = 4526
enterprise_id_info[ENTERPRISE_ID_NETGEAR] = 'Netgear'

# https://kb.netgear.com/24352/MIBs-for-Smart-switches
# All netgear mibs browsable:
# https://www.oidview.com/mibs/4526/md-4526-1.html


# NETGEAR-POWER-ETHERNET-MIB - Private POE MIB
# https://mibs.observium.org/mib/NETGEAR-POWER-ETHERNET-MIB/

#  fastPathpowerEthernetMIB		           .1.3.6.1.4.1.4526.10.15
#  agentPethObjects		                .1.3.6.1.4.1.4526.10.15.1
#  agentPethPsePortTable 		        .1.3.6.1.4.1.4526.10.15.1.1
#  agentPethPsePortEntry 		        .1.3.6.1.4.1.4526.10.15.1.1.1
#  agentPethPowerLimit 	Milliwatts	    .1.3.6.1.4.1.4526.10.15.1.1.1.1
#  agentPethOutputPower 	Milliwatts	.1.3.6.1.4.1.4526.10.15.1.1.1.2
#  agentPethOutputCurrent 	Milliamps	.1.3.6.1.4.1.4526.10.15.1.1.1.3
#  agentPethOutputVolts 	Millivolts	.1.3.6.1.4.1.4526.10.15.1.1.1.4
#  agentPethTemperature 	DEGREES	    .1.3.6.1.4.1.4526.10.15.1.1.1.5
#  agentPethPowerLimitType 		        .1.3.6.1.4.1.4526.10.15.1.1.1.6
#  agentPethHighPowerEnable (obsolete)  .1.3.6.1.4.1.4526.10.15.1.1.1.7
#  agentPethPowerDetectionType 		    .1.3.6.1.4.1.4526.10.15.1.1.1.8
#  agentPethFaultStatus 		        .1.3.6.1.4.1.4526.10.15.1.1.1.9
#  agentPethPortReset 		            .1.3.6.1.4.1.4526.10.15.1.1.1.10
#  agentPethPowerUpMode 		        .1.3.6.1.4.1.4526.10.15.1.1.1.11
#  agentPethClassificationMode 		    .1.3.6.1.4.1.4526.10.15.1.1.1.12

agentPethOutputPower = '.1.3.6.1.4.1.4526.10.15.1.1.1.2'  # in milliWatts
snmp_mib_variables['agentPethOutputPower'] = agentPethOutputPower

# Power Supply objects
#  agentPethMainPseObjects		.1.3.6.1.4.1.4526.10.15.1.2
#  agentPethMainPseTable 		.1.3.6.1.4.1.4526.10.15.1.2.1
#  agentPethMainPseEntry 		.1.3.6.1.4.1.4526.10.15.1.2.1.1
#  agentPethMainPseLegacy 		.1.3.6.1.4.1.4526.10.15.1.2.1.1.1
#  agentPethPseTable 		.1.3.6.1.4.1.4526.10.15.1.3
#  agentPethPseEntry 		.1.3.6.1.4.1.4526.10.15.1.3.1
#  agentPethPsePowerManagementMode 		.1.3.6.1.4.1.4526.10.15.1.3.1.1
#  agentPethPseAutoResetEnable 		.1.3.6.1.4.1.4526.10.15.1.3.1.2
#  agentPethPseThresholdPower 	Watts	.1.3.6.1.4.1.4526.10.15.1.3.1.6
#  agentPethPoeMainPseObjects		.1.3.6.1.4.1.4526.10.15.1.4
#  agentPethPoeMainPseTable 		.1.3.6.1.4.1.4526.10.15.1.4.1
#  agentPethPoeMainPseEntry 		.1.3.6.1.4.1.4526.10.15.1.4.1.1
#  agentPethPoeMainPseGroupIndex 		.1.3.6.1.4.1.4526.10.15.1.4.1.1.1
#  agentPethPoePseCardModel 		.1.3.6.1.4.1.4526.10.15.1.4.1.1.10
#  agentPethPoePseCardHost 		.1.3.6.1.4.1.4526.10.15.1.4.1.1.11
#  agentPethPoePseCardStatus 		.1.3.6.1.4.1.4526.10.15.1.4.1.1.12
#  agentPethPoeMainPseSlotIndex 		.1.3.6.1.4.1.4526.10.15.1.4.1.1.2
#  agentPethPoeMainPsePower 	Watts	.1.3.6.1.4.1.4526.10.15.1.4.1.1.3
#  agentPethPoeMainPseOperStatus 		.1.3.6.1.4.1.4526.10.15.1.4.1.1.4
#  agentPethPoeMainPseThresholdPower 	Watts deprecated	.1.3.6.1.4.1.4526.10.15.1.4.1.1.5
#  agentPethPoeMainPseConsumptionPower 	Milliwatts	.1.3.6.1.4.1.4526.10.15.1.4.1.1.6
#  agentPethPoeMainPseUsageThreshold 	% deprecated	.1.3.6.1.4.1.4526.10.15.1.4.1.1.7
#  agentPethPoeMainPseFWImageVersion 		.1.3.6.1.4.1.4526.10.15.1.4.1.1.8
#  agentPethPoePsePowerManagementMode 		.1.3.6.1.4.1.4526.10.15.1.4.1.1.9

# .1.3.6.1.4.1.4526.11.16.1.1.1.3.1
