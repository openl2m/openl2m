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
# Juniper Networks
#
ENTERPRISE_ID_JUNIPER = 2636
enterprise_id_info[ENTERPRISE_ID_JUNIPER] = 'Juniper Networks'


# Juniper specific VLAN related entries:
# http://www.circitor.fr/Mibs/Html/J/JUNIPER-L2ALD-MIB.php
jnxL2aldVlanEntry = '.1.3.6.1.4.1.2636.3.48.1.3.1.1'
snmp_mib_variables['jnxL2aldVlanEntry'] = jnxL2aldVlanEntry

jnxL2aldVlanID = '.1.3.6.1.4.1.2636.3.48.1.3.1.1.1'
snmp_mib_variables['jnxL2aldVlanID'] = jnxL2aldVlanID

jnxL2aldVlanName = '.1.3.6.1.4.1.2636.3.48.1.3.1.1.2'
snmp_mib_variables['jnxL2aldVlanName'] = jnxL2aldVlanName

jnxL2aldVlanTag = '.1.3.6.1.4.1.2636.3.48.1.3.1.1.3'
snmp_mib_variables['jnxL2aldVlanTag'] = jnxL2aldVlanTag

jnxL2aldVlanType = '.1.3.6.1.4.1.2636.3.48.1.3.1.1.4'
snmp_mib_variables['jnxL2aldVlanType'] = jnxL2aldVlanType
JNX_VLAN_TYPE_STATIC = 1
JNX_VLAN_TYPE_DYNAMIC = 2

jnxL2aldVlanType = '.1.3.6.1.4.1.2636.3.48.1.3.1.1.4'
snmp_mib_variables['jnxL2aldVlanType'] = jnxL2aldVlanType
# see above for static/dynamic

# see https://kb.juniper.net/InfoCenter/index?page=content&id=KB32532&actp=METADATA
# this is the filter database for a specific vlan.
#  jnxL2aldVlanFdbId.VLAN-INDEX = Filter-DB-Index
jnxL2aldVlanFdbId = '.1.3.6.1.4.1.2636.3.48.1.3.1.1.5'
snmp_mib_variables['jnxL2aldVlanFdbId'] = jnxL2aldVlanFdbId

# THESE ARE OBSOLETE!!!
# https://circitor.fr/Mibs/Html/J/JUNIPER-VLAN-MIB.php
# Layer 2:
jnxVlanTable = '.1.3.6.1.4.1.2636.3.40.1.5.1.1'
# Layer 3 is below this:
jnxVlanInterfaceTable = '.1.3.6.1.4.1.2636.3.40.1.5.1.2'
