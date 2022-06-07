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

def junos_speed_to_mbps(speed):
    '''
    Convert speed string to integer in 1Mbps

    Args:
        speed(str): a string representing interface speed in Mbps

    Returns:
        (int) the speed in Mbps as an integer
    '''
    if speed.endswith('mbps'):
        return int(speed.replace('mbps', ''))
    # else hardcode to 1Gbps for now:
    return 1000


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
