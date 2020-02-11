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

#
# HP-ProCurve / Aruba
#
ENTERPRISE_ID_HP = 11
enterprise_id_info[ENTERPRISE_ID_HP] = 'HP/Aruba'

# SOME SWITCHES IMPLEMENTE THIS:
# http://www.circitor.fr/Mibs/Html/H/HPN-ICF-CONFIG-MAN-MIB.php
hpnicfConfigManObjects = '.1.3.6.1.4.1.11.2.14.11.15.2.4.1'
snmp_mib_variables['hpnicfConfigManObjects'] = hpnicfConfigManObjects
# start of some good information:
hpnicfCfgLog = '.1.3.6.1.4.1.11.2.14.11.15.2.4.1.1'
snmp_mib_variables['hpnicfCfgLog'] = hpnicfCfgLog
# The object records the value of sysUpTime when the current configuration running in the system was last modified.
# The value will be changed immediately after system detects the current configuration has been changed.
hpnicfCfgRunModifiedLast = '.1.3.6.1.4.1.11.2.14.11.15.2.4.1.1.1'
snmp_mib_variables['hpnicfCfgRunModifiedLast'] = hpnicfCfgRunModifiedLast
# The object records the value of sysUpTime when the current configuration running in the system was last saved.
# If the value of the object is smaller than hpnicfCfgRunModifiedLast,
# the current configuration has been modified but not saved.
hpnicfCfgRunSavedLast = '.1.3.6.1.4.1.11.2.14.11.15.2.4.1.1.2'
snmp_mib_variables['hpnicfCfgRunSavedLast'] = hpnicfCfgRunSavedLast

# HP If Extention mib: HPN-ICF-IF-EXT-MIB
# http://www.circitor.fr/Mibs/Html/H/HPN-ICF-IF-EXT-MIB.php
hpnicfIfLinkMode = '.1.3.6.1.4.1.11.2.14.11.15.2.40.2.2.3.1.1'
snmp_mib_variables['hpnicfIfLinkMode'] = hpnicfIfLinkMode
# bridgeMode(1), routeMode(2)
HP_BRIDGE_MODE = 1
HP_ROUTE_MODE = 2

# SOME SWITCHES IMPLEMENT THIS:
# see http://www.circitor.fr/Mibs/Html/H/HP-ICF-POE-MIB.php
hpicfPOE = '.1.3.6.1.4.1.11.2.14.11.1.9'

hpicfPoePethPsePortCurrent = '.1.3.6.1.4.1.11.2.14.11.1.9.1.1.1.1'

hpicfPoePethPsePortVoltage = '.1.3.6.1.4.1.11.2.14.11.1.9.1.1.1.2'

# This field specifies the Power supplied at this port.
# This value is specified in milliwatts (mW).
hpicfPoePethPsePortPower = '.1.3.6.1.4.1.11.2.14.11.1.9.1.1.1.3'
snmp_mib_variables['hpicfPoePethPsePortPower'] = hpicfPoePethPsePortPower

hpicfPoePethPsePortActualPower = '.1.3.6.1.4.1.11.2.14.11.1.9.1.1.1.8'
snmp_mib_variables['hpicfPoePethPsePortActualPower'] = hpicfPoePethPsePortActualPower


# SOME DEVICE MAY IMPLEMENT THIS:
# HP-ENTITY-POWER-MIB
# see http://www.circitor.fr/Mibs/Html/H/HP-ENTITY-POWER-MIB.php
hpEntityPowerMIB = '.1.3.6.1.4.1.11.2.14.11.5.1.71'

hpEntPowerCurrentPowerUsage = '.1.3.6.1.4.1.11.2.14.11.5.1.71.1.1.1.3'
snmp_mib_variables['hpEntPowerCurrentPowerUsage'] = hpEntPowerCurrentPowerUsage
