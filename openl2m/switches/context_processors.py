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
# see https://stackoverflow.com/questions/433162/can-i-access-constants-in-settings-py-from-templates-in-django

#
# register variables to be "globally" available in templates
#

from django.conf import settings as mysettings
from switches.constants import *
from switches.connect.constants import *


def add_variables(request):
    # the list of variables and constants that need to be available in all templates
    return {
        'IF_ADMIN_STATUS_UP': IF_ADMIN_STATUS_UP,
        'IF_ADMIN_STATUS_DOWN': IF_ADMIN_STATUS_DOWN,
        'IF_OPER_STATUS_UP': IF_OPER_STATUS_UP,
        'IF_OPER_STATUS_DOWN': IF_OPER_STATUS_DOWN,
        'IF_TYPE_ETHERNET': IF_TYPE_ETHERNET,
        'IF_TYPE_LAGG': IF_TYPE_LAGG,

        'VLAN_TYPE_NORMAL': VLAN_TYPE_NORMAL,
        'VLAN_STATUS_DYNAMIC': VLAN_STATUS_DYNAMIC,

        'GVRP_ENABLED': GVRP_ENABLED,

        'POE_PORT_ADMIN_ENABLED': POE_PORT_ADMIN_ENABLED,
        'POE_PORT_ADMIN_DISABLED': POE_PORT_ADMIN_DISABLED,
        'POE_PORT_DETECT_DELIVERING': POE_PORT_DETECT_DELIVERING,

        'BULKEDIT_POE_CHOICES': BULKEDIT_POE_CHOICES,
        'BULKEDIT_INTERFACE_CHOICES': BULKEDIT_INTERFACE_CHOICES,
        'BULKEDIT_ALIAS_TYPE_CHOICES': BULKEDIT_ALIAS_TYPE_CHOICES,

        'CAPABILITIES_QBRIDGE_MIB': CAPABILITIES_QBRIDGE_MIB,
        'CAPABILITIES_LLDP_MIB': CAPABILITIES_LLDP_MIB,
        'CAPABILITIES_POE_MIB': CAPABILITIES_POE_MIB,
        'CAPABILITIES_NET2MEDIA_MIB': CAPABILITIES_NET2MEDIA_MIB,
        'CAPABILITIES_NET2PHYS_MIB': CAPABILITIES_NET2PHYS_MIB,
        'CAPABILITIES_CISCO_VTP_MIB': CAPABILITIES_CISCO_VTP_MIB,
        'CAPABILITIES_CISCO_POE_MIB': CAPABILITIES_CISCO_POE_MIB,
        'CAPABILITIES_CISCO_STACK_MIB': CAPABILITIES_CISCO_STACK_MIB,

        'SWITCH_STATUS_ACTIVE': SWITCH_STATUS_ACTIVE,
        'SWITCH_VIEW_BASIC': SWITCH_VIEW_BASIC,

        'ENTITY_CLASS_NAME': ENTITY_CLASS_NAME,

        'LOG_TYPE_VIEW': LOG_TYPE_VIEW,
        'LOG_TYPE_CHANGE': LOG_TYPE_CHANGE,
        'LOG_TYPE_WARNING': LOG_TYPE_WARNING,
        'LOG_TYPE_ERROR': LOG_TYPE_ERROR,
        'LOG_TYPE_COMMAND': LOG_TYPE_COMMAND,

        'LOG_TYPE_CHOICES': LOG_TYPE_CHOICES,

        'TASK_STATUS_SCHEDULED': TASK_STATUS_SCHEDULED,
        'TASK_STATUS_RUNNING': TASK_STATUS_RUNNING,

        'settings': mysettings,
    }
