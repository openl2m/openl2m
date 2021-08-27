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
