#!/bin/bash
# This script comes from NetBox ! Thank you :-)
#
# This script will prepare OpenL2M to run after the code has been upgraded to
# its most recent release.
#
# Once the script completes, remember to restart the WSGI service (e.g.
# gunicorn or uWSGI).

cd "$(dirname "$0")"

PYTHON="python3"
PIP="pip3"
MAKE="make"
SYSTEMCTL="systemctl"

# Stop the gunicorn python service
#COMMAND="($SYSTEMCTL) stop openl2m"
#echo "Stopping OpenL2M Python service ($COMMAND)..."
#eval $COMMAND

# Delete bytecode to get fresh copy
COMMAND="find . -name \"*.pyc\" -delete"
echo "Cleaning up stale Python bytecode ($COMMAND)..."
eval $COMMAND

# Install any new Python packages
COMMAND="${PIP} install -r requirements.txt --upgrade"
echo "Updating required Python packages ($COMMAND)..."
eval $COMMAND

# Validate Python dependencies
COMMAND="${PIP} check"
echo "Validating Python dependencies ($COMMAND)..."
eval $COMMAND || (
  echo "******** PLEASE FIX THE DEPENDENCIES BEFORE CONTINUING ********"
  echo "* Manually install newer version(s) of the highlighted packages"
  echo "* so that 'pip3 check' passes. For more information see:"
  echo "* https://github.com/pypa/pip/issues/988"
  exit 1
)

# Apply any database migrations
COMMAND="${PYTHON} openl2m/manage.py migrate"
echo "Applying database migrations ($COMMAND)..."
eval $COMMAND

# Recompile the documentation
COMMAND="cd docs; $MAKE html; cd .."
echo "Updating HTML documentation ($COMMAND)..."
eval $COMMAND

# Delete any stale content types
COMMAND="${PYTHON} openl2m/manage.py remove_stale_contenttypes --no-input"
echo "Removing stale content types ($COMMAND)..."
eval $COMMAND

# Collect static files
COMMAND="${PYTHON} openl2m/manage.py collectstatic --no-input"
echo "Collecting static files ($COMMAND)..."
eval $COMMAND

# Restart the python service
#COMMAND="($SYSTEMCTL) start openl2m"
#echo "Starting OpenL2M Python service ($COMMAND)..."
#eval $COMMAND
