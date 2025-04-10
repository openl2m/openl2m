#!/usr/bin/python3
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

# An example script to show how to access OpenL2M objects ...
# We show how to import User() and Switch() objects.

# Set the location of the Django openl2m project
# this should work from anywhere in your directory structure,
# as long as you point the PROJECT_DIR variable to the right place!
import sys
import argparse
import django
import os
import csv

PROJECT_DIR = "../openl2m/"

# insert location in front of path, so it is first one found!
sys.path.insert(0, PROJECT_DIR)

# initialize Django framework
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openl2m.settings')
django.setup()

from django.conf import settings

# load the User() object
from django.contrib.auth.models import User

# load various OpenL2M objects
from switches.models import Switch, SwitchGroup, SnmpProfile, NetmikoProfile, CommandList
from switches.constants import *


def main():
    # setup and parse arguments
    parser = argparse.ArgumentParser(description='Import Data from a CSV file.')

    parser.add_argument(
        '-u',
        '--userfile',
        type=str,
        dest='user_file',
        action='store',
        default='',
        required=False,
        help='the User CSV file to import',
    )

    parser.add_argument(
        '-s',
        '--switchfile',
        type=str,
        dest='switch_file',
        action='store',
        default='',
        required=False,
        help='the Switch CSV file to import',
    )

    args = parser.parse_args()

    if args.user_file:
        with open(args.user_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            print("\nImporting USERS")
            for row in reader:
                print("Found: " + row['username'])
                username = row['username']
                email = row['email']
                # current does not deal with hashed password (as required for import)
                password = row['password']
                try:
                    u = User.objects.create_user(username, email, password)
                except Exception:
                    print("   Error creating User '%s'" % row['username'])
                    print("   Error details: ", sys.exc_info()[0])
                    continue
                if 'staff' in row.keys():
                    u.is_staff = bool(row['staff'])
                if 'superuser' in row.keys():
                    u.is_superuser = bool(row['superuser'])
                u.save()
                print("   Import OK")
                # now add to group. Cannot do earlier, as new user object needs to exist!
                if 'group' in row.keys() and row['group']:
                    try:
                        group = Group.objects.get(name=row['group'])
                        group.user_set.add(u)
                    except Exception:
                        print("   Error adding user to group '%s'" % row['group'])
                        print("   Error details: %s" % sys.exc_info()[0])

    if args.switch_file:
        with open(args.switch_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            print("\nImporting SWITCHES")
            for row in reader:
                print("Found: " + row['name'])
                # see if switch object exists:
                try:
                    switch = Switch.objects.get(name=row['name'])
                    if not args.allow_update:
                        print("Existing switch found, but update NOT allowed!")
                        continue
                except Exception:
                    # not found, create new object:
                    switch = Switch()
                    switch.name = row['name']
                # now set all the values found:
                switch.primary_ip4 = row['primary_ip4']
                if 'description' in row.keys():
                    switch.description = row['description']
                if 'read_only' in row.keys():
                    switch.read_only = row['read_only']
                if 'default_view' in row.keys():
                    switch.default_view = row['default_view']
                # figure out the SnmpProfile
                if 'snmp_profile' in row.keys() and row['snmp_profile']:
                    try:
                        snmp = SnmpProfile.objects.get(name=row['snmp_profile'])
                        switch.snmp_profile = snmp
                    except Exception:
                        print("   Error getting valid SNMP Profile '%s'" % row['snmp_profile'])
                        print("   Error details: %s" % sys.exc_info()[0])
                        print("   We cannot import a switch with an invalid SNMP Profile!")
                        continue
                if 'netmiko_profile' in row.keys() and row['netmiko_profile']:
                    try:
                        nm = NetmikoProfile.objects.get(name=row['netmiko_profile'])
                        switch.netmiko_profile = nm
                    except Exception:
                        print("   Error getting Netmiko Profile '%s'" % row['netmiko_profile'])
                        print("   Error details: %s" % sys.exc_info()[0])
                        print("   We cannot import a switch with an invalid Netmiko Profile!")
                        continue
                if 'command_list' in row.keys() and row['command_list']:
                    try:
                        cl = CommandList.objects.get(name=row['command_list'])
                        switch.command_list = cl
                    except Exception:
                        # command list does not exist, create it!
                        cl = CommandList()
                        cl.name = row['command_list']  # the only mandatory field!
                        try:
                            cl.save()
                            print("   EMPTY Command List '%s' created, please edit as needed!" % row['command_list'])
                        except Exception:
                            print("   Error creating Command List '%s'" % row['command_list'])
                            print("   Error details: %s" % sys.exc_info()[0])
                            continue
                g = False
                if 'group' in row.keys() and row['group']:
                    # see if the group exists, if not, create it
                    try:
                        g = SwitchGroup.objects.get(name=row['group'])
                    except Exception:
                        # group does not exist yet, create it!
                        g = SwitchGroup()
                        g.name = row['group']
                        try:
                            g.save()
                            print("  SwitchGroup '%s' created" % row['group'])
                        except Exception:
                            print("   Error creating SwitchGroup '%s'" % row['group'])
                            print("   Error details: %s" % sys.exc_info()[0])
                            continue
                # save the new switch
                try:
                    switch.save()
                except Exception:
                    print("   Error saving new switch object for '%s'" % row['name'])
                    print("   Error details: %s" % sys.exc_info()[0])
                    continue
                if g:
                    # assign switch to the switchgroup
                    try:
                        g.switches.add(switch)
                    except Exception:
                        print("   Error adding switch to switchgroup, please do this manually!")
                        print("   Error details: %s" % sys.exc_info()[0])
                        continue
                print("   Import OK")


if __name__ == '__main__':
    main()
