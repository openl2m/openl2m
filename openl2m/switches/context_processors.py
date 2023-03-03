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
import switches.constants as constants
import switches.connect.constants as if_constants


def add_variables(request):
    # the list of variables and constants that need to be available in all templates
    return {
        'IF_TYPE_NONE': if_constants.IF_TYPE_NONE,
        'IF_TYPE_ETHERNET': if_constants.IF_TYPE_ETHERNET,
        'IF_TYPE_LAGG': if_constants.IF_TYPE_LAGG,
        'IF_TYPE_VIRTUAL': if_constants.IF_TYPE_VIRTUAL,
        'IF_TYPE_LOOPBACK': if_constants.IF_TYPE_LOOPBACK,
        'IF_TYPE_TUNNEL': if_constants.IF_TYPE_TUNNEL,
        'IF_TYPE_MCAST': if_constants.IF_TYPE_MCAST,

        'LACP_IF_TYPE_NONE': if_constants.LACP_IF_TYPE_NONE,

        'VLAN_TYPE_NORMAL': if_constants.VLAN_TYPE_NORMAL,
        'VLAN_STATUS_DYNAMIC': if_constants.VLAN_STATUS_DYNAMIC,

        'GVRP_ENABLED': if_constants.GVRP_ENABLED,

        'POE_PORT_ADMIN_ENABLED': if_constants.POE_PORT_ADMIN_ENABLED,
        'POE_PORT_ADMIN_DISABLED': if_constants.POE_PORT_ADMIN_DISABLED,
        'POE_PORT_DETECT_DELIVERING': if_constants.POE_PORT_DETECT_DELIVERING,

        'BULKEDIT_POE_CHOICES': constants.BULKEDIT_POE_CHOICES,
        'BULKEDIT_INTERFACE_CHOICES': constants.BULKEDIT_INTERFACE_CHOICES,
        'BULKEDIT_ALIAS_TYPE_CHOICES': constants.BULKEDIT_ALIAS_TYPE_CHOICES,

        'SWITCH_STATUS_ACTIVE': constants.SWITCH_STATUS_ACTIVE,
        'SWITCH_VIEW_BASIC': constants.SWITCH_VIEW_BASIC,

        'ENTITY_CLASS_NAME': if_constants.ENTITY_CLASS_NAME,

        'LOG_TYPE_VIEW': constants.LOG_TYPE_VIEW,
        'LOG_TYPE_CHANGE': constants.LOG_TYPE_CHANGE,
        'LOG_TYPE_WARNING': constants.LOG_TYPE_WARNING,
        'LOG_TYPE_ERROR': constants.LOG_TYPE_ERROR,
        'LOG_TYPE_COMMAND': constants.LOG_TYPE_COMMAND,

        'LOG_TYPE_CHOICES': constants.LOG_TYPE_CHOICES,

        'TASK_STATUS_SCHEDULED': constants.TASK_STATUS_SCHEDULED,
        'TASK_STATUS_RUNNING': constants.TASK_STATUS_RUNNING,

        'settings': mysettings,
    }
