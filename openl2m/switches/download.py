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


class Spreadsheet:
    """Class to wrap some settings for spreadsheet output together"""

    def __init__(self):
        # create the Excel file handler to a temporary byte stream
        # Note: this file is closed by the Django FileResponse(fh) call in views.py !
        self.fh = io.BytesIO()
        self.workbook = xlsxwriter.Workbook(self.fh)

        # Add some formats to use to highlight cells.
        self.format_bold = self.workbook.add_format({'bold': True, 'font_name': 'Calibri', 'font_size': 14})
        self.format_regular = self.workbook.add_format({'font_name': 'Calibri', 'font_size': 12})


def create_workbook():
    """Create an XLS format workbook

    Returns:
        (spreadsheet, error_str)
            spreadsheet: a Spreadsheet() object
            error_str: explanation of error
    """
    dprint("create_workbook()")
    try:
        spreadsheet = Spreadsheet()
        return spreadsheet, ""

    except Exception as err:
        dprint(f"Cannot create spreadsheet, error: {err}")
        return False, f"{err}"


def create_interfaces_worksheet(spreadsheet: Spreadsheet(), connection: Connector):
    """Add a worksheet that contains the interface/port information for a device.
    Does NOT trap exceptions, so these can be caught in the calling function for better
    error reporting.

    Args:
        spreadsheet (Spreadsheet()): a Spreadsheet() object with Workbook() ready to write to.
        connection (Connector()): a valid Connector object, that has ethernet and neighbor information filled in.

    Returns:
        n/a
    """
    dprint("create_interfaces_worksheet()")
    # add a tab to workbook
    worksheet = spreadsheet.workbook.add_worksheet('Interfaces')

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
        spreadsheet.format_bold,
    )

    # write header row
    row += 1
    worksheet.write(row, COL_INTERFACE_NAME, 'Interface', spreadsheet.format_bold)
    worksheet.set_column(COL_INTERFACE_NAME, COL_INTERFACE_NAME, 30)  # Adjust the column width.

    worksheet.write(row, COL_INTERFACE_MODE, 'Mode', spreadsheet.format_bold)
    worksheet.set_column(COL_INTERFACE_MODE, COL_INTERFACE_MODE, 20)

    worksheet.write(row, COL_INTERFACE_STATE, 'State', spreadsheet.format_bold)
    worksheet.set_column(COL_INTERFACE_STATE, COL_INTERFACE_STATE, 10)

    worksheet.write(row, COL_INTERFACE_VLAN, 'Untagged VLAN', spreadsheet.format_bold)
    worksheet.set_column(COL_INTERFACE_VLAN, COL_INTERFACE_VLAN, 20)

    worksheet.write(row, COL_INTERFACE_POE, 'PoE Status', spreadsheet.format_bold)
    worksheet.set_column(COL_INTERFACE_POE, COL_INTERFACE_POE, 15)

    worksheet.write(row, COL_INTERFACE_POE_DRAW, 'Power (mW)', spreadsheet.format_bold)
    worksheet.set_column(COL_INTERFACE_POE_DRAW, COL_INTERFACE_POE_DRAW, 15)

    worksheet.write(row, COL_INTERFACE_DESCRIPTION, 'Description', spreadsheet.format_bold)
    worksheet.set_column(COL_INTERFACE_DESCRIPTION, COL_INTERFACE_DESCRIPTION, 50)

    # freeze top 2 rows to easy scrolling
    worksheet.freeze_panes(2, 0)

    # now loop through all interfaces on the connection:
    for interface in connection.interfaces.values():
        if interface.visible:
            row += 1
            worksheet.write(row, COL_INTERFACE_NAME, interface.name, spreadsheet.format_regular)

            if interface.is_routed:
                worksheet.write(row, COL_INTERFACE_MODE, "Routed", spreadsheet.format_regular)
            elif interface.lacp_master_index > 0:
                worksheet.write(row, COL_INTERFACE_MODE, "LACP-Member", spreadsheet.format_regular)
            elif interface.type == IF_TYPE_LAGG:
                worksheet.write(row, COL_INTERFACE_MODE, "LACP", spreadsheet.format_regular)
            elif interface.is_tagged:
                worksheet.write(row, COL_INTERFACE_MODE, "Trunk", spreadsheet.format_regular)
            elif interface.type != IF_TYPE_ETHERNET:
                worksheet.write(row, COL_INTERFACE_MODE, "Virtual", spreadsheet.format_regular)
            else:
                # anything else is access port:
                worksheet.write(row, COL_INTERFACE_MODE, "Access", spreadsheet.format_regular)

            if interface.untagged_vlan > 0:
                worksheet.write(row, COL_INTERFACE_VLAN, interface.untagged_vlan, spreadsheet.format_regular)

            if interface.oper_status:
                worksheet.write(row, COL_INTERFACE_STATE, "Up", spreadsheet.format_regular)
            else:
                worksheet.write(row, COL_INTERFACE_STATE, "Down", spreadsheet.format_regular)

            if interface.poe_entry:
                if interface.poe_entry.detect_status > POE_PORT_DETECT_DELIVERING:
                    worksheet.write(row, COL_INTERFACE_POE, "Error", spreadsheet.format_regular)
                elif interface.poe_entry.detect_status == POE_PORT_DETECT_DELIVERING:
                    worksheet.write(row, COL_INTERFACE_POE, "Delivering", spreadsheet.format_regular)
                    worksheet.write(
                        row, COL_INTERFACE_POE_DRAW, interface.poe_entry.power_consumed, spreadsheet.format_regular
                    )
                else:
                    worksheet.write(row, COL_INTERFACE_POE, "Available", spreadsheet.format_regular)

            worksheet.write(row, COL_INTERFACE_DESCRIPTION, interface.description, spreadsheet.format_regular)


