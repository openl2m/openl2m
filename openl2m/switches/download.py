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
import io
import time
import xlsxwriter

from switches.connect.classes import Error
from switches.connect.connector import Connector
from switches.connect.constants import (
    LLDP_CHASSIC_TYPE_ETH_ADDR,
    LLDP_CHASSIC_TYPE_NET_ADDR,
    IANA_TYPE_IPV4,
    IANA_TYPE_IPV6,
    POE_PORT_DETECT_DELIVERING,
    IF_TYPE_LAGG,
    IF_TYPE_ETHERNET,
)
from switches.utils import dprint


def create_eth_neighbor_xls_file(connection: Connector):
    """Create an XLS temp file that contains the ethernet and neighbors of a device.

    Args:
        connection (Connector()): a valid Connector object, that has ethernet and neighbor information filled in.

    Returns:
        (BytesIO() object), Error() ): an open stream, or an Error() object if that cannot be created,.
    """
    dprint("create_eth_neighbor_xls_file()")
    try:
        # create the Excel file handler to a temporary byte stream
        fh = io.BytesIO()
        workbook = xlsxwriter.Workbook(fh)

        # Add some formats to use to highlight cells.
        format_bold = workbook.add_format({'bold': True, 'font_name': 'Calibri', 'font_size': 14})
        format_regular = workbook.add_format({'font_name': 'Calibri', 'font_size': 12})
        # add a tab
        worksheet = workbook.add_worksheet('Ethernet-Arp-LLDP')

        COL_INTERFACE_NAME = 0
        COL_INTERFACE_VLAN = 1
        COL_INTERFACE_POE_DRAW = 2
        COL_INTERFACE_DESCRIPTION = 3
        COL_ETHERNET = 4
        COL_IPV4 = 5
        COL_VENDOR = 6
        COL_NEIGHBOR_NAME = 7
        COL_NEIGHBOR_TYPE = 8
        COL_NEIGHBOR_DESCRIPTION = 9

        # start with a date message:
        row = 0
        worksheet.write(
            row,
            COL_INTERFACE_NAME,
            f"Ethernet and Neighbor data from '{connection.switch.name}' generated for '{connection.request.user}' at {time.strftime('%I:%M %p, %d %B %Y', time.localtime())}",
            format_bold,
        )

        # write header row
        row += 1
        worksheet.write(row, COL_INTERFACE_NAME, 'Interface', format_bold)
        worksheet.set_column(COL_INTERFACE_NAME, COL_INTERFACE_NAME, 30)  # Adjust the column width.

        worksheet.write(row, COL_INTERFACE_VLAN, 'Untagged VLAN', format_bold)
        worksheet.set_column(COL_INTERFACE_VLAN, COL_INTERFACE_VLAN, 20)

        worksheet.write(row, COL_INTERFACE_POE_DRAW, 'Power (mW)', format_bold)
        worksheet.set_column(COL_INTERFACE_POE_DRAW, COL_INTERFACE_POE_DRAW, 15)

        worksheet.write(row, COL_INTERFACE_DESCRIPTION, 'Description', format_bold)
        worksheet.set_column(COL_INTERFACE_DESCRIPTION, COL_INTERFACE_DESCRIPTION, 50)

        worksheet.write(row, COL_ETHERNET, 'Ethernet Heard', format_bold)
        worksheet.set_column(COL_ETHERNET, COL_ETHERNET, 20)

        worksheet.write(row, COL_IPV4, 'IPv4 Address', format_bold)
        worksheet.set_column(COL_IPV4, COL_IPV4, 20)

        worksheet.write(row, COL_VENDOR, 'Vendor', format_bold)
        worksheet.set_column(COL_VENDOR, COL_VENDOR, 25)

        worksheet.write(row, COL_NEIGHBOR_NAME, 'Neighbor Name', format_bold)
        worksheet.set_column(COL_NEIGHBOR_NAME, COL_NEIGHBOR_NAME, 20)

        worksheet.write(row, COL_NEIGHBOR_TYPE, 'Neighbor Type', format_bold)
        worksheet.set_column(COL_NEIGHBOR_TYPE, COL_NEIGHBOR_TYPE, 20)

        worksheet.write(row, COL_NEIGHBOR_DESCRIPTION, 'Neighbor Description', format_bold)
        worksheet.set_column(COL_NEIGHBOR_DESCRIPTION, COL_NEIGHBOR_DESCRIPTION, 50)

        # now loop through all interfaces on the connection:
        for interface in connection.interfaces.values():
            for eth in interface.eth.values():
                row += 1
                # for now write name first
                # vendor = eth.vendor
                worksheet.write(row, COL_INTERFACE_NAME, interface.name, format_regular)
                worksheet.write(row, COL_INTERFACE_VLAN, interface.untagged_vlan, format_regular)

                if interface.poe_entry and interface.poe_entry.detect_status == POE_PORT_DETECT_DELIVERING:
                    worksheet.write(row, COL_INTERFACE_POE_DRAW, interface.poe_entry.power_consumed, format_regular)

                worksheet.write(row, COL_INTERFACE_DESCRIPTION, interface.description, format_regular)
                worksheet.write(row, COL_ETHERNET, str(eth), format_regular)
                worksheet.write(row, COL_VENDOR, eth.vendor, format_regular)
                worksheet.write(row, COL_IPV4, eth.address_ip4, format_regular)

            # and loop through lldp:
            for neighbor in interface.lldp.values():
                row += 1
                found_ip = False
                dprint(f"LLDP: on {interface.name} - {neighbor.sys_name}")
                worksheet.write(row, COL_INTERFACE_NAME, interface.name, format_regular)
                # what kind of chassis address do we have (if any)
                if neighbor.chassis_type == LLDP_CHASSIC_TYPE_ETH_ADDR:
                    worksheet.write(row, COL_ETHERNET, neighbor.chassis_string, format_regular)
                    worksheet.write(row, COL_VENDOR, neighbor.vendor, format_regular)
                elif neighbor.chassis_type == LLDP_CHASSIC_TYPE_NET_ADDR:
                    if neighbor.chassis_string_type == IANA_TYPE_IPV4:
                        worksheet.write(row, COL_IPV4, neighbor.chassis_string, format_regular)
                        found_ip = True
                    elif neighbor.chassis_string_type == IANA_TYPE_IPV6:
                        # TBD, IPv6 not supported yet.
                        dprint("  IPV6 chassis address: NOT supported yet")
                        # worksheet.write(row, COL_IPV6, neighbor.chassis_string, format_regular)
                # if we don't have IP info yet, do we have management IP?
                if not found_ip and neighbor.management_address:
                    if neighbor.management_address_type == IANA_TYPE_IPV4:
                        worksheet.write(row, COL_IPV4, neighbor.management_address, format_regular)
                    elif neighbor.management_address_type == IANA_TYPE_IPV6:
                        # TBD, IPv6 not supported yet.
                        dprint("  IPV6 management address: NOT supported yet")
                        # worksheet.write(row, COL_IPV6, neighbor.management_address, format_regular)

                worksheet.write(row, COL_NEIGHBOR_NAME, neighbor.sys_name, format_regular)
                worksheet.write(row, COL_NEIGHBOR_TYPE, neighbor.capabilities_as_string(), format_regular)
                worksheet.write(row, COL_NEIGHBOR_DESCRIPTION, neighbor.sys_descr, format_regular)

        workbook.close()
    except Exception as err:  # trap all errors from above!
        error = Error()
        error.description = "Error creating Excel file!"
        error.details = f"ERROR: {err}"
        return False, error

    # all OK!
    fh.seek(0)  # rewind to beginning of "file"
    return fh, None


