#!/bin/bash
# This script comes from NetBox ! Thank you :-)
#
# This script will prepare OpenL2M to run after the code has been upgraded to
# its most recent release.
#
# Once the script completes, remember to restart the WSGI service
# (e.g.  systemctl restart openl2m )

# Use the python interpreter from the PYTHON environment variable,
# or fall back to the system python binary.
PYTHON="${PYTHON:-python3}"

# See if the user want an alternate version of Python at set in a config file:
if [ -f "altpython.sh" ]; then
  source "altpython.sh"
  echo "Using Alternate Python version at '${PYTHON}'"
fi

# From netbox:
# Validate the minimum required Python version
COMMAND="${PYTHON} -c 'import sys; exit(1 if sys.version_info < (3, 8) else 0)'"
PYTHON_VERSION=$(eval "${PYTHON} -V")
eval $COMMAND || {
  echo "--------------------------------------------------------------------"
  echo "ERROR: Unsupported Python version: ${PYTHON_VERSION}. OpenL2M requires"
  echo "Python 3.8 or later. To specify an alternate Python executable, set"
  echo "the PYTHON environment variable. For example:"
  echo ""
  echo "  sudo PYTHON=/usr/bin/python3.8 ./upgrade.sh"
  echo ""
  echo "To show your current Python version: ${PYTHON} -V"
  echo "--------------------------------------------------------------------"
  exit 1
}
echo "Using ${PYTHON_VERSION}"

cd "$(dirname "$0")"
VIRTUALENV="$(pwd -P)/venv"

# Remove the existing virtual environment (if any)
if [ -d "$VIRTUALENV" ]; then
  echo "Found existing virt environment at $VIRTUALENV"
  COMMAND="rm -rf ${VIRTUALENV}"
  echo "Removing old virtual environment..."
  eval $COMMAND
fi

# Create a new virtual environment
COMMAND="${PYTHON} -m venv ${VIRTUALENV}"
echo "Creating a new virtual environment at ${VIRTUALENV}..."
eval $COMMAND || {
  echo "--------------------------------------------------------------------"
  echo "ERROR: Failed to create the virtual environment. Check that you have"
  echo "the required system packages installed and the following path is"
  echo "writable: ${VIRTUALENV}"
  echo "--------------------------------------------------------------------"
  exit 1
}

# Activate the virtual environment
source "${VIRTUALENV}/bin/activate"

# Install latest pip
COMMAND="pip3 install --upgrade pip"
echo "Installing latest pip ($COMMAND)..."
eval $COMMAND || exit 1

# Install necessary system packages
COMMAND="pip3 install --upgrade wheel setuptools"
echo "Installing Python system packages ($COMMAND)..."
eval $COMMAND || exit 1

# Pre-Install some Python packages to work around things:
COMMAND="pip3 install six"
echo "Pre-installing dependencies ($COMMAND)..."
eval $COMMAND || exit 1

# Install required Python packages
COMMAND="pip3 install -r requirements.txt"
echo "Installing core dependencies ($COMMAND)..."
eval $COMMAND || exit 1

# Install optional packages (if any)
if [ -s "local_requirements.txt" ]; then
  COMMAND="pip install -r local_requirements.txt"
  echo "Installing local dependencies ($COMMAND)..."
  eval $COMMAND || exit 1
elif [ -f "local_requirements.txt" ]; then
  echo "Skipping local dependencies (local_requirements.txt is empty)"
else
  echo "Skipping local dependencies (local_requirements.txt not found)"
fi

# Apply any database migrations
COMMAND="python3 openl2m/manage.py migrate"
echo "Applying database migrations ($COMMAND)..."
eval $COMMAND || exit 1

cd docs

# Recompile the documentation, these become django static files!
COMMAND="make clean; make html"
echo "Updating HTML documentation ($COMMAND)..."
eval $COMMAND || exit 1

cd ..

# Collect static files
COMMAND="python3 openl2m/manage.py collectstatic --no-input"
echo "Collecting static files ($COMMAND)..."
eval $COMMAND || exit 1

# Delete any stale content types
COMMAND="python3 openl2m/manage.py remove_stale_contenttypes --no-input"
echo "Removing stale content types ($COMMAND)..."
eval $COMMAND || exit 1

# Delete any expired user sessions
COMMAND="python3 openl2m/manage.py clearsessions"
echo "Removing expired user sessions ($COMMAND)..."
eval $COMMAND || exit 1

# update the 'mnauf' package database,
# i.e. the Wireshark Ethernet Manufacturers database
echo
echo "Updating Wireshark Ethernet database..."
COMMAND="python3 openl2m/lib/manuf/manuf/manuf.py --update"
eval $COMMAND || exit 1

# All done!
echo
echo "OpenL2M upgrade complete! Don't forget to restart the OpenL2M service:"
echo "    sudo systemctl restart openl2m"
echo
echo "If you are using scheduled tasks, don't forget to restart the Celery service:"
echo "    sudo systemctl restart celery"
echo

# Restart the python service
#COMMAND="($SYSTEMCTL) restart openl2m"
#echo "Starting OpenL2M Python service ($COMMAND)..."
#eval $COMMAND
# Restart the celery service
#COMMAND="($SYSTEMCTL) restart celery"
#echo "Starting OpenL2M Celery service ($COMMAND)..."
#eval $COMMAND
