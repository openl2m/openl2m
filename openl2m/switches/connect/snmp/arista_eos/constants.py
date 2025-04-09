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
"""constants.py defines Arista-specific SNMP-related variables. These are mostly MIB OIDs and their value definitions."""

from switches.connect.snmp.constants import snmp_mib_variables, enterprise_id_info

#
# Arista networks
#
ENTERPRISE_ID_ARISTA = 30065
enterprise_id_info[ENTERPRISE_ID_ARISTA] = 'Arista Networks'

# VRF info from https://www.arista.com/assets/data/docs/MIBS/ARISTA-VRF-MIB.txt
arista = "Enterprise 30065"
aristaMibs = "arista 3"
aristaVrfMIB = "aristaMibs 18"

aristaVrfMibObjects = "aristaVrfMIB 1"

aristaVrfTable = '.1.3.6.1.4.1.30065.3.18.1.1'  # "aristaVrfMibObjects 1"
snmp_mib_variables['aristaVrfTable'] = aristaVrfTable

aristaVrfEntry = '.1.3.6.1.4.1.30065.3.18.1.1.1'
snmp_mib_variables['aristaVrfEntry'] = aristaVrfEntry  # "aristaVrfTable 1", indexed by vrfName

aristaVrfName = '.1.3.6.1.4.1.30065.3.18.1.1.1.1'
snmp_mib_variables['aristaVrfName'] = aristaVrfName

aristaVrfRoutingStatus = '.1.3.6.1.4.1.30065.3.18.1.1.1.2'
snmp_mib_variables['aristaVrfRoutingStatus'] = aristaVrfRoutingStatus
# these are bit locations, if set IPv4 or 6 is enabled:
# VRF_ROUTING_IPV4 = 0
# VRF_ROUTING_IPV6 = 1
ARISTA_VRF_ROUTING_IPV4_BIT = 0x1
ARISTA_VRF_ROUTING_IPV6_BIT = 0x2

aristaVrfRouteDistinguisher = '.1.3.6.1.4.1.30065.3.18.1.1.1.3'
snmp_mib_variables['aristaVrfRouteDistinguisher'] = aristaVrfRouteDistinguisher

aristaVrfState = '.1.3.6.1.4.1.30065.3.18.1.1.1.4'
snmp_mib_variables['aristaVrfState'] = aristaVrfState

ARISTA_VRF_ACTIVE = 1
ARISTA_VRF_INACTIVE = 2


# the VRF IF Table entries have the lists of interfaces that are part of a VRF
# indexed by interface id, value is the VRF name:
# aristaVrfIfTable = aristaVrfMibObjects 2
# aristaVrfIfEntry = aristaVrfIfTable 1
# aristaVrfIfMembership = aristaVrfIfEntry 1

aristaVrfIfMembership = '.1.3.6.1.4.1.30065.3.18.1.2.1.1'
# eg:
# .1.3.6.1.4.1.30065.3.18.1.2.1.1.999001 = STRING: "MGMT"
# interface index 999001 is member of "MGMT"
snmp_mib_variables['aristaVrfIfMembership'] = aristaVrfIfMembership