def create_interfaces_xls_file(connection: Connector):
    """Create an XLS temp file that contains the interface/port information for a device.

    Args:
        connection (Connector()): a valid Connector object, that has basic (interface) information filled in.

    Returns:
        (BytesIO() object), Error() ): an open stream, or an Error() object if that cannot be created,.
    """
    dprint("create_interfaces_xls_file()")
    try:
        # create the Excel file handler to a temporary byte stream
        fh = io.BytesIO()
        workbook = xlsxwriter.Workbook(fh)

        # Add some formats to use to highlight cells.
        format_bold = workbook.add_format({'bold': True, 'font_name': 'Calibri', 'font_size': 14})
        format_regular = workbook.add_format({'font_name': 'Calibri', 'font_size': 12})
        # add a tab
        worksheet = workbook.add_worksheet('Interfaces')

        COL_INTERFACE_NAME = 0
        COL_INTERFACE_MODE = 1
        COL_INTERFACE_STATE = 2
        COL_INTERFACE_VLAN = 3
        COL_INTERFACE_POE = 4
        COL_INTERFACE_POE_DRAW = 5
        COL_INTERFACE_DESCRIPTION = 6

        # start with a date message:
        row = 0
        worksheet.write(
            row,
            COL_INTERFACE_NAME,
            f"Interface info from '{connection.switch.name}' generated for '{connection.request.user}' at {time.strftime('%I:%M %p, %d %B %Y', time.localtime())}",
            format_bold,
        )

        # write header row
        row += 1
        worksheet.write(row, COL_INTERFACE_NAME, 'Interface', format_bold)
        worksheet.set_column(COL_INTERFACE_NAME, COL_INTERFACE_NAME, 30)  # Adjust the column width.

        worksheet.write(row, COL_INTERFACE_MODE, 'Mode', format_bold)
        worksheet.set_column(COL_INTERFACE_MODE, COL_INTERFACE_MODE, 20)

        worksheet.write(row, COL_INTERFACE_STATE, 'State', format_bold)
        worksheet.set_column(COL_INTERFACE_STATE, COL_INTERFACE_STATE, 10)

        worksheet.write(row, COL_INTERFACE_VLAN, 'Untagged VLAN', format_bold)
        worksheet.set_column(COL_INTERFACE_VLAN, COL_INTERFACE_VLAN, 20)

        worksheet.write(row, COL_INTERFACE_POE, 'PoE Status', format_bold)
        worksheet.set_column(COL_INTERFACE_POE, COL_INTERFACE_POE, 15)

        worksheet.write(row, COL_INTERFACE_POE_DRAW, 'Power (mW)', format_bold)
        worksheet.set_column(COL_INTERFACE_POE_DRAW, COL_INTERFACE_POE_DRAW, 15)

        worksheet.write(row, COL_INTERFACE_DESCRIPTION, 'Description', format_bold)
        worksheet.set_column(COL_INTERFACE_DESCRIPTION, COL_INTERFACE_DESCRIPTION, 50)

        # now loop through all interfaces on the connection:
        for interface in connection.interfaces.values():
            if interface.visible:
                row += 1
                worksheet.write(row, COL_INTERFACE_NAME, interface.name, format_regular)

                if interface.is_routed:
                    worksheet.write(row, COL_INTERFACE_MODE, "Routed", format_regular)
                elif interface.lacp_master_index > 0:
                    worksheet.write(row, COL_INTERFACE_MODE, "LACP-Member", format_regular)
                elif interface.type == IF_TYPE_LAGG:
                    worksheet.write(row, COL_INTERFACE_MODE, "LACP", format_regular)
                elif interface.is_tagged:
                    worksheet.write(row, COL_INTERFACE_MODE, "Trunk", format_regular)
                elif interface.type != IF_TYPE_ETHERNET:
                    worksheet.write(row, COL_INTERFACE_MODE, "Virtual", format_regular)
                else:
                    # anything else is access port:
                    worksheet.write(row, COL_INTERFACE_MODE, "Access", format_regular)

                if interface.untagged_vlan > 0:
                    worksheet.write(row, COL_INTERFACE_VLAN, interface.untagged_vlan, format_regular)

                if interface.oper_status:
                    worksheet.write(row, COL_INTERFACE_STATE, "Up", format_regular)
                else:
                    worksheet.write(row, COL_INTERFACE_STATE, "Down", format_regular)

                if interface.poe_entry:
                    if interface.poe_entry.detect_status > POE_PORT_DETECT_DELIVERING:
                        worksheet.write(row, COL_INTERFACE_POE, "Error", format_regular)
                    elif interface.poe_entry.detect_status == POE_PORT_DETECT_DELIVERING:
                        worksheet.write(row, COL_INTERFACE_POE, "Delivering", format_regular)
                        worksheet.write(row, COL_INTERFACE_POE_DRAW, interface.poe_entry.power_consumed, format_regular)
                    else:
                        worksheet.write(row, COL_INTERFACE_POE, "Available", format_regular)

                worksheet.write(row, COL_INTERFACE_DESCRIPTION, interface.description, format_regular)

        workbook.close()
    except Exception as err:  # trap all errors from above!
        error = Error()
        error.description = "Error creating Excel file!"
        error.details = f"ERROR: {err}"
        return False, error

    # all OK!
    fh.seek(0)  # rewind to beginning of "file"
    return fh, None
