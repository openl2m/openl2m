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
Commands-Only Connector: this implements an SSH connection to the devices
that is used for excuting commands only!
"""
from django.http.request import HttpRequest
import json
import requests

# used to disable unknown SSL cert warnings:
import urllib3
import traceback

from switches.connect.connector import Connector
from switches.models import Switch, SwitchGroup
from switches.utils import time_duration, dprint


class AristaApiConnector(Connector):
    """
    This implements an Arista eAPI connector object.
    """

    def __init__(self, request: HttpRequest, group: SwitchGroup, switch: Switch):
        # call the super class
        dprint("AristaApiConnector __init__")
        super().__init__(request, group, switch)
        self.description = 'Arista eAPI driver'
        self.vendor_name = "Arista"
        # force READ-ONLY for now
        self.read_only = True
        if switch.description:
            self.add_more_info('System', 'Description', switch.description)
        self.show_interfaces = False  # for now, do NOT show interfaces, vlans etc...

    def get_my_basic_info(self) -> bool:
        """
        placeholder, to be implemented.
        """
        dprint("AristaApiConnector get_my_basic_info()")
        self.hostname = self.switch.hostname

        if not self._open_device():
            return False  # self.error already set!

        try:
            #
            # get device version
            #
            command = "show version"
            json_data = self._arista_run_command(command=command)

            # The 'result' key will contain a list of command outputs.
            data = json_data.get('result')[0]
            self.add_more_info('System', 'Model', data['modelName'])
            self.add_more_info('System', 'Serial', data['serialNumber'])
            self.add_more_info('System', 'OS Version', data['version'])
            self.add_more_info('System', 'Uptime', time_duration(int(data['uptime'])))

            #
            # get interface information
            #
            command = "show interfaces"

            #
            # get optical transceiver data
            #
            command = "show interfaces transceiver properties"

            #
            # read VRF info
            #
            command = "show vrf"

        except Exception as err:
            dprint(f"  ERROR running '{command}': {err}")
            self.error.status = True
            self.error.description = f"Error running eAPI command = '{command}'!"
            self.error.details = f"Cannot read device information: {format(err)}"
            self.add_warning(
                warning=f"Cannot read device information: {repr(err)} ({str(type(err))}) => {traceback.format_exc()}"
            )
            return False

        return True

    def get_my_client_data(self) -> bool:
        '''
        read mac addressess, and lldp neigbor info.
        Not yet fully supported in AOS-CX API.
        return True on success, False on error and set self.error variables
        '''

        if not self._open_device():
            dprint("_open_device() failed!")
            return False

        if not self._open_device():
            return False  # self.error already set!

        try:
            #
            # get layer 2 mac info
            #
            command = "show mac address-table"
            json_data = self._arista_run_command(command=command)

            #
            # get ipv4 ARP data
            #
            command = "show arp vrf all"
            json_data = self._arista_run_command(command=command)

            #
            # get ipv6 neighbors
            #
            command = "show ipv6 neighbors vrf all"
            json_data = self._arista_run_command(command=command)

        except Exception as err:
            dprint(f"  ERROR running '{command}': {err}")
            self.error.status = True
            self.error.description = f"Error running eAPI command = '{command}'!"
            self.error.details = f"Cannot read device information: {format(err)}"
            self.add_warning(
                warning=f"Cannot read device information: {repr(err)} ({str(type(err))}) => {traceback.format_exc()}"
            )
            return False

        return True

    def _open_device(self) -> bool:
        '''
        Arista API is stateless, so no need to open...
        return True on success, False on failure, and will set self.error
        '''
        dprint("Arista eAPI _open_device()")

        # do we have creds set?
        if not self.switch.netmiko_profile:
            self.error.status = True
            self.error.description = "Please configure a Credentials Profile to be able to connect to this device!"
            dprint("  _open_device: No Credentials!")
            return False

        # do we want to check SSL certificates?
        if not self.switch.netmiko_profile.verify_hostkey:
            dprint("  Cert warnings disabled in urllib3!")
            # disable unknown cert warnings
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            # or all warnings:
            # urllib3.disable_warnings()

        dprint("  session OK!")
        return True

    def _close_device(self) -> bool:
        '''
        eAPI is stateless, so close is not needed!
        '''
        dprint("Arist eAPI _close_device()")
        return True

    def _arista_run_command(self, command: str, format="json", autoComplete=True):
        """Run a specifc Arista command on the router configured.
        By default, return as JSON, and allow for command auto-complete.

        """
        # eAPI endpoint
        url = f"https://{self.switch.primary_ip4}/command-api"

        # JSON-RPC request payload for 'show ip route'
        payload = {
            "jsonrpc": "2.0",
            "method": "runCmds",
            "params": {
                "format": format,
                "timestamps": False,
                "autoComplete": autoComplete,
                "expandAliases": False,
                "version": 1,
                "cmds": [f"{command}"],
            },
            "id": 1,
        }

        # Headers for the request
        headers = {"Content-type": "application/json"}

        try:
            # Send the request
            response = requests.post(
                url,
                data=json.dumps(payload),
                headers=headers,
                auth=(self.switch.netmiko_profile.username, self.switch.netmiko_profile.password),
                verify=False,
            )
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error connecting to Arista switch (equests.exceptions.RequestException): {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Error decoding JSON response (json.JSONDecodeError): {e}")
        except KeyError as e:
            raise Exception(f"Unexpected JSON structure (KeyError): Missing key {e}")
        except Exception as e:
            raise Exception(f"Generic error caught in arista_run_command: {e}")