def create_neighbors_worksheet(spreadsheet: Spreadsheet, connection: Connector):
    """To the existing workbook, add a worksheet that contains the ethernet and neighbors of a device.
    Does NOT trap exceptions, so these can be caught in the calling function for better
    error reporting.

    Args:
        workbook (Workboo()): a XlsWriter.Workbook object ready to write to.
        connection (Connector()): a valid Connector object, that has ethernet and neighbor information filled in.

    Returns:
        n/a
    """
    dprint("create_neighbors_worksheet()")
    # add a tab to workbook
    worksheet = spreadsheet.workbook.add_worksheet('Ethernet-Arp-LLDP')
    # if we render this worksheet (ie tab), this will always be the active tab:
    worksheet.activate()

    COL_INTERFACE_NAME = 0
    COL_INTERFACE_VLAN = 1
    COL_INTERFACE_POE_DRAW = 2
    COL_INTERFACE_DESCRIPTION = 3
    COL_ETHERNET = 4
    COL_IPV4 = 5
    COL_IPV6 = 6
    COL_VENDOR = 7
    COL_NEIGHBOR_NAME = 8
    COL_NEIGHBOR_TYPE = 9
    COL_NEIGHBOR_DESCRIPTION = 10

    # start with a date message:
    row = 0
    worksheet.write(
        row,
        COL_INTERFACE_NAME,
        f"Ethernet and Neighbor data from '{connection.switch.name}' generated for '{connection.request.user}' at {time.strftime('%I:%M %p, %d %B %Y', time.localtime())}",
        spreadsheet.format_bold,
    )

    # write header row
    row += 1
    worksheet.write(row, COL_INTERFACE_NAME, 'Interface', spreadsheet.format_bold)
    worksheet.set_column(COL_INTERFACE_NAME, COL_INTERFACE_NAME, 30)  # Adjust the column width.

    worksheet.write(row, COL_INTERFACE_VLAN, 'Untagged VLAN', spreadsheet.format_bold)
    worksheet.set_column(COL_INTERFACE_VLAN, COL_INTERFACE_VLAN, 20)

    worksheet.write(row, COL_INTERFACE_POE_DRAW, 'Power (mW)', spreadsheet.format_bold)
    worksheet.set_column(COL_INTERFACE_POE_DRAW, COL_INTERFACE_POE_DRAW, 15)

    worksheet.write(row, COL_INTERFACE_DESCRIPTION, 'Description', spreadsheet.format_bold)
    worksheet.set_column(COL_INTERFACE_DESCRIPTION, COL_INTERFACE_DESCRIPTION, 50)

    worksheet.write(row, COL_ETHERNET, 'Ethernet Heard', spreadsheet.format_bold)
    worksheet.set_column(COL_ETHERNET, COL_ETHERNET, 20)

    worksheet.write(row, COL_IPV4, 'IPv4 Address', spreadsheet.format_bold)
    worksheet.set_column(COL_IPV4, COL_IPV4, 20)

    worksheet.write(row, COL_IPV6, 'IPv6 Address', spreadsheet.format_bold)
    worksheet.set_column(COL_IPV6, COL_IPV6, 25)

    worksheet.write(row, COL_VENDOR, 'Vendor', spreadsheet.format_bold)
    worksheet.set_column(COL_VENDOR, COL_VENDOR, 25)

    worksheet.write(row, COL_NEIGHBOR_NAME, 'Neighbor Name', spreadsheet.format_bold)
    worksheet.set_column(COL_NEIGHBOR_NAME, COL_NEIGHBOR_NAME, 20)

    worksheet.write(row, COL_NEIGHBOR_TYPE, 'Neighbor Type', spreadsheet.format_bold)
    worksheet.set_column(COL_NEIGHBOR_TYPE, COL_NEIGHBOR_TYPE, 20)

    worksheet.write(row, COL_NEIGHBOR_DESCRIPTION, 'Neighbor Description', spreadsheet.format_bold)
    worksheet.set_column(COL_NEIGHBOR_DESCRIPTION, COL_NEIGHBOR_DESCRIPTION, 50)

    # freeze top 2 rows to easy scrolling
    worksheet.freeze_panes(2, 0)

    # now loop through all interfaces on the connection:
    for interface in connection.interfaces.values():
        for eth in interface.eth.values():
            row += 1
            # for now write name first
            # vendor = eth.vendor
            worksheet.write(row, COL_INTERFACE_NAME, interface.name, spreadsheet.format_regular)
            worksheet.write(row, COL_INTERFACE_VLAN, interface.untagged_vlan, spreadsheet.format_regular)

            if interface.poe_entry and interface.poe_entry.detect_status == POE_PORT_DETECT_DELIVERING:
                worksheet.write(
                    row, COL_INTERFACE_POE_DRAW, interface.poe_entry.power_consumed, spreadsheet.format_regular
                )

            worksheet.write(row, COL_INTERFACE_DESCRIPTION, interface.description, spreadsheet.format_regular)
            worksheet.write(row, COL_ETHERNET, str(eth), spreadsheet.format_regular)
            worksheet.write(row, COL_VENDOR, eth.vendor, spreadsheet.format_regular)
            # for IPv4 and IPv6, we keep multiple addresses, so handle the list:
            worksheet.write(row, COL_IPV4, ", ".join(eth.address_ip4), spreadsheet.format_regular)
            worksheet.write(row, COL_IPV6, ", ".join(eth.address_ip6), spreadsheet.format_regular)

        # and loop through lldp:
        for neighbor in interface.lldp.values():
            row += 1
            found_ip = False
            dprint(f"LLDP: on {interface.name} - {neighbor.sys_name}")
            worksheet.write(row, COL_INTERFACE_NAME, interface.name, spreadsheet.format_regular)
            worksheet.write(row, COL_INTERFACE_VLAN, interface.untagged_vlan, spreadsheet.format_regular)

            if interface.poe_entry and interface.poe_entry.detect_status == POE_PORT_DETECT_DELIVERING:
                worksheet.write(
                    row, COL_INTERFACE_POE_DRAW, interface.poe_entry.power_consumed, spreadsheet.format_regular
                )

            worksheet.write(row, COL_INTERFACE_DESCRIPTION, interface.description, spreadsheet.format_regular)

            # what kind of chassis address do we have (if any)
            if neighbor.chassis_type == LLDP_CHASSIC_TYPE_ETH_ADDR:
                worksheet.write(row, COL_ETHERNET, neighbor.chassis_string, spreadsheet.format_regular)
                worksheet.write(row, COL_VENDOR, neighbor.vendor, spreadsheet.format_regular)
            elif neighbor.chassis_type == LLDP_CHASSIC_TYPE_NET_ADDR:
                if neighbor.chassis_string_type == IANA_TYPE_IPV4:
                    worksheet.write(row, COL_IPV4, neighbor.chassis_string, spreadsheet.format_regular)
                    found_ip = True
                elif neighbor.chassis_string_type == IANA_TYPE_IPV6:
                    # TBD, IPv6 not supported yet.
                    dprint("  IPV6 chassis address: NOT supported yet")
                    # worksheet.write(row, COL_IPV6, neighbor.chassis_string, spreadsheet.format_regular)
            # if we don't have IP info yet, do we have management IP?
            if not found_ip and neighbor.management_address:
                if neighbor.management_address_type == IANA_TYPE_IPV4:
                    worksheet.write(row, COL_IPV4, neighbor.management_address, spreadsheet.format_regular)
                elif neighbor.management_address_type == IANA_TYPE_IPV6:
                    # TBD, IPv6 not supported yet.
                    dprint("  IPV6 management address: NOT supported yet")
                    # worksheet.write(row, COL_IPV6, neighbor.management_address, spreadsheet.format_regular)

            worksheet.write(row, COL_NEIGHBOR_NAME, neighbor.sys_name, spreadsheet.format_regular)
            worksheet.write(row, COL_NEIGHBOR_TYPE, neighbor.capabilities_as_string(), spreadsheet.format_regular)
            worksheet.write(row, COL_NEIGHBOR_DESCRIPTION, neighbor.sys_descr, spreadsheet.format_regular)


