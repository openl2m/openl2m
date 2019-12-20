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

# here we defined mappings from SNMP Enterprise Id to Company Name
# specific entries for supported vendors are in their implementation
# directories, eg. vendors/procurve/constants.py, vendors/cisco/constants.py...

#
# Juniper
ENTERPRISE_ID_JUNIPER = 2636
# generic Net-SNMP installed snmpd
ENTERPRISE_ID_NETSNMP = 8072
# a test cheap test switch used
ENTERPRISE_ID_PLANET = 10456

enterprise_id_info = {}
enterprise_id_info[ENTERPRISE_ID_JUNIPER] = 'Juniper'
enterprise_id_info[ENTERPRISE_ID_NETSNMP] = 'Generic Net-SNMP'
enterprise_id_info[ENTERPRISE_ID_PLANET] = 'PLANET Technology Corp.'
