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
Routines to allow Netmiko communications (ie SSH) with switches
to execute various 'show' or 'display' commands
"""
import traceback
import netmiko

from switches.connect.classes import Error
from switches.utils import dprint


class NetmikoExecute():
    """
    This is the base class where it all happens!
    This implements "Generic" netmiko connection to a switch
    """
    def __init__(self, switch):
        """
        Initialize the object with all the settings,
        and connect to the switch
        switch -  the Switch() class object we will connect to
        """
        dprint(f"NetmikoConnector __init__ for {switch.name} ({switch.primary_ip4})")
        self.name = "Standard Netmiko"  # what type of class is running!
        self.device_type = ''       # unknown at creation
        self.connection = False     # return from ConnectHandler()
        self.switch = switch
        # self.timeout = settings.SSH_TIMEOUT  # should be SSH timeout/retry values
        # self.retries = settings.SSH_RETRIES
        self.cmd = ''  # command to issue
        self.output = ''  # command output captured
        self.error = Error()
        self.error.status = False
        return

    def connect(self):
        """
        Establish the connection
        return True on success, False on error,
        with self.error.status and self.error.description set accordingly
        """
        if not self.switch.netmiko_profile:
            self.error.status = True
            self.error.description = 'Switch does not have a Netmiko profile! Please ask the admin to correct this.'
            return False

        # try to connect
        device = {
            'device_type': self.switch.netmiko_profile.device_type,
            'host': self.switch.primary_ip4,
            'username': self.switch.netmiko_profile.username,
            'password': self.switch.netmiko_profile.password,
            'port': self.switch.netmiko_profile.tcp_port,
        }

        try:
            handle = netmiko.ConnectHandler(**device)
        except netmiko.NetMikoTimeoutException:
            self.error.status = True
            self.error.description = "Connection time-out! Please ask the admin to correct the switch hostname or IP."
            return False
        except netmiko.NetMikoAuthenticationException:
            self.error.status = True
            self.error.description = "Access denied! Please ask the admin to correct the switch credentials."
            return False
        except Exception as e:
            self.error.status = True
            self.error.description = "SSH Connection denied! Please inform your admin."
            self.error.details = f"Netmiko Error: {repr(e)} ({str(type(e))})\n{traceback.format_exc()}"
            return False

        self.connection = handle
        return True

    def disable_paging(self):
        """
        disable paging, ie the "hit a key" for more
        We call the Netmiko built-in function
        """
        if not self.connection:
            self.connect()
        if self.connection:
            if self.switch.netmiko_profile.device_type == 'hp_comware':
                command = 'screen-length disable'
            elif self.switch.netmiko_profile.device_type == 'hp_procurve':
                command = 'no page'
            else:
                # other types just use default command (defaults to Cisco)
                command = 'teminal length 0'
            try:
                self.connection.disable_paging(command)
            except Exception:
                self.output = "Error disabling paging!"
                return False
        return True

    def execute_command(self, command):
        """
        Execute a single command on the switch and return True on success.
        Set the command output to self.output
        """
        dprint(f"NetmikoConnector execute_command() '{command}'")
        self.output = ''
        if not self.connection:
            self.connect()
        if self.connection:
            self.disable_paging()
            try:
                self.output = self.connection.send_command(command)
            except Exception:
                self.output = "Error sending command!"
                return False
            return True
        else:
            self.output = "No connection found!"
            return False

    def execute_config_commands(self, commands):
        """
        Put the switch in 'config' mode, and then execute a command string or
        list of commands on the switch.
        Return the command output
        """
        dprint(f"NetmikoConnector execute_config_command '{commands}'")
        self.output = ''
        if not self.connection:
            self.connect()
        if self.connection:
            try:
                self.connection.send_config_set(commands)
            except Exception:
                self.output = "Error sending commands!"
                dprint("Exception in connection.send_config_set()!")
                return False
            return True
        else:
            self.output = "No connection found!"
            return -1
