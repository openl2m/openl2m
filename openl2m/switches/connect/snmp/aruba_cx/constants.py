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
# Aruba 'new style' devices
#
ENTERPRISE_ID_HP_ENTERPRISE = 47196
# Note: this is registered as 'Hewlett Packard Enterprise',
# but now doing business as Aruba.
enterprise_id_info[ENTERPRISE_ID_HP_ENTERPRISE] = 'Aruba (HPE)'

# AOS-CX uses the ieee QBridge Mibs for vlan info (ieee8021QBridgeVlan)
# defind in switches.connect.snmp.constants.*
# see more at https://oidref.com/1.3.111.2.802.1.1.4.1.4

# AOS-CX also uses numerous HP/ProCurve snmp counters.
# this are defined in switches.connect.snmp.procurve.constants

# the ARUBAWIRED-POE mib is used for PoE reporting:
# see http://www.circitor.fr/Mibs/Html/A/ARUBAWIRED-POE-MIB.php

# the power drawn, in milliwatts:
arubaWiredPoePethPsePortPowerDrawn = '.1.3.6.1.4.1.47196.4.1.1.3.8.1.1.1.7'
snmp_mib_variables['arubaWiredPoePethPsePortPowerDrawn'] = arubaWiredPoePethPsePortPowerDrawn
