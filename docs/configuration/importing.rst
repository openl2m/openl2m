.. image:: ../_static/openl2m_logo.png

========================
Importing Switches, etc.
========================

**Importing configuration**

Most configuration objects can be imported from CSV.
We provide the built-in admin command "import_csv":

.. code-block:: bash

    python3 manage.py import_csv --help
    usage: manage.py import_csv [-h] [--switchgroups SWITCHGROUPS]
                               [--commands COMMANDS] [--switches SWITCHES]
                               [--netmiko NETMIKO] [--snmp SNMP] [--users USERS]
                               [--vlans VLANS] [--update]

    Import CSV files with Switches, etc.

    optional arguments:
     -h, --help            show this help message and exit
     --switchgroups SWITCHGROUPS
                           the SwitchGroup CSV file to import
     --commands COMMANDS   the Commands CSV file to import
     --switches SWITCHES   the Switch CSV file to import
     --netmiko NETMIKO     the Netmiko Profile CSV file to import
     --snmp SNMP           the SNMP Profile CSV file to import
     --users USERS         the User CSV file to import
     --vlans VLANS         the VLAN CSV file to import
     --update              update object if it exists


See the /scripts/example_csv/ folder for some examples of CSV files.
You can run the following command to import them all:

.. code-block:: bash

  cd scripts/csv_examples/
  python3 ../../openl2m/manage.py import_csv
    --switchgroup groups.csv --users users.csv
    --netmiko netmiko.csv --commands commandlists.csv
    --snmp snmp.csv --switches switches.csv --vlans vlans.csv


Note that you will need to import all snmp and netmiko 'profile' entries first,
before you can reference (use) them from Switches. New groups referenced will be
automatically created if not found at time of importing a user or switch.

==============
Custom imports
==============

You can write custom import scripts as outlined in the
:doc:`writing scripts<scripts>` section. If you submit them, we can add
these to the OpenL2M distribution.
