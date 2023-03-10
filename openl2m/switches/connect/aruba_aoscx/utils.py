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

from switches.connect.constants import IF_DUPLEX_UNKNOWN, IF_DUPLEX_HALF, IF_DUPLEX_FULL


def aoscx_parse_duplex(duplex):
    '''
    Convert a duplex string to an integer with the proper duplex meaning.

    Args:
        duplex(str): a string representing a duplex setting

    Returns:
        (int) duplex value as IF_DUPLEX_UNKNOWN, IF_DUPLEX_FULL or IF_DUPLEX_HALF
    '''
    if not isinstance(duplex, str):
        return IF_DUPLEX_UNKNOWN

    full_duplex = ['full']
    if duplex.lower() in full_duplex:
        return IF_DUPLEX_FULL

    half_duplex = ['half']
    if duplex.lower() in half_duplex:
        return IF_DUPLEX_HALF

    return IF_DUPLEX_UNKNOWN
