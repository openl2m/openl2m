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

from django.http.request import HttpRequest
from django.utils import timezone

from rest_framework.request import Request as RESTRequest

import switches
from switches.utils import dprint
from switches.constants import (
    CONNECTOR_TYPE_SNMP,
    CONNECTOR_TYPE_AOSCX,
    # CONNECTOR_TYPE_HPE_CW7_NC,
    CONNECTOR_TYPE_HPE_CW_REST,
    CONNECTOR_TYPE_AOS_S_REST,
    CONNECTOR_TYPE_EAPI,
    CONNECTOR_TYPE_PYEZ,
    CONNECTOR_TYPE_COMMANDS_ONLY,
    CONNECTOR_TYPE_NAPALM,
    CONNECTOR_TYPE_TESTDUMMY,
)

from switches.connect.connector import Connector

# here are the device specific classes.
# this should be made dynamic at some point!
from switches.connect.snmp.connector import SnmpConnector, SnmpProbeConnector, oid_in_branch
from switches.connect.snmp.constants import enterprises

# from switches.connect.snmp.cisco.constants import ENTERPRISE_ID_CISCO
from switches.connect.snmp.cisco.connector import SnmpConnectorCisco

# Dell is yet to be tested!
# from switches.connect.snmp.dell.constants import *
# from switches.connect.snmp.dell.connector import SnmpConnectorDell
# from switches.connect.snmp.comware.constants import ENTERPRISE_ID_H3C
from switches.connect.snmp.comware.connector import SnmpConnectorComware

# from switches.connect.snmp.juniper.constants import ENTERPRISE_ID_JUNIPER
from switches.connect.snmp.juniper.connector import SnmpConnectorJuniper

# from switches.connect.snmp.procurve.constants import ENTERPRISE_ID_HP
from switches.connect.snmp.procurve.connector import SnmpConnectorProcurve

# from switches.connect.snmp.arista_eos.constants import ENTERPRISE_ID_ARISTA
from switches.connect.snmp.arista_eos.connector import SnmpConnectorAristaEOS

# from switches.connect.snmp.aruba_cx.constants import ENTERPRISE_ID_HP_ENTERPRISE
from switches.connect.snmp.aruba_cx.connector import SnmpConnectorArubaCx

# from switches.connect.snmp.netgear.constants import ENTERPRISE_ID_NETGEAR
from switches.connect.snmp.netgear.connector import SnmpConnectorNetgear

# from switches.connect.snmp.mikrotik.constants import ENTERPRISE_ID_MIKROTIK
from switches.connect.snmp.mikrotik.connector import SnmpConnectorMikroTik

from switches.connect.aruba_aoscx.connector import AosCxConnector
from switches.connect.aruba_aoss_rest.connector import ArubaAOSsRestConnector
from switches.connect.arista_eapi.connector import AristaApiConnector
# from switches.connect.hpe_cw7_nc.connector import HPECw7NcConnector
from switches.connect.hpe_cw_rest.connector import HPECwRestConnector
from switches.connect.junos_pyez.connector import PyEZConnector
from switches.connect.commands_only.connector import CommandsOnlyConnector

# Napalm drivers are here:
from switches.connect.napalm.connector import NapalmConnector

# a dummy 'test connector'
from switches.connect.dummy.connector import DummyConnector

from switches.models import Switch, SwitchGroup


