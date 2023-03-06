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

from switches.connect.constants import IF_TYPE_NONE, IF_TYPE_ETHERNET, IF_TYPE_LOOPBACK, IF_TYPE_VIRTUAL, IF_TYPE_TUNNEL, IF_TYPE_MCAST


def junos_speed_to_mbps(speed):
    '''
    Convert speed string to integer in 1Mbps

    Args:
        speed(str): a string representing interface speed in Mbps

    Returns:
        (int) the speed in Mbps as an integer
    '''
    if speed == '0':    # special case, for speeds like "Unlimited" on virtual and backplane interfaces, etc.
        return 0
    speed = speed.lower()
    if speed.endswith('mbps'):
        return int(speed.replace('mbps', ''))
    if speed.endswith('gbps'):
        return int(speed.replace('gbps', '000'))
    if speed.endswith('tbps'):      # future-proofing :-)
        return int(speed.replace('tbps', '000000'))
    # unknown, return as 0
    return 0


def junos_parse_power(power, milliwatts=False):
    '''
    Convert a power string to an integer in Watts or milliWatts.

    Args:
        power(str): a string representing interface power in Watts or milliWatts
        milliwatts(boolean): if true, power is in mW, other in W.

    Returns:
        (int) power as an integer
    '''
    if power.endswith('W'):
        # power is something like "12.3W"
        power = float(power.replace('W', ''))
        if milliwatts:
            power = power * 1000
        return int(power)
    # else hardcode 0 Watts
    return 0


def junos_remove_unit(if_name):
    '''
    Remove the Junos unit from the interface name.
    E.g. "" eth-0/0/0.0" becomes "eth-0/0/0"

    Args:
        if_name(str): the interface name

    Returns:
        if_name minus the unit, or if_name if no unit found.
    '''
    pos = if_name.rfind('.')
    if pos > 0:
        return if_name[:pos]
    return if_name


def junos_parse_if_type(if_type):
    '''
    Parse the XML "if-type" field, and return an IF_TYPE_XXX flag.

    Args:
        if_type(str): the XML string for the "if-type" field

    Returns:
        (int) flag that represents the matching IF_TYPE_XXX values
    '''
    iftypes = {
        'Software-Pseudo': IF_TYPE_VIRTUAL,
        'Mgmt-VLAN': IF_TYPE_VIRTUAL,
        'GRE': IF_TYPE_TUNNEL,  # general routing encapsulation
        'Multicast-GRE': IF_TYPE_TUNNEL,    # general routing encapsulation
        'FTI': IF_TYPE_TUNNEL,  # flexible tunnel
        'IPIP': IF_TYPE_TUNNEL,  # IP-in-IP tunnel
        'IP-over-IP': IF_TYPE_TUNNEL,  # IP-in-IP tunnel
        'Flexible-tunnel-Interface': IF_TYPE_TUNNEL,
        'Ethernet': IF_TYPE_ETHERNET,
        'PIMD': IF_TYPE_MCAST,  # multicast related
        'PIME': IF_TYPE_MCAST,  # multicast encapsulation
        'PIM-Encapsulator': IF_TYPE_MCAST,
        'PIM-Decapsulator': IF_TYPE_MCAST,
        'LSI': IF_TYPE_VIRTUAL,
        'Loopback': IF_TYPE_LOOPBACK,
        'VxLAN-Tunnel-Endpoint': IF_TYPE_TUNNEL,
        'Interface-Specific': IF_TYPE_VIRTUAL,
    }
    if if_type in iftypes:
        return iftypes[if_type]
    return IF_TYPE_NONE
