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
Get a connection to the device. Ideally, we use SNMP,
but could end up using something else (e.g. Netmiko(ssh))
if we cannot do it all using snmp.
"""
import datetime

from django.utils import timezone

from switches.utils import dprint
from switches.connect.connector import *
from switches.connect.classes import Error
import switches.views

# here are the device specific classes.
# this should be made dynamic at some point!
from switches.connect.snmp.connector import *
from switches.connect.snmp.constants import *
from switches.connect.snmp.cisco.constants import *
from switches.connect.snmp.cisco.connector import SnmpConnectorCisco
from switches.connect.snmp.dell.constants import *
from switches.connect.snmp.dell.connector import SnmpConnectorDell
from switches.connect.snmp.comware.constants import *
from switches.connect.snmp.comware.connector import SnmpConnectorComware
from switches.connect.snmp.juniper.constants import *
from switches.connect.snmp.juniper.connector import SnmpConnectorJuniper
from switches.connect.snmp.procurve.constants import *
from switches.connect.snmp.procurve.connector import SnmpConnectorProcurve
from switches.connect.snmp.aruba.constants import *
from switches.connect.snmp.aruba.connector import SnmpConnectorAruba
from switches.connect.aruba_aoscx.constants import *
from switches.connect.aruba_aoscx.connector import AosCxConnector

from switches.connect.commands_only.constants import *
from switches.connect.commands_only.connector import CommandsOnlyConnector

# Napalm drivers are here:
from switches.connect.napalm.connector import NapalmConnector

# a dummy 'test connector'
from switches.connect.dummy.connector import DummyConnector


def get_connection_object(request, group, switch):
    """
    Function to get the proper type of SNMP object for this switch.
    Either Generic (SNMP), HP-3COM (H3C) or Cisco specific objects will be returned.
    If switch objectID is not known yet, we will probe the switch first.
    If probing fails, we raise an exception!
    """
    dprint(f"get_connection_object() for {switch} at {timezone.now()}")

    # What type of connector are we using?
    if switch.connector_type == CONNECTOR_TYPE_SNMP:
        if not switch.snmp_oid:
            # we don't know this switch yet, go probe it
            conn = SnmpConnector(request, group, switch)
            if not conn._probe_mibs():
                raise Exception('Error probing device. Is the SNMP Profile correct?')
                return  # for clarify

        # now we should have the basics:
        if switch.snmp_oid:
            # we have the ObjectID, what kind of vendor is it:
            dprint(f"   Checking device type for {switch.snmp_oid}")
            sub_oid = oid_in_branch(enterprises, switch.snmp_oid)
            if sub_oid:
                parts = sub_oid.split('.', 1)  # 1 means one split, two elements!
                enterprise_id = int(parts[0])
                # here we go:
                if enterprise_id == ENTERPRISE_ID_CISCO:
                    connection = SnmpConnectorCisco(request, group, switch)

                elif enterprise_id == ENTERPRISE_ID_JUNIPER:
                    connection = SnmpConnectorJuniper(request, group, switch)

                elif enterprise_id == ENTERPRISE_ID_HP:
                    connection = SnmpConnectorProcurve(request, group, switch)

                elif enterprise_id == ENTERPRISE_ID_H3C:
                    connection = SnmpConnectorComware(request, group, switch)

                elif enterprise_id == ENTERPRISE_ID_HP_ENTERPRISE:
                    connection = SnmpConnectorAruba(request, group, switch)

                # Dell is yet to be tested!
                # elif enterprise_id == ENTERPRISE_ID_DELL:
                #    connection = SnmpConnectorDell(request, group, switch)

                else:
                    # system oid found, but unknown vendor:
                    connection = SnmpConnector(request, group, switch)

        # no system oid found, return a "generic" SNMP object
        else:
            connection = SnmpConnector(request, group, switch)

    # This is the "custom" Aruba AOS CS connector, using the device REST API.
    # this implementation is planned, ETA is TBD :-)
    elif switch.connector_type == CONNECTOR_TYPE_AOSCX:
        connection = AosCxConnector(request, group, switch)

    # This is the "custom" connector that handles SSH commands, but does not load
    # interface data!
    elif switch.connector_type == CONNECTOR_TYPE_COMMANDS_ONLY:
        connection = CommandsOnlyConnector(request, group, switch)

    # The Napalm connector uses the Python Napalm package. It is read-only.
    # Mostly implemented to test and show the new Connector() API class.
    elif switch.connector_type == CONNECTOR_TYPE_NAPALM:
        connection = NapalmConnector(request, group, switch)

    # this is a test class, to show and test the new Connector() API class:
    elif switch.connector_type == CONNECTOR_TYPE_TESTDUMMY:
        connection = DummyConnector(request, group, switch)

    else:
        # should not happen!
        raise Exception("Invalid connector type configured on switch!")

    # load caches (http session, memory cache (future), whatever else for performance)
    connection.load_cache()
    # then return object
    return connection
