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
# from switches.utils import dprint

#
# Arista specific utility functions
#


def get_vlan_and_interface_from_string(if_string: str):
    """Parse the Arista "Vlan, Interface" format into vlan id and interface.

    Args:
        if_string (str): the string with vlan and interface info.

    Returns:
        (vlan_id, if_name): vlan ID(int) and interface name (str)
    """
    # parse "Vlxxxx, Interface"
    # note: the IPv4 arp by vrf info starts with "Vlanxxxx",
    # whereasthe Ipv6 ND info starts with "Vlxxxx"
    if if_string.startswith("Vlan"):
        # Ipv4 Vlan format:
        (vlan_str, if_name) = if_string[4:].split(",")
    elif if_string.startswith("Vl"):  # short IPv6 ND format:
        (vlan_str, if_name) = if_string[2:].split(",")
    else:  # no vlan info, plain "Ethernet1/1" format:
        vlan_str = -1
        # in IPV6 ND, when no vlan found, the interface name is abreviated to "Etx/y", so expand this:
        if if_string[2:3].isdigit():
            if_name = if_string.replace("Et", "Ethernet")
        else:
            if_name = if_string

    return (int(vlan_str), if_name.strip())
