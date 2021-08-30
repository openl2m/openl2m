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
import traceback
import pyaoscx

from switches.connect.classes import *
from switches.connect.connector import *
from switches.connect.utils import interface_name_to_long

"""
Basic Aruba AOS-CX connector. This uses the documented REST API , and allows us to handle
any device supported by the Aruba Python "pyaoscx" library.
See more at https://developer.arubanetworks.com/aruba-aoscx/docs/python-getting-started
"""


class AosCxConnector(Connector):
    """
    This class implements a Connector() to get switch information from Aruba AOS-CX devices.
    """
    def __init__(self, request=False, group=False, switch=False):
        """
        Initialize the object
        """
        dprint("AosCxConnector() __init__")
        super().__init__(request, group, switch)
        self.name = "AOS-CX Connector"
        # force READ-ONLY for now! We have not implemented changing settings.
        self.switch.read_only = True

        self.add_more_info('Connection', 'Type', f"AOS-CX Connector for '{self.switch.name}'")
        self.aoscx_device = False     # this will be the pyaoscx driver object
        # and we dont want to cache this:
        self.set_do_not_cache_attribute('aoxcx_device')

    def get_my_basic_info(self):
        '''
        load 'basic' list of interfaces with status.
        return True on success, False on error and set self.error variables
        '''
        if not self._open_device():
            return False
        # get facts of device first, ie OS, model, etc.!
        return False

    def get_my_client_data(self):
        '''
        return list of interfaces with static_egress_portlist
        return True on success, False on error and set self.error variables
        '''
        if not self._open_device():
            return False
        # get mac address table
        return False

    def _open_device(self):
        '''
        get a pyaoscx 'driver' and open connection to the device
        return True on success, False on failure, and will set self.error
        '''
        return False
