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
from switches.connect.classes import Interface

"""
This file contains general utility functions
"""


def interface_name_to_long(name: str) -> str:
    # convert a short interface name, Gi0/1, Te1/0/1, etc.
    # to their equivalent long names GigabitEthernet0/1, TenGigabitEthernet1/0/1, etc.
    dprint(f"interface_name_to_long() for {name}")
    # regex to get all characters before the first number
    match = re.search(r'^([a-zA-Z ]*)(\d.*)$', name)
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


def standardize_ipv4_subnet(ip: str) -> str:
    """Expand an IPv4 address in the form of x/y, x.x/y, or x.x.x/y to x.x.x.x/y
    Args:
        ip (str): string representing an ipv4 subnet

    Returns:
        (str):  standardazied format, or original value if not matching.
    """
    dprint(f"standardize_ipv4_subnet({ip})")

    # match normal format 10.1.2.0/24
    if re.match(r"^(\d+)\.(\d+)\.(\d+)\.(\d+)\/(\d+)", ip):
        dprint("  Normal IP found!")
        return ip
    # match 10.1.2/x
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)\/(\d+)", ip)
    if m:
        dprint("  3-digit IP found!")
        return f"{m.group(1)}.{m.group(2)}.{m.group(3)}.0/{m.group(4)}"
    # match 10.1/x
    m = re.match(r"^(\d+)\.(\d+)\/(\d+)", ip)
    if m:
        dprint("  2-digit IP found!")
        return f"{m.group(1)}.{m.group(2)}.0.0/{m.group(3)}"
    # match 10/x
    m = re.match(r"^(\d+)\/(\d+)", ip)
    if m:
        dprint("  1-digit IP found!")
        return f"{m.group(1)}.0.0.0/{m.group(2)}"
    # this does not look like an IPv4 address:
    dprint("    NO valid IPv4 match!")
    return ip


def get_vlan_id_from_l3_interface(iface: Interface) -> int:
    """See if this interfaces is a routed vlan interface,
       and parse the vlan-id from it.

    Args:
        iface (Interface): the Interface() we are looking at

    Return:
        (int):  the Vlan ID for this routed (L3) interface, or -1 if not found.
    """
    # Comware format:
    m = re.match(r"^vlan-interface(\d+)", iface.name.lower())
    if m:
        vlan_id = int(m.group(1))
        dprint(f"get_vlan_id_from_l3_interface() found Comware vlan {vlan_id}")
        return vlan_id
    # Cisco format:
    m = re.match(r"^vlan(\d+)", iface.name.lower())
    if m:
        vlan_id = int(m.group(1))
        dprint(f"get_vlan_id_from_l3_interface() found Cisco vlan {vlan_id}")
        return vlan_id
    # not found
    return -1
