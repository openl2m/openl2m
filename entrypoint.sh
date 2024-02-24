#!/bin/bash

echo "Starting initialization..."

cp openl2m/configuration.example.py openl2m/configuration.py

SECRET_KEY="${SECRET_KEY:-$(python3 generate_secret_key.py)}"
echo "SECRET_KEY = '$SECRET_KEY'" >> openl2m/configuration.py
echo "DEBUG = ${DEBUG:-False}" >> openl2m/configuration.py

cat <<EOF >> openl2m/configuration.py
DATABASE = {
    'NAME': '${DB_NAME:-openl2m}',      # Database name
    'USER': '${DB_USER:-openl2m}',      # PostgreSQL username
    'PASSWORD': '${DB_PASS:-changeme}', # PostgreSQL password
    'HOST': '${DB_HOST:-localhost}',               # Database server
    'PORT': '${DB_PORT:-}',         # Database port (leave blank for default)
}
EOF

python3 manage.py migrate

# echo -e "1234\n1234" | python3 manage.py createsuperuser \
#   --username ${ADMIN_USERNAME:-admin} \
#   --email ${ADMIN_EMAIL:-changeme@abc.xyz}

echo "Initialization done!"

python3 manage.py runserver 0:8000 --insecure
