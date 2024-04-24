#!/bin/bash

#
# docker entrypoint file for testing OpenL2M.
# Note: this is NOT meant to become a production setup!!!
#

echo "Starting initialization..."

BASEDIR=/opt/openl2m/
cp $BASEDIR/openl2m/configuration.example.py $BASEDIR/openl2m/configuration.py

SECRET_KEY="${SECRET_KEY:-$(python3 generate_secret_key.py)}"
echo "SECRET_KEY = '$SECRET_KEY'" >> $BASEDIR/openl2m/configuration.py
echo "DEBUG = ${DEBUG:-False}" >> $BASEDIR/openl2m/configuration.py

cat <<EOF >> $BASEDIR/openl2m/configuration.py
DATABASE = {
    'NAME': '${DB_NAME:-openl2m}',      # Database name
    'USER': '${DB_USER:-openl2m}',      # PostgreSQL username
    'PASSWORD': '${DB_PASS:-changeme}', # PostgreSQL password
    'HOST': '${DB_HOST:-localhost}',               # Database server
    'PORT': '${DB_PORT:-}',         # Database port (leave blank for default)
}
EOF

python3 manage.py migrate

echo "Updating Wireshark Ethernet database..."
python3 lib/manuf/manuf/manuf.py --update

echo "Initialization done!"

echo "OpenL2M will now start FOR TESTING PURPOSES ONLY!"
python3 manage.py runserver 0:8000 --insecure
