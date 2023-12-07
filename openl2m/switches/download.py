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
import time
from pathlib import Path
import platform
import tempfile
import pprint
import xlsxwriter

from django.http import FileResponse

from switches.connect.classes import Error
from switches.connect.constants import (
    LLDP_CHASSIC_TYPE_ETH_ADDR,
    LLDP_CHASSIC_TYPE_NET_ADDR,
    IANA_TYPE_IPV4,
    IANA_TYPE_IPV6,
)
from switches.utils import dprint, error_page


def send_file(request, filename):
    """Send a file as download to the user.

    Args:
        request (HttpRequest()): The request object.
        filename (str): The full path to the file to download.
    """
    dprint(f"send_file(filename='{filename}')")
    try:
        stream = open(filename, "rb")
    except Exception as err:
        dprint(f"ERROR opening file: {err}")
        error = Error()
        error.description = "Error opening file to download"
        error.details = f"{err}"
        return error_page(request=request, group=False, switch=False, error=error)
    else:
        return FileResponse(stream)


def create_eth_neighbor_xls_file(connection):
    """Create an XLS temp file that contains the ethernet and neighbors of a device.

    Args:
        connection (Connection()): a valid connection object, that has ethernet and neighbor information filled in.

    Returns:
        (str),(error): the full path to the temp file created, or an Error() object if that cannot be created,.
    """
    dprint("create_eth_neighbor_xls_file()")
    try:
        # create the Excel file
        tempdir = Path("/tmp" if platform.system() == "Darwin" else tempfile.gettempdir())
        temp_filename = f"{tempdir}/{connection.switch.name}-ethernet-neighbor-info.xlsx"

        workbook = xlsxwriter.Workbook(temp_filename)

        # Add some formats to use to highlight cells.
        format_bold = workbook.add_format({'bold': True, 'font_name': 'Calibri', 'font_size': 14})
        format_regular = workbook.add_format({'font_name': 'Calibri', 'font_size': 12})
        # add a tab
        worksheet = workbook.add_worksheet('Ethernet-Arp-LLDP')

        COL_INTERFACE = 0
        COL_ETHERNET = 1
        COL_IPV4 = 2
        COL_VENDOR = 3
        COL_NEIGHBOR_NAME = 4
        COL_NEIGHBOR_TYPE = 5
        COL_NEIGHBOR_DESCRIPTION = 6

        # start with a date message:
        row = 0
        worksheet.write(
            row,
            COL_INTERFACE,
            f"Ethernet and Neighbor data from '{connection.switch.name}' generated for '{connection.request.user}' on: {time.strftime('%d-%m-%Y, %H:%M:%S', time.localtime())}",
            format_bold,
        )

        # write header row
        row += 1
        worksheet.write(row, COL_INTERFACE, 'Interface', format_bold)
        worksheet.set_column(COL_INTERFACE, COL_INTERFACE, 30)  # Adjust the column width.

        worksheet.write(row, COL_ETHERNET, 'Ethernet', format_bold)
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
                worksheet.write(row, COL_INTERFACE, interface.name, format_regular)
                worksheet.write(row, COL_ETHERNET, str(eth), format_regular)
                worksheet.write(row, COL_VENDOR, eth.vendor, format_regular)
                worksheet.write(row, COL_IPV4, eth.address_ip4, format_regular)

            # and loop through lldp:
            for neighbor in interface.lldp.values():
                row += 1
                dprint(f"LLDP: on {interface.name} - {neighbor.sys_name}")
                worksheet.write(row, COL_INTERFACE, interface.name, format_regular)
                # what kind of chassis address do we have (if any)
                if neighbor.chassis_type == LLDP_CHASSIC_TYPE_ETH_ADDR:
                    worksheet.write(row, COL_ETHERNET, neighbor.chassis_string, format_regular)
                    worksheet.write(row, COL_VENDOR, neighbor.vendor, format_regular)
                elif neighbor.chassis_type == LLDP_CHASSIC_TYPE_NET_ADDR:
                    if neighbor.chassis_string_type == IANA_TYPE_IPV4:
                        worksheet.write(row, COL_IPV4, neighbor.chassis_string, format_regular)
                    elif neighbor.chassis_string_type == IANA_TYPE_IPV6:
                        # TBD, IPv6 not supported yet.
                        dprint("  IPV6 chassis address: NOT supported yet")
                        # worksheet.write(row, COL_IPV6, neighbor.chassis_string, format_regular)
                worksheet.write(row, COL_NEIGHBOR_NAME, neighbor.sys_name, format_regular)
                worksheet.write(row, COL_NEIGHBOR_TYPE, neighbor.capabilities_as_string(), format_regular)
                worksheet.write(row, COL_NEIGHBOR_DESCRIPTION, neighbor.sys_descr, format_regular)

        workbook.close()
    except Exception as err:  # trap all errors from above!
        error = Error()
        error.description = "Error creating Excel file!"
        error.details = f"ERROR: {err}"
        return "", error

    # all OK!
    return temp_filename, None
