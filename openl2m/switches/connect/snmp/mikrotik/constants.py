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
"""constants.py defines Mikrotik-specific SNMP-related variables. These are mostly MIB OIDs and their value definitions."""


from switches.connect.snmp.constants import snmp_mib_variables, enterprise_id_info

ENTERPRISE_ID_MIKROTIK = 14988
enterprise_id_info[ENTERPRISE_ID_MIKROTIK] = 'MikroTik'

#
# mikrotik mib found at https://mibs.observium.org/mib/MIKROTIK-MIB/
#
# mtxrPOE = '.1.3.6.1.4.1.14988.1.1.15'
# mtxrPOETable = '.1.3.6.1.4.1.14988.1.1.15.1'
mtxrPOEEntry = '.1.3.6.1.4.1.14988.1.1.15.1.1'
snmp_mib_variables['mtxrPOEEntry'] = mtxrPOEEntry

# this maps the POE index "...15.1.1.1.x" = ifIndex
mtxrPOEInterfaceIndex = '.1.3.6.1.4.1.14988.1.1.15.1.1.1'
snmp_mib_variables['mtxrPOEInterfaceIndex'] = mtxrPOEInterfaceIndex
# this just provides the interface name (we already know this from ifIndex branch):
mtxrPOEName = '.1.3.6.1.4.1.14988.1.1.15.1.1.2'
snmp_mib_variables['mtxrPOEName'] = mtxrPOEName

mtxrPOEStatus = '.1.3.6.1.4.1.14988.1.1.15.1.1.3'
snmp_mib_variables['mtxrPOEStatus'] = mtxrPOEStatus
MIKROTIK_POE_DISABLED = 1
MIKROTIK_POE_WAITINGFORLOAD = 2
MIKROTIK_POE_POWEREDON = 3
# everything 4 and above is error
MIKROTIK_POE_ERRORS = 4
# overload(4),
# shortCircuit(5),
# voltageTooLow(6),
# currentTooLow(7),
# powerReset(8),
# voltageTooHigh(9),
# controllerError(10),
# controllerUpgrade(11),
# poeInDetected(12),
# noValidPsu(13),
# controllerInit(14),
# lowVoltageTooLow(15)

mtxrPOEVoltage = '.1.3.6.1.4.1.14988.1.1.15.1.1.4'
snmp_mib_variables['mtxrPOEVoltage'] = mtxrPOEVoltage

mtxrPOECurrent = '.1.3.6.1.4.1.14988.1.1.15.1.1.5'
snmp_mib_variables['mtxrPOECurrent'] = mtxrPOECurrent

mtxrPOEPower = '.1.3.6.1.4.1.14988.1.1.15.1.1.6'
snmp_mib_variables['mtxrPOEPower'] = mtxrPOEPower
