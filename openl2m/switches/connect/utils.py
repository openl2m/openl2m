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
import re
from switches.utils import dprint

"""
This file contains general utility functions
"""


def interface_name_to_long(name: str) -> str:
    # convert a short interface name, Gi0/1, Te1/0/1, etc.
    # to their equivalent long names GigabitEthernet0/1, TenGigabitEthernet1/0/1, etc.
    dprint(f"interface_name_to_long() for {name}")
    # regex to get all characters before the first number
    match = re.search('^([a-zA-Z ]*)(\d.*)$', name)
    if match:
        dprint("   match found")
        if match.group(1).lower() == 'fa':
            newname = f"FastEthernet{match.group(2)}"
        elif match.group(1).lower() == 'gi':
            newname = f"GigabitEthernet{match.group(2)}"
        elif match.group(1).lower() == 'te':
            newname = f"TenGigabitEthernet{match.group(2)}"
        elif match.group(1).lower() == 'fo':
            newname = f"FourtyGigabitEthernet{match.group(2)}"
        elif match.group(1).lower() == 'hu':
            newname = f"HundredGigabitEthernet{match.group(2)}"
        elif match.group(1).lower() == 'po':
            newname = f"Port-channel{match.group(2)}"
        # Hmm, some unknow interface format? return name again?
        else:
            newname = name
        dprint(f"   New = {newname}")
        return newname
    else:
        # no match, just return original
        dprint("   NO match found")
        return name
