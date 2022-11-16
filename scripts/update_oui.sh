#!/usr/bin/env bash
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
# Script to update the Python netaddr module's Ethernet IAB/OUI library.
# See more at https://www.redelijkheid.com/blog/2019/5/10/update-python-netaddr-oui-database
#
# NOTE: you should run this *every* time you run upgrade.sh !!!
#

# this is where OpenL2M is installed. If you used a different path, update as needed:
WORKDIR="/opt/openl2m"

# here we go:
cd $WORKDIR

echo "Updating the OUI files for the netaddr package."
# activate the virtual environment
source venv/bin/activate

# get the path to the netaddr package
NETADDR_PATH=`python3 scripts/get_netaddr_path.py`

# double-check if a netaddr/eui directory inside the virtual env exists
if [ ! -d "$NETADDR_PATH/eui" ]
then
    echo " netaddr package directory '$NETADDR_PATH' not found!"
    echo " NOT updating the OUI database."
    exit 1
fi


# go to the netaddr install location inside the Virtual Environment:
echo "Changing to '$NETADDR_PATH/eui'"
cd "$NETADDR_PATH/eui"

# check that we are in the proper folder
if [ ! -f "ieee.py" ]
then
    echo " ieee.py does not exist in '$NETADDR_PATH/eui'!"
    echo " NOT updating the OUI database."
    exit 1
fi

# create backup copy of old files
cp iab.idx iab.idx.old
cp iab.txt iab.txt.old
cp oui.idx oui.idx.old
cp oui.txt oui.txt.old

# download new iab and oui files
echo "Downloading updates to two OUI files..."
wget http://standards-oui.ieee.org/iab/iab.txt --output-document=iab.txt
wget http://standards-oui.ieee.org/oui/oui.txt --output-document=oui.txt

# run the 'index creation script'
echo "Creating new database files for netaddr package..."
python3 ieee.py

echo "OUI updates finished!"