def get_connection_object(request: HttpRequest, group: SwitchGroup, switch: Switch) -> Connector:
    """
    Function to get the proper type of Connector() object, based on device connector_type settings.
    For SNMP devices, we probe the 'system' mib, and then a vendor-specific Connector() object will be returned.
    If vendor is unknown, we return a generic snmp object.
    If probing fails, we raise an exception!
    """
    dprint(f"get_connection_object() for {switch} at {timezone.now()}")

    # What type of connector are we using?
    if switch.connector_type == CONNECTOR_TYPE_SNMP:
        # go probe to find vendor type
        dprint("SNMP: Probing device...")
        conn = SnmpProbeConnector(request, group, switch)
        snmp_oid = conn.get_system_oid()
        if snmp_oid:
            # we have the ObjectID, what kind of vendor is it:
            dprint(f"   Checking device type for {snmp_oid}")
            sub_oid = oid_in_branch(enterprises, snmp_oid)
            if sub_oid:
                parts = sub_oid.split(".", 1)  # 1 means one split, two elements!
                enterprise_id = int(parts[0])
                # here we go:
                match enterprise_id:
                    case switches.connect.snmp.cisco.constants.ENTERPRISE_ID_CISCO:
                        connection = SnmpConnectorCisco(request, group, switch)
                    case switches.connect.snmp.juniper.constants.ENTERPRISE_ID_JUNIPER:
                        connection = SnmpConnectorJuniper(request, group, switch)
                    case switches.connect.snmp.procurve.constants.ENTERPRISE_ID_HP:
                        connection = SnmpConnectorProcurve(request, group, switch)
                    case switches.connect.snmp.comware.constants.ENTERPRISE_ID_H3C:
                        connection = SnmpConnectorComware(request, group, switch)
                    case switches.connect.snmp.aruba_cx.constants.ENTERPRISE_ID_HP_ENTERPRISE:
                        connection = SnmpConnectorArubaCx(request, group, switch)
                    case switches.connect.snmp.arista_eos.constants.ENTERPRISE_ID_ARISTA:
                        connection = SnmpConnectorAristaEOS(request, group, switch)
                    case switches.connect.snmp.netgear.constants.ENTERPRISE_ID_NETGEAR:
                        connection = SnmpConnectorNetgear(request, group, switch)
                    case switches.connect.snmp.mikrotik.constants.ENTERPRISE_ID_MIKROTIK:
                        connection = SnmpConnectorMikroTik(request, group, switch)
                    # Dell is yet to be tested!
                    # case ENTERPRISE_ID_DELL:
                    #    connection = SnmpConnectorDell(request, group, switch)
                    case _:
                        # system oid found, but unknown vendor:
                        connection = SnmpConnector(request, group, switch)

        # no system oid found, return a "generic" SNMP object
        else:
            connection = SnmpConnector(request, group, switch)

    # This is the "custom" Aruba AOS CX connector, using the device REST API.
    elif switch.connector_type == CONNECTOR_TYPE_AOSCX:
        connection = AosCxConnector(request, group, switch)

    # This is the "custom" Arista eAPI connector, using the device REST API.
    elif switch.connector_type == CONNECTOR_TYPE_EAPI:
        connection = AristaApiConnector(request, group, switch)

    # this driver is abandoned, in favor of the REST API driver below!
    #
    # # This is the "custom" HPE Comware7 NetConf connector, using the device NetConf API.
    # elif switch.connector_type == CONNECTOR_TYPE_HPE_CW7_NC:
    #     connection = HPECw7NcConnector(request, group, switch)

    # This is the "custom" HPE Comware REST API connector.
    elif switch.connector_type == CONNECTOR_TYPE_HPE_CW_REST:
        connection = HPECwRestConnector(request, group, switch)

    # This is a "custom" Aruba AOS-S switches REST API connector.
    elif switch.connector_type == CONNECTOR_TYPE_AOS_S_REST:
        connection = ArubaAOSsRestConnector(request, group, switch)

    # This is the "custom" Junos PyEZ connector, using the device NetConf API.
    elif switch.connector_type == CONNECTOR_TYPE_PYEZ:
        connection = PyEZConnector(request, group, switch)

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
    if not connection.load_cache():
        # first WebGUI request, update only once per session the device access count and timestamp
        switch.update_access()
        # now check if this is REST request:
        if isinstance(request, RESTRequest):
            # API call with token, there is no cache so always load the basic switch config:
            dprint("  API call: calling get_basic_info()")
            if not connection.get_basic_info():
                dprint(f"  ERROR in get_basic_info(): {connection.error.description}")
                raise Exception(connection.error.description)
    # then return object
    dprint("  Returning connection() from get_connection_object()")
    return connection
