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
"""
Aruba-AOS (new style) specific implementation of the SNMP object
Note that the SNMP implementation in AOS-CX is read-only.
We will implement many features via the REST API of the product, See
https://developer.arubanetworks.com/aruba-aoscx/docs/python-getting-started
This will be done as part of the 'Aruba-AOS' configuration type, coded in
/switches/connect/aruba_aoscx/
"""
from switches.models import Log
from switches.constants import *
from switches.connect.classes import *
from switches.connect.connector import *
from switches.connect.snmp.connector import SnmpConnector
from switches.connect.snmp.constants import *
from switches.utils import *

from .constants import *


class SnmpConnectorAruba(SnmpConnector):
    """
    Aruba specific implementation of the SNMP object, for now a derivative of the default SNMP connector.
    """

    def __init__(self, request, group, switch):
        # for now, just call the super class
        dprint("Aruba SnmpConnector __init__")
        super().__init__(request, group, switch)
        self.vendor_name = 'Aruba AOS (HPE)'
        self.switch.read_only = True    # the new Aruba AOS switches are read-only over snmp. Write-access is via REST API.


"""
    def can_save_config(self):
        # If True, this instance can save the running config to startup
        # Procurve has auto-save, so no save needed, i.e. return False
        return False
"""