def create_interfaces_xls_file(connection: Connector):
    """Create an XLS temp file that contains the interface/port information for a device.

    Args:
        connection (Connector()): a valid Connector object, that has basic (interface) information filled in.

    Returns:
        (BytesIO() object), Error() ): an open stream, or an Error() object if that cannot be created,.
    """
    dprint("create_interfaces_xls_file()")

    (spreadsheet, reason) = create_workbook()
    if not spreadsheet:
        error = Error()
        error.description = "Error creating Excel file!"
        error.details = reason
        return False, error

    # all OK:
    try:
        create_interfaces_worksheet(spreadsheet=spreadsheet, connection=connection)
        spreadsheet.workbook.close()
    except Exception as err:  # trap all errors from above!
        error = Error()
        error.description = "Error adding content to Excel file!"
        error.details = f"ERROR: {err}"
        return False, error

    # all OK!
    spreadsheet.fh.seek(0)  # rewind to beginning of "file" for FileResponse() download
    return spreadsheet.fh, None


def create_eth_neighbor_xls_file(connection: Connector):
    """Create an XLS temp file that contains the ethernet and neighbors of a device.

    Args:
        connection (Connector()): a valid Connector object, that has ethernet and neighbor information filled in.

    Returns:
        (BytesIO() object), Error() ): an open stream, or an Error() object if that cannot be created,.
    """
    dprint("create_eth_neighbor_xls_file()")

    (spreadsheet, reason) = create_workbook()
    if not spreadsheet:
        error = Error()
        error.description = "Error creating Excel file!"
        error.details = reason
        return False, error

    # all OK:
    try:
        create_interfaces_worksheet(spreadsheet=spreadsheet, connection=connection)
        create_neighbors_worksheet(spreadsheet=spreadsheet, connection=connection)
        spreadsheet.workbook.close()
    except Exception as err:  # trap all errors from above!
        error = Error()
        error.description = "Error adding content to Excel file!"
        error.details = f"ERROR: {err}"
        return False, error

    # all OK!
    spreadsheet.fh.seek(0)  # rewind to beginning of "file" for FileResponse() download
    return spreadsheet.fh, None
