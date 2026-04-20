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

from .constants import sb_vlan_mode


def get_if_mode_name(mode: int):
    """return string representation of interface mode
    Args:
        mode (int): the (snmp) integer representing the mode, eg. SB_VLAN_MODE_ACCESS

    Returns:
        (str): string representation of the mode, include number of unknown.
    """

    if mode in sb_vlan_mode:
        return sb_vlan_mode[mode]
    return f"Unknown ({mode})"
