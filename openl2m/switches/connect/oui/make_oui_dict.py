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

#
# read the oui.txt file in this directory,
# and create the file oui_dict.py, which defines dictionary
# with vendor info for each know oui.
#
import sys
import re

# quick hack :-)

# match this format:
# E0-43-DB   (hex)		Shenzhen ViewAt Technology Co. Ltd
OUI_PATTERN = "^(\w\w-\w\w-\w\w)\s+\(\w+\)\s+(.*)$"

# input data
infile = open("oui.txt")
if not infile:
    print("ERROR: cannot open oui.txt")
    sys.exit

# output file
outfile = open("oui_dict.py", "w")
if not outfile:
    print("ERROR: cannot write oui.py")
    sys.exit

outfile.write("# Auto-generated file, see readme\n\noui_to_vendor = {}\n")

line = infile.readline()
while line:
    match = re.match(OUI_PATTERN, line)
    if match:
        # print("OUI = " + match[1])
        # print("Vendor = " + match[2])
        outfile.write("oui_to_vendor['%s'] = \"%s\"\n" % (match[1], match[2]))
    line = infile.readline()

outfile.close()
infile.close()
