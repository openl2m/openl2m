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

# Custom command line commands, see also:
#    https://docs.djangoproject.com/en/2.2/howto/custom-management-commands/
#    https://simpleisbetterthancomplex.com/tutorial/2018/08/27/how-to-create-custom-django-management-commands.html
import sys
import csv

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from switches.models import *
from switches.constants import *


class Command(BaseCommand):
    help = 'Import CSV files with Switches, etc.'

    def add_arguments(self, parser):
        # Positional arguments - NONE

        # optional commands
        parser.add_argument(
            '--switchgroups',
            type=str,
            help='the SwitchGroup CSV file to import'
        )

        parser.add_argument(
            '--commands',
            type=str,
            help='the Commands CSV file to import'
        )

        parser.add_argument(
            '--switches',
            type=str,
            help='the Switch CSV file to import'
        )

        parser.add_argument(
            '--netmiko',
            type=str,
            help='the Netmiko Profile CSV file to import'
        )

        parser.add_argument(
            '--snmp',
            type=str,
            help='the SNMP Profile CSV file to import'
        )

        parser.add_argument(
            '--users',
            type=str,
            help='the User CSV file to import'
        )

        parser.add_argument(
            '--vlans',
            type=str,
            help='the VLAN CSV file to import'
        )

        parser.add_argument(
            '--update',
            action='store_true',
            help='update object if it exists'
        )

    def handle(self, *args, **options):
        update = options['update']

        commands_file = options['commands']
        if commands_file:
            with open(commands_file, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                self.stdout.write("Importing Commands")
                for row in reader:
                    # print(row)
                    if 'name' not in row.keys():
                        print("'name' field is required!")
                        sys.exit()
                    self.stdout.write("Found: %s" % row['name'])
                    try:
                        c = Command.objects.get(name=row['name'], type=row['os'])
                        if not update:
                            self.stdout.write(self.style.WARNING("Command %s already exists, but update NOT allowed!" % row['name']))
                            continue
                    except Exception:
                        c = Command()
                        c.name = row['name']   # the only mandatory field!
                    # the remaining fields
                    if 'description' in row.keys():
                        c.description = row['description']
                    if 'type' in row.keys():
                        c.type = row['type']
                    if 'command' in row.keys():
                        c.command = row['command']
                    if 'os' in row.keys():
                        c.os = row['os']
                    try:
                        c.save()
                    except Exception:
                        self.stdout.write(self.style.ERROR("   Error saving Command '%s'" % row['name']))
                        self.stdout.write(self.style.ERROR("   Error details: %s" % sys.exc_info()[0]))
                        continue
                    self.stdout.write(self.style.SUCCESS("   Save OK"))

        switchgroup_file = options['switchgroups']
        if switchgroup_file:
            with open(switchgroup_file, newline='') as csvfile:
                # see the comment about newline at https://docs.python.org/3/library/csv.html
                # to make sure "\n" in strings gets properly parsed!
                reader = csv.DictReader(csvfile)
                self.stdout.write("Importing SwitchGroups")
                for row in reader:
                    # print(row)
                    if 'name' not in row.keys():
                        print("'name' field is required!")
                        sys.exit()
                    self.stdout.write("Found: %s" % row['name'])
                    try:
                        g = SwitchGroup.objects.get(name=row['name'])
                        self.stdout.write(self.style.WARNING("SwitchGroup %s already exists!" % row['name']))
                        continue
                    except Exception:
                        # create new group
                        g = SwitchGroup()
                        g.name = row['name']
                    try:
                        g.save()
                        self.stdout.write(self.style.SUCCESS("   Save OK"))
                    except Exception:
                        self.stdout.write(self.style.ERROR("   Error saving SwitchGroup '%s'" % row['name']))
                        self.stdout.write(self.style.ERROR("   Error details: %s" % sys.exc_info()[0]))
                        continue

        user_file = options['users']
        if user_file:
            with open(user_file, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                self.stdout.write("Importing Users")
                for row in reader:
                    # print(row)
                    if 'username' not in row.keys():
                        print("'username' field is required!")
                        sys.exit()
                    if 'email' not in row.keys():
                        print("'email' field is required!")
                        sys.exit()
                    if 'password' not in row.keys():
                        print("'password' field is required!")
                        sys.exit()
                    self.stdout.write("Found: %s" % row['username'])
                    username = row['username']
                    email = row['email']
                    # current does not deal with hashed password (as required for import)
                    password = row['password']
                    try:
                        u = User.objects.create_user(username, email, password)
                    except Exception:
                        self.stdout.write(self.style.ERROR("   Error creating User '%s'" % row['username']))
                        self.stdout.write(self.style.ERROR("   Error details: ", sys.exc_info()[0]))
                        continue
                    if 'staff' in row.keys():
                        u.is_staff = bool(row['staff'])
                    if 'superuser' in row.keys():
                        u.is_superuser = bool(row['superuser'])
                    u.save()
                    self.stdout.write(self.style.SUCCESS("   Import OK"))
                    # now add to group. Cannot do earlier, as new user object needs to exist!
                    if 'group' in row.keys() and row['group']:
                        try:
                            group = Group.objects.get(name=row['group'])
                            group.user_set.add(u)
                        except Exception:
                            self.stdout.write(self.style.ERROR("   Error adding user to group '%s'" % row['group']))
                            self.stdout.write(self.style.ERROR("   Error details: %s" % sys.exc_info()[0]))

        vlan_file = options['vlans']
        if vlan_file:
            with open(vlan_file, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                self.stdout.write("Importing VLANs")
                for row in reader:
                    # print(row)
                    if 'name' not in row.keys():
                        print("'name' field is required!")
                        sys.exit()
                    self.stdout.write("Found: %s" % row['name'])
                    # are we updating?
                    try:
                        v = VLAN.objects.get(vid=row['vid'], name=row['name'])
                        if not update:
                            self.stdout.write(self.style.WARNING("Existing VLAN found, but update NOT allowed!"))
                            continue
                    except Exception:
                        # create new vlan:
                        v = VLAN()
                        v.vid = int(row['vid'])
                        v.name = row['name']
                    # set or update values:
                    if 'description' in row.keys():
                        v.description = row['description']
                    if 'contact' in row.keys():
                        v.contact = row['contact']
                    try:
                        v.save()
                    except Exception:
                        self.stdout.write(self.style.ERROR("   Error saving VLAN '%s'" % row['name']))
                        self.stdout.write(self.style.ERROR("   Error details: %s" % sys.exc_info()[0]))
                        continue
                    self.stdout.write(self.style.SUCCESS("   Save OK"))

        switch_file = options['switches']
        if switch_file:
            with open(switch_file, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                self.stdout.write("Importing Switches")
                for row in reader:
                    # print(row)
                    if 'name' not in row.keys():
                        print("'name' field is required!")
                        sys.exit()
                    self.stdout.write("Found: %s" % row['name'])
                    # see if switch object exists:
                    try:
                        switch = Switch.objects.get(name=row['name'])
                        if not update:
                            self.stdout.write(self.style.WARNING("Existing switch found, but update NOT allowed!"))
                            continue
                    except Exception:
                        # not found, create new object:
                        switch = Switch()
                        switch.name = row['name']
                    # now set all the values found:
                    if 'primary_ip4' in row.keys():
                        switch.primary_ip4 = row['primary_ip4']
                    else:
                        print("'primary_ip4' field is required!")
                        sys.exit()
                    if 'description' in row.keys():
                        switch.description = row['description']
                    if 'read_only' in row.keys():
                        switch.read_only = row['read_only']
                    if 'default_view' in row.keys():
                        switch.default_view = row['default_view']
                    if 'indent_level' in row.keys():
                        switch.indent_level = int(row['indent_level'])
                    if 'nms_id' in row.keys():
                        switch.nms_id = row['nms_id']
                    # figure out the SnmpProfile
                    if 'snmp_profile' in row.keys() and row['snmp_profile']:
                        try:
                            snmp = SnmpProfile.objects.get(name=row['snmp_profile'])
                            switch.snmp_profile = snmp
                        except Exception:
                            self.stdout.write(self.style.ERROR("   Error getting valid SNMP Profile '%s'" % row['snmp_profile']))
                            self.stdout.write(self.style.ERROR("   Error details: %s" % sys.exc_info()[0]))
                            self.stdout.write(self.style.ERROR("   We cannot import a switch with an invalid SNMP Profile!"))
                            continue
                    if 'netmiko_profile' in row.keys() and row['netmiko_profile']:
                        try:
                            nm = NetmikoProfile.objects.get(name=row['netmiko_profile'])
                            switch.netmiko_profile = nm
                        except Exception:
                            self.stdout.write(self.style.ERROR("   Error getting Netmiko Profile '%s'" % row['netmiko_profile']))
                            self.stdout.write(self.style.ERROR("   Error details: %s" % sys.exc_info()[0]))
                            self.stdout.write(self.style.ERROR("   We cannot import a switch with an invalid Netmiko Profile!"))
                            continue
                    if 'command_list' in row.keys() and row['command_list']:
                        try:
                            cl = CommandList.objects.get(name=row['command_list'])
                            switch.command_list = cl
                        except Exception:
                            # command list does not exist, create a new, empty command list!
                            cl = CommandList()
                            cl.name = row['command_list']   # the only mandatory field!
                            try:
                                cl.save()
                                self.stdout.write(self.style.WARNING("   EMPTY Command List '%s' created, please edit as needed!" % row['command_list']))
                            except Exception:
                                self.stdout.write(self.style.ERROR("   Error creating Command List '%s'" % row['command_list']))
                                self.stdout.write(self.style.ERROR("   Error details: %s" % sys.exc_info()[0]))
                                continue
                    if 'group' in row.keys() and row['group']:
                        # see if the group exists, if not, create it
                        g = False
                        try:
                            g = SwitchGroup.objects.get(name=row['group'])
                        except Exception:
                            # group does not exist yet, create it!
                            g = SwitchGroup()
                            g.name = row['group']
                            try:
                                g.save()
                                self.stdout.write(self.style.SUCCESS("  SwitchGroup '%s' created" % row['group']))
                            except Exception:
                                self.stdout.write(self.style.ERROR("   Error creating SwitchGroup '%s'" % row['group']))
                                self.stdout.write(self.style.ERROR("   Error details: %s" % sys.exc_info()[0]))
                                g = False

                    try:
                        switch.save()
                    except Exception:
                        self.stdout.write(self.style.ERROR("   Error saving new switch object for '%s'" % row['name']))
                        self.stdout.write(self.style.ERROR("   Error details: %s" % sys.exc_info()[0]))
                        continue
                    if g:
                        # assign switch to the switchgroup
                        try:
                            g.switches.add(switch)
                        except Exception:
                            self.stdout.write(self.style.ERROR("   Error adding switch to switchgroup '%s', please do this manually!" % g.name))
                            self.stdout.write(self.style.ERROR("   Error details: %s" % sys.exc_info()[0]))
                            continue
                    self.stdout.write(self.style.SUCCESS("   Import OK"))

        netmiko_file = options['netmiko']
        if netmiko_file:
            with open(netmiko_file, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                self.stdout.write("Importing Netmiko Profile")
                for row in reader:
                    # print(row)
                    if 'name' not in row.keys():
                        print("'name' field is required!")
                        sys.exit()
                    self.stdout.write("Found: %s" % row['name'])
                    try:
                        nm = NetmikoProfile.objects.get(name=row['name'])
                        if not update:
                            self.stdout.write(self.style.WARNING("Existing NetmikeProfile found, but update NOT allowed!"))
                            continue
                    except Exception:
                        # create new
                        nm = NetmikoProfile()
                        nm.name = row['name']    # mandatory
                    # update the rest
                    nm.username = row['username']    # mandatory
                    nm.password = row['password']    # mandatory
                    nm.device_type = row['device_type']     # mandatory

                    if 'description' in row.keys():
                        nm.description = row['description']

                    if 'tcp_port' in row.keys():
                        nm.tcp_port = int(row['tcp_port'])

                    if 'verify_hostkey' in row.keys():
                        nm.verify_hostkey = bool(row['verify_hostkey'])

                    if 'secret' in row.keys():
                        nm.secret = bool(row['secret'])

                    try:
                        nm.save()
                    except Exception:
                        self.stdout.write(self.style.ERROR("   Error saving Netmiko Profile '%s'" % row['name']))
                        self.stdout.write(self.style.ERROR("   Error details: %s" % sys.exc_info()[0]))
                        continue
                    self.stdout.write(self.style.SUCCESS("   Import OK"))

        snmp_file = options['snmp']
        if snmp_file:
            with open(snmp_file, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                self.stdout.write("Importing SNMP Profile")
                for row in reader:
                    # print(row)
                    if 'name' not in row.keys():
                        print("'name' field is required!")
                        sys.exit()
                    self.stdout.write("Found: %s" % row['name'])
                    try:
                        s = SnmpProfile.objects.get(name=row['name'])
                        if not update:
                            self.stdout.write(self.style.WARNING("Existing SnmpProfile found, but update NOT allowed!"))
                            continue
                    except Exception:
                        # create new
                        s = SnmpProfile()
                        s.name = row['name']    # mandatory
                    # now update the rest
                    s.version = int(row['version'])     # mandatory

                    if 'description' in row.keys():
                        s.description = row['description']

                    if 'community' in row.keys():
                        s.community = row['community']

                    if 'udp_port' in row.keys():
                        s.udp_port = int(row['udp_port'])

                    if 'username' in row.keys():
                        s.username = row['username']

                    if 'passphrase' in row.keys():
                        s.passphrase = row['passphrase']

                    if 'priv_passphrase' in row.keys():
                        s.priv_passphrase = row['priv_passphrase']

                    if 'auth_protocol' in row.keys():
                        if row['auth_protocol'] == "MD5":
                            s.auth_protocol = SNMP_V3_AUTH_MD5
                        elif row['auth_protocol'] == "SHA":
                            s.auth_protocol = SNMP_V3_AUTH_SHA

                    if 'priv_protocol' in row.keys():
                        if row['priv_protocol'] == "DES":
                            s.priv_protocol = SNMP_V3_PRIV_DES
                        elif row['priv_protocol'] == "AES":
                            s.priv_protocol = SNMP_V3_PRIV_AES

                    if 'sec_level' in row.keys():
                        if row['sec_level'] == 'NoAuth-NoPriv':
                            s.sec_level = SNMP_V3_SECURITY_NOAUTH_NOPRIV
                        elif row['sec_level'] == 'Auth-NoPriv':
                            s.sec_level = SNMP_V3_SECURITY_AUTH_NOPRIV
                        elif row['sec_level'] == 'Auth-Priv':
                            s.sec_level = SNMP_V3_SECURITY_AUTH_PRIV

                    try:
                        s.save()
                    except Exception:
                        self.stdout.write(self.style.ERROR("   Error saving SNMP Profile '%s'" % row['name']))
                        self.stdout.write(self.style.ERROR("   Error details: %s" % sys.exc_info()[0]))
                        continue
                    self.stdout.write(self.style.SUCCESS("   Import OK"))
