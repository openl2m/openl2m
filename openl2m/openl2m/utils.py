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

# various utility function for this project


def mangle_dict_keys(data):
    """mangle the keys of this data dictionary to lower-case string with spaces as underscores.
    Used to make API keys 'machine' version instead of human names.
    """
    return_dict = {}
    for key, value in data.items():
        return_dict[str(key).replace(' ', '_').lower()] = value
    return return_dict
