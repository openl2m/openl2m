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
# see more at https://oidref.com/1.3.111.2.802.1.1.4.1.4

# vlan names:
ieee8021QBridgeVlanStaticName = '.1.3.111.2.802.1.1.4.1.4.3.1.3.1'
snmp_mib_variables['ieee8021QBridgeVlanStaticName'] = ieee8021QBridgeVlanStaticName

# the PVID of a port is here.
# see also https://oidref.com/1.3.111.2.802.1.1.4.1.4.5.1.1
ieee8021QBridgePortVlanEntry = '.1.3.111.2.802.1.1.4.1.4.5.1'
snmp_mib_variables['ieee8021QBridgePortVlanEntry'] = ieee8021QBridgePortVlanEntry

# as of AOS-CX 10.08.1021 this is added to display port vlan membership:
# see also http://oid-info.com/get/1.3.6.1.4.1.11.2.14.11.5.1.9.4.2.1.4
hpSwitchPortFdbVidList = '.1.3.6.1.4.1.11.2.14.11.5.1.9.4.2.1.4'
snmp_mib_variables['hpSwitchPortFdbVidList'] = hpSwitchPortFdbVidList
