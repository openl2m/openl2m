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
"""
SNMP Library for OpenL2M, based on MIB-2 based RFC standards. Uses the pysnmp library.
Some of the code here is inspired by the NAV (Network Administration Visualized) tool
Various vendor specific implementations that augment this class exist.
"""
import sys
import time
import timeit
import re
import traceback
import pprint
from django.conf import settings
from django.contrib.auth.models import User
import easysnmp
from easysnmp.variables import SNMPVariable
from pysnmp.hlapi import *
from pysnmp.proto.rfc1902 import ObjectName, OctetString

from switches.constants import *
from switches.models import Switch, VLAN, SnmpProfile, Log
from switches.connect.constants import *
from switches.connect.classes import *
from switches.connect.connect import *
from switches.connect.netmiko.connector import *
from switches.connect.vendors.constants import *
from switches.connect.oui.oui import *
from switches.utils import *


class pysnmpHelper():
    """
    Implement functionality we need to do a few simple things.
    We use the "pysnmp" library primarily for help with OctetString / BitMap values.
    EasySNMP cannot handle this cleanly, especially for uneven byte counts, due to
    how it maps everything to a unicode string internally!
    Based on the pysnmp HPAPI at http://snmplabs.com/pysnmp/examples/contents.html#high-level-snmp
    """
    def __init__(self, switch=False):
        """
        Initialize the PySnmp bindings
        """
        self.switch = switch    # the Switch() object
        self._set_auth_data()
        self.error = Error()

    def get(self, oid):
        """
        Get a single specific OID value via SNMP
        Update the local OID cache by default.
        Returns a tuple with (error_status (bool), return_value)
        if error, then return_value is string with reason for error
        """
        if not self.switch:
            return (True, "Switch() NOT set!")
        if not self._auth_data:
            return (True, "Auth Data NOT set!")

        # Get a variable using an SNMP GET
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(self._auth_data,
                   UdpTransportTarget((self.switch.primary_ip4, self.switch.snmp_profile.udp_port)),
                   ContextData(),
                   ObjectType(ObjectName(oid)),
                   lookupMib=False,
                   )
        )

        if errorIndication:
            details = "ERROR with SNMP Engine: %s at %s" % (pprint.pformat(errorStatus),
                                                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?')
            return (True, details)

        elif errorStatus:
            details = "ERROR in SNMP PDU: %s at %s" % (pprint.pformat(errorStatus),
                                                       errorIndex and varBinds[int(errorIndex) - 1][0] or '?')
            return (True, details)

        else:
            # store the returned data
            (oid, retval) = varBinds
            return (False, retval)

    def _set(self, vars):
        """
        Set a single OID value. Note that 'value' has to be properly typed, see
        http://snmplabs.com/pysnmp/docs/api-reference.html#pysnmp.smi.rfc1902.ObjectType
        """
        if not self._auth_data:
            return (True, "Auth Data NOT set!")

        errorIndication, errorStatus, errorIndex, varBinds = next(
            setCmd(SnmpEngine(),
                   self._auth_data,
                   UdpTransportTarget((self.switch.primary_ip4, self.switch.snmp_profile.udp_port)),
                   ContextData(),
                   *vars,
                   lookupMib=False,
                   )
        )

        if errorIndication:
            details = "ERROR with SNMP Engine: %s at %s" % (pprint.pformat(errorStatus),
                                                            errorIndex and varBinds[int(errorIndex) - 1][0] or '?')
            return (True, details)

        elif errorStatus:
            details = "ERROR in SNMP PDU: %s at %s" % (pprint.pformat(errorStatus),
                                                       errorIndex and varBinds[int(errorIndex) - 1][0] or '?')
            return (True, details)

        else:
            # no errors
            return (False, None)

    def set(self, oid, value):
        """
        Set a single OID value. Note that 'value' has to be properly typed, see
        http://snmplabs.com/pysnmp/docs/api-reference.html#pysnmp.smi.rfc1902.ObjectType
        """
        if not self._auth_data:
            return (True, "Auth Data NOT set!")

        var = []
        var.append(ObjectType(ObjectIdentity(ObjectName(oid)), value))
        return self._set(var)

    def set_multiple(self, oid_tuples):
        """
        Set multiple OIDs in a single atomic snmp set()
        oid_tuples is a list of tuples (oid, value) containing
        the oid as a string, and a properly typed value,
        e.g. OctetString, Integer32, etc...
        """
        # first format in the varBinds format needed by pysnmp:
        vars = []
        for (oid, value) in oid_tuples:
            vars.append(ObjectType(ObjectIdentity(ObjectName(oid)), value))
        # now call _set() to do the work:
        return self._set(vars)

    def _set_auth_data(self):
        """
        Set the UsmUserdata() or CommunityData() object based on the snmp_profile
        """
        if not self.switch:
            # we need a Switch() object!
            return False

        if(self.switch.snmp_profile.version == SNMP_VERSION_2C):
            self._auth_data = CommunityData(self.switch.snmp_profile.community)
            return True

        if (self.switch.snmp_profile.version == SNMP_VERSION_3):
            # NoAuthNoPriv
            if self.switch.snmp_profile.sec_level == SNMP_V3_SECURITY_NOAUTH_NOPRIV:
                self._auth_data = UsmUserdata(self.switch.snmp_profile.username)
                return True

            # AuthNoPriv
            elif self.switch.snmp_profile.sec_level == SNMP_V3_SECURITY_AUTH_NOPRIV:
                if self.switch.snmp_profile.auth_protocol == SNMP_V3_AUTH_MD5:
                    self._auth_data = UsmUserData(self.switch.snmp_profile.username,
                                                  self.switch.snmp_profile.passphrase)

                elif self.switch.snmp_profile.auth_protocol == SNMP_V3_AUTH_SHA:
                    self._auth_data = UsmUserData(self.switch.snmp_profile.username,
                                                  self.switch.snmp_profile.passphrase,
                                                  authProtocol=usmHMACSHAAuthProtocol)
                return True

            # AuthPriv
            elif self.switch.snmp_profile.sec_level == SNMP_V3_SECURITY_AUTH_PRIV:
                authOptions = {}
                # authentication protocol
                if self.switch.snmp_profile.auth_protocol == SNMP_V3_AUTH_MD5:
                    authOptions[authProtocol] = usmHMACMD5AuthProtocol
                elif elf.switch.snmp_profile.auth_protocol == SNMP_V3_AUTH_SHA:
                    authOptions[authProtocol] = usmHMACSHAAuthProtocol

                # privacy protocol
                if self.switch.snmp_profile.priv_protocol == SNMP_V3_PRIV_DES:
                    authOptions[privProtocol] = usmDESPrivProtocol
                elif self.switch.snmp_profile.priv_protocol == SNMP_V3_PRIV_AES:
                    authOptions[privProtocol] = usmAesCfb128Protocol

                self._auth_data = UsmUserData(self.switch.snmp_profile.username,
                                              self.switch.snmp_profile.passphrase,
                                              self.switch.snmp_profile.priv_passphrase,
                                              authOptions)
                return True
            else:
                # unknown security level!
                self.error.status = True
                self.error.description = "Unknown Security Level!"
                return False

        # unknown version!
        self.error.status = True
        self.error.description = "Version %s not supported!" % self.switch.snmp_profile.version
        return False


class EasySNMP():
    """
    This is the base class that implements the EasySNMP interface for high-performing SNMP walks.
    """
    def __init__(self, switch):
        """
        Implements base functionality we need from EasySnmp
        """
        self.switch = switch    # the Switch() object
        self._snmp_session = False   # EasySNMP session object
        self.error = Error()

    def _get(self, oid, update_oidcache=True, parser=False):
        """
        Get a single specific OID value via SNMP
        Update the local OID cache by default.
        Returns a tuple with (error_status, return_value)
        if error, then return_value is not defined
        """
        self.error.clear()

        # Set a variable using an SNMP SET
        try:
            retval = self._snmp_session.get(oids=oid)
        except Exception as e:
            self.error.status = True
            self.error.description = "Access denied"
            self.error.details = "SNMP Error: %s (%s)\n%s" % (repr(e), str(type(e)), traceback.format_exc())
            return (True, None)

        # we cache all values as strings, just like the original returns from get_branch()
        self._parse_oid_and_cache("%s.%s" % (retval.oid, retval.oid_index),
                                  str(retval.value), retval.snmp_type, update_oidcache, parser)
        # update the local cache as needed by saving in the session:
        if update_oidcache:
            self._set_http_session_cache()

        return (False, retval)

    def _get_branch_by_name(self, branch_name, cache_it=True, parser=False, max_repetitions=settings.SNMP_MAX_REPETITIONS):
        """
        Bulk-walk a branch of the snmp mib, fill the data in the oid store.
        This finishes when we leave this branch.
        branch_name = SNMP name
        cache_it = True - we will save data in http session oid_cache
        parser - if given, will be a function to call to parse the MIB data.
        Return count of objects returned from query, or -1 if error.
        """
        if branch_name not in snmp_mib_variables.keys():
            warning = "ERROR: invalid branch name '%s'" % branch_name
            self._add_warning(warning)
            dprint("+++> INVALID BRANCH NAME: %s" % branch_name)
            return -1

        start_oid = snmp_mib_variables[branch_name]
        # Perform an SNMP walk
        self.error.clear()
        count = 0
        try:
            start = time.time()
            dprint("_get_branch_by_name(%s) BulkWalk %s" % (branch_name, start_oid))
            items = self._snmp_session.bulkwalk(oids=start_oid, non_repeaters=0, max_repetitions=max_repetitions)
            stop = time.time()
            # Each returned item can be used normally as its related type (str or int)
            # but also has several extended attributes with SNMP-specific information
            for item in items:
                count = count + 1
                # for octetstring, use this:  https://github.com/kamakazikamikaze/easysnmp/issues/91
                dprint("\n\n====> SNMP READ: {oid}.{oid_index} {snmp_type} = {var_type}: {value}".format(
                    oid=item.oid,
                    oid_index=item.oid_index,
                    snmp_type=item.snmp_type,
                    value=item.value,
                    var_type=str(type(item.value)),
                ))
                oid_found = '{oid}.{oid_index}'.format(
                    oid=item.oid,
                    oid_index=item.oid_index)
                self._parse_oid_and_cache(oid_found, item.value, item.snmp_type, cache_it, parser)    # write to local OID 'cache'

        except Exception as e:
            self.error.status = True
            self.error.description = "A timeout or network error occured!"
            self.error.details = "SNMP Error: branch %s, %s (%s)\n%s" % (branch_name, repr(e), str(type(e)), traceback.format_exc())
            self._add_warning(self.error.details)
            dprint("   _get_branch_by_name(%s): Exception: %s\n%s\n" % (branch_name, e.__class__.__name__, self.error.details))
            return -1

        # add to timing data, for admin use!
        self._add_mib_timing(branch_name, count, stop - start)
        self.switch.snmp_bulk_read_count += 1
        dprint("_get_branch_by_name returns %d" % count)
        return count

    def _set(self, oid, value, snmp_type, update_oidcache=True, parser=False):
        """
        Set a single OID value. Note that 'value' has to be properly typed!
        Returns 1 if success, and if requested, then we also update the
        local oid cache to track the change.
        On failure, returns -1, and self.error.X will be set
        """
        # Set a variable using an SNMP SET
        self.error.clear()
        try:
            self._snmp_session.set(oid=oid, value=value, snmp_type=snmp_type)

        except Exception as e:
            self.error.status = True
            self.error.description = "Access denied"
            self.error.details = "SNMP Error: %s (%s)\n%s" % (repr(e), str(type(e)), traceback.format_exc())
            return -1

        # update the local cache:
        if update_oidcache:
            # we cache all values as strings, just like the original returns from get_branch()
            self._parse_oid_and_cache(str(oid), str(value), snmp_type, True, parser)
            self._set_http_session_cache()

        self.switch.snmp_write_count += 1
        self.switch.save()
        return 1

    def _set_multiple(self, oid_values, update_oidcache=True, parser=False):
        """
        Set multiple OIDs at the same time, in a single snmp request
        oid_values is a list of (oid, value, type)
        Returns 1 if success, and if requested, then we also update the
        local oid cache to track the change.
        On failure, returns -1, and self.error.X will be set
        """
        self.error.clear()
        # for (oid, value, type) in oid_values:
        #    dprint("   OID = %s\n   type = %s\n   value = %s" % (oid, type, value))
        # here we go:
        self.error.clear()
        try:
            self._snmp_session.set_multiple(oid_values=oid_values)

        except Exception as e:
            self.error.status = True
            self.error.description = "Access denied"
            self.error.details = "SNMP Error: %s (%s)\n%s" % (repr(e), str(type(e)), traceback.format_exc())
            return -1

        return 1

    def _set_snmp_session(self, com_or_ctx=''):
        """
        Get a EasySnmp Session() object for this snmp connection
        com_or_ctx - the community to override the snmp profile settings if v2,
                      or the snmp v3 context to use.
        """
        snmp_profile = self.switch.snmp_profile
        if snmp_profile:
            if snmp_profile.version == SNMP_VERSION_2C:
                # use specific given community, if set:
                if com_or_ctx:
                    community = com_or_ctx
                else:
                    # use profile setting
                    community = snmp_profile.community
                self._snmp_session = easysnmp.Session(hostname=self.switch.primary_ip4,
                                                      version=snmp_profile.version,
                                                      community=community,
                                                      remote_port=snmp_profile.udp_port,
                                                      use_numeric=True,
                                                      use_sprint_value=False,
                                                      timeout=settings.SNMP_TIMEOUT,
                                                      retries=settings.SNMP_RETRIES,)
                return True

            # everything else is version 3
            if snmp_profile.version == SNMP_VERSION_3:
                # NoAuthNoPriv
                if snmp_profile.sec_level == SNMP_V3_SECURITY_NOAUTH_NOPRIV:
                    self._snmp_session = easysnmp.Session(hostname=self.switch.primary_ip4,
                                                          version=snmp_profile.version,
                                                          remote_port=snmp_profile.udp_port,
                                                          use_numeric=True,
                                                          use_sprint_value=False,
                                                          security_level=u"no_auth_or_privacy",
                                                          security_username=snmp_profile.username,
                                                          context=str(com_or_ctx),)
                    return True

                # AuthNoPriv
                elif snmp_profile.sec_level == SNMP_V3_SECURITY_AUTH_NOPRIV:
                    if snmp_profile.auth_protocol == SNMP_V3_AUTH_MD5:
                        self._snmp_session = easysnmp.Session(hostname=self.switch.primary_ip4,
                                                              version=snmp_profile.version,
                                                              remote_port=snmp_profile.udp_port,
                                                              use_numeric=True,
                                                              use_sprint_value=False,
                                                              security_level=u"auth_without_privacy",
                                                              security_username=snmp_profile.username,
                                                              auth_protocol=u"MD5",
                                                              auth_password=snmp_profile.passphrase,
                                                              context=str(com_or_ctx),)
                        return True

                    elif snmp_profile.auth_protocol == SNMP_V3_AUTH_SHA:
                        self._snmp_session = easysnmp.Session(hostname=self.switch.primary_ip4,
                                                              version=snmp_profile.version,
                                                              remote_port=snmp_profile.udp_port,
                                                              use_numeric=True,
                                                              use_sprint_value=False,
                                                              security_level=u"auth_without_privacy",
                                                              security_username=snmp_profile.username,
                                                              auth_protocol=u"SHA",
                                                              auth_password=snmp_profile.passphrase,
                                                              context=str(com_or_ctx),)
                        return True

                # AuthPriv
                elif snmp_profile.sec_level == SNMP_V3_SECURITY_AUTH_PRIV:
                    if snmp_profile.auth_protocol == SNMP_V3_AUTH_MD5:
                        if snmp_profile.priv_protocol == SNMP_V3_PRIV_DES:
                            self._snmp_session = easysnmp.Session(hostname=self.switch.primary_ip4,
                                                                  version=snmp_profile.version,
                                                                  remote_port=snmp_profile.udp_port,
                                                                  use_numeric=True,
                                                                  use_sprint_value=False,
                                                                  security_level=u"auth_with_privacy",
                                                                  security_username=snmp_profile.username,
                                                                  auth_protocol=u"MD5",
                                                                  auth_password=snmp_profile.passphrase,
                                                                  privacy_protocol=u"DES",
                                                                  privacy_password=snmp_profile.priv_passphrase,
                                                                  context=str(com_or_ctx),)
                            return True

                        if snmp_profile.priv_protocol == SNMP_V3_PRIV_AES:
                            self._snmp_session = easysnmp.Session(hostname=self.switch.primary_ip4,
                                                                  version=snmp_profile.version,
                                                                  remote_port=snmp_profile.udp_port,
                                                                  use_numeric=True,
                                                                  use_sprint_value=False,
                                                                  security_level=u"auth_with_privacy",
                                                                  security_username=snmp_profile.username,
                                                                  auth_protocol=u"MD5",
                                                                  auth_password=snmp_profile.passphrase,
                                                                  privacy_protocol=u"AES",
                                                                  privacy_password=snmp_profile.priv_passphrase,
                                                                  context=str(com_or_ctx),)
                            return True

                    if snmp_profile.auth_protocol == SNMP_V3_AUTH_SHA:
                        if snmp_profile.priv_protocol == SNMP_V3_PRIV_DES:
                            self._snmp_session = Session(hostname=self.switch.primary_ip4,
                                                         version=snmp_profile.version,
                                                         remote_port=snmp_profile.udp_port,
                                                         use_numeric=True,
                                                         use_sprint_value=False,
                                                         security_level=u"auth_with_privacy",
                                                         security_username=snmp_profile.username,
                                                         auth_protocol=u"SHA",
                                                         auth_password=snmp_profile.passphrase,
                                                         privacy_protocol=u"DES",
                                                         privacy_password=snmp_profile.priv_passphrase,
                                                         context=str(com_or_ctx),)
                            return True

                        if snmp_profile.priv_protocol == SNMP_V3_PRIV_AES:
                            self._snmp_session = easysnmp.Session(hostname=self.switch.primary_ip4,
                                                                  version=snmp_profile.version,
                                                                  remote_port=snmp_profile.udp_port,
                                                                  use_numeric=True,
                                                                  use_sprint_value=False,
                                                                  security_level=u"auth_with_privacy",
                                                                  security_username=snmp_profile.username,
                                                                  auth_protocol=u"SHA",
                                                                  auth_password=snmp_profile.passphrase,
                                                                  privacy_protocol=u"AES",
                                                                  privacy_password=snmp_profile.priv_passphrase,
                                                                  context=str(com_or_ctx),)
                            return True
                # else:
                #    dprint("  Unknown auth-priv")

        # snmp profile not set, or we cannot get session
        self._snmp_session = False
        return False


class SnmpConnector(EasySNMP):
    """
    This is the base class where it all happens! We inherit from a specific class that implements
    the basic snmp interface. This allows for quick switching between easysnmp, pysnmp, netsnmp-python, etc.

    This class implements "Generic" standards-based snmp information.
    Below are several classes that implement vendor-specific parts of this generic class.
    """
    def __init__(self, request=False, group=False, switch=False):
        """
        Initialize the object
        """
        # dprint("SnmpConnector __init__ for %s (%s)" % (switch.name, switch.primary_ip4))
        super().__init__(switch)

        self.name = "Standard SNMP"  # what type of class is running!
        self.vendor_name = ''   # typically set in sub-classes
        self.request = request  # if running on web server, Django http request object, needed for request.user() and request.session[]
        self.group = group      # Django SwitchGroup object
        # self.switch = switch    # Django Switch(), set in the base class __init__() above
        self.error = Error()
        self.error.status = False   # we don't actually have an error yet :-)
        self.oid_cache = {}         # OIDs already read are stored here
        self.system = System()      # the global system aka switch info
        self.interfaces = {}        # Interface() objects representing the ports on this switch, key is ifIndex
        self.poe_port_entries = {}  # PoePort() port power entries, used to store until we can map to interface

        self.vlan_id_by_index = {}  # list of vlan indexes and their vlan ID's. Note on many switches these two are the same!
        self.vlans = {}             # Vlan() objects on this switch, key is vlan id (not index!)
        self.allowed_vlans = {}     # list of vlans (stored as Vlan() objects) allowed on the switch, the join of switch and group Vlans
        self.vlan_id_context = 0    # non-zero if the current function is running in the context of a specific vlan (e.g. for certain Cisco mibs)
        self.qbridge_port_to_if_index = {}  # this maps Q-Bridge port id to MIB-II ifIndex
        self.dot1tp_fdb_to_vlan_index = {}  # forwarding database index to vlan index mapping. Note many switches do not use this...
        self.stack_port_to_if_index = {}    # maps (Cisco) stacking port to ifIndex values
        self.ip4_to_if_index = {}   # the IPv4 addresses as keys, with stored value ifIndex; needed to map netmask to interface
        self.eth_addr_count = 0     # number of known mac addresses
        self.neighbor_count = 0     # number of lldp neighbors
        self.warnings = []          # list of warning strings that may be shown to users
        self.mib_timing = {}        # dictionary to track how many vars and how long various MIBs take to read
        self._add_mib_timing('Total', 0, 0)     # initialize the 'total' count to 0 entries, 0 seconds!

        # features that may or may noit be implemented:
        self.vlan_change_implemented = True

        # syslog related info, if supported:
        self.syslog_msgs = {}       # list of Syslog messages, if any
        self.syslog_max_msgs = 0    # how many syslog msgs device will store

        # physical device related:
        self.stack_members = {}     # list of StackMember() objects that are part of this switch
        self.vendor_data = {}       # dict of categories with a list of VendorData() objects, to extend sytem info about this switch!

        # some timestamps
        self.basic_info_read_time = 0    # when the last 'basic' snmp read occured
        self.basic_info_duration = 0     # time in seconds for initial basic info gathering
        self.detailed_info_duration = 0  # time in seconds for each detailed info gathering

        self.cached_oid_data = False    # if True, we read switch data from the session cache

        self.hwinfo_needed = True   # True if we still need to read the Entity tables

        if not self._set_snmp_session():
            raise Exception("Cannot get SNMP session, did you configure a profile?")

    def load_caches(self):
        """
        Load various caches to improve performance.
        For now, just http session cache.
        In future, possibly add redis caching...
        """
        # now check to see if this switch snmp oid data is cached:
        self._get_http_session_cache()
        return True

    def _add_mib_timing(self, mib, count, time):
        """
        Function to track MIB responses on switch
        """
        self.mib_timing[mib] = (count, time)
        (total_count, total_time) = self.mib_timing['Total']
        total_count += count
        total_time += time
        self.mib_timing['Total'] = (total_count, total_time)

    def _set_http_session_cache(self):
        """
        Store the snmp switch data in the http session, if exists
        """
        if self.request:
            self.request.session['switch_id'] = self.switch.id
            self.request.session['oid_cache'] = self.oid_cache
            self.request.session['basic_info_read_time'] = self.basic_info_read_time
            self.request.session['basic_info_duration'] = self.basic_info_duration
            self.request.session['hwinfo_needed'] = self.hwinfo_needed
            self.request.session['mib_timing'] = self.mib_timing

            # make sure this is stored, can also add this setting:
            # SESSION_SAVE_EVERY_REQUEST=True
            self.request.session.modified = True
        # else:
            # only happens if running in CLI or tasks
            # dprint("_set_http_session_cache() called but NO http.request found!")

    def _get_http_session_cache(self):
        """
        Read the snmp switch data from the http session,
        return True is found, False otherwize.
        """
        if self.request and 'switch_id' in self.request.session.keys():
            switch_id = self.request.session['switch_id']
            if switch_id == self.switch.id:
                # Session for same switch - read it
                if 'hwinfo_needed' in self.request.session.keys():
                    self.hwinfo_needed = self.request.session['hwinfo_needed']
                if 'mib_timing' in self.request.session.keys():
                    self.mib_timing = self.request.session['mib_timing']
                if 'oid_cache' in self.request.session.keys():
                    self.oid_cache = self.request.session['oid_cache']
                    # need to update the sysUptime value first, before reading the cache:
                    self._get_sys_uptime()
                    # now parse the cache:
                    self._parse_oid_cache()
                    self.cached_oid_data = True
                    if 'basic_info_read_time' in self.request.session.keys():
                        self.basic_info_read_time = self.request.session['basic_info_read_time']
                    if 'basic_info_duration' in self.request.session.keys():
                        self.basic_info_duration = self.request.session['basic_info_duration']
                    return True
                else:
                    # this should "never" happen!
                    dprint("SESSION DATA NOT FOUND!!!")
                    return False
            else:
                # wrong switch id, i.e. we changed switches, clear session data!
                self._clear_session_oid_cache()
        # else:
        #    we are running from CLI or Celery task process!

        return False

    def set_save_needed(self, value=True):
        """
        Set a flag that this switch needs the config saved
        """
        if value:
            if self.can_save_config() and self.request:
                self.request.session['save_needed'] = True
            # else:
            #    dprint("   save config NOT supported")
        else:
            _clear_session_save_needed(self.request)
        return True

    def get_save_needed(self):
        """
        Get the flag that this switch needs the config saved
        """
        if self.request and ('save_needed' in self.request.session.keys()):
            return True
        return False

    def get_cached_oid(self, oid):
        """
        Get the OID we have already read before, from the oid_data dictionary
        oid is the string representation of the wanted oid
        """
        if oid in self.oid_cache:
            return self.oid_cache[oid]
        else:
            return False

    def _parse_oid_cache(self):
        """
        Parse all stored cached OID data and re-create Interface() data
        """
        for oid, val in self.oid_cache.items():
            self._parse_oid(str(oid), val)
        # any other (vendor) post-processing
        self._parse_oid_cache_post_processing()
        # we parse the system info separately
        self._parse_system_oids()
        # check if we can manage vlans on this device:
        self.vlan_change_implemented = self.can_change_interface_vlan()
        # and also map the PoE port data to the interfaces
        self._map_poe_port_entries_to_interface()
        # set the permissions to the interfaces:
        self._set_interfaces_permissions()
        return

    def _parse_oid_cache_post_processing(self):
        """
        Any post-parsing that needs to be performed.
        Meant for vendor-specific processing...
        """
        return

    def _parse_oid_and_cache(self, oid, value, snmp_type, cache_it, parser):
        """
        Set the read OID data in the local oid_cache store
        Also map from SNMP data type to Python data type we can handle
        EasySNMP returns everything as a Python str() object!
        """
        dprint("\n_parse_oid_and_cache()")
        dprint("HANDLING OID: %s" % str(oid))
        dprint(" value type = %s" % str(type(value)))
        dprint("  snmp_type = %s" % snmp_type)
        dprint("     length = %d" % len(value))
        # change some types, and pass
        # pysnmp types:
        if ('DisplayString' in snmp_type):
            newvalue = str(value)
        elif ('OctetString' in snmp_type):
            newvalue = str(value)
        # EasySNMP types, already str() !
        # elif ('OCTETSTR' in snmp_type):
        #    dprint("   OCTETSTRING already as str()")
        #    #see https://github.com/kamakazikamikaze/easysnmp/issues/91
        #    newvalue = value
        # elif ('INTEGER' in snmp_type):
        #    dprint("   INTEGER to int()")
        #    newvalue = int(value)
        # elif ('GAUGE' in snmp_type):
        #    dprint("   GAUGE to int()")
        #    newvalue = int(value)
        # elif ('TICKS' in snmp_type):
        #    dprint("   TICKS to int()")
        #    newvalue = int(value)
        # elif ('OBJECTID' in snmp_type):
        #    dprint("   OBJECTID already as str()")
        #    newvalue = value
        else:
            # default is already string
            newvalue = value

        # go parse the oid data
        if parser:
            # specific data parser
            retval = parser(oid, newvalue)
        else:
            # default parser
            retval = self._parse_oid(oid, newvalue)
        if retval and cache_it:
            # and if we parsed it, store original data in the local cache
            self.oid_cache[str(oid)] = value

    def _parse_oid(self, oid, val):
        """
        Parse a single OID with data returned from a switch through some "get" or "getbulk" function
        Will return True if we have parse this, and False if not.
        This will be used upstream to cache or not cache this OID.
        THIS NEEDS WORK TO IMPROVE PERFORMANCE !!!
        Returns True if we parse the OID and we should cache it!
        """
        dprint("Base _parse_oid() %s" % str(oid))
        # SYS MIB is read, we only cache it
        oid_end = oid_in_branch(system, oid)
        if oid_end:
            # SYSTEM MIB entry, caching only
            return True

        oid_end = oid_in_branch(ifIndex, oid)
        if oid_end:
            # ifIndex branch is special, the "val" is the index, not the oid ending!
            # create new interface object and store
            self.interfaces[int(val)] = Interface(int(val))
            return True

        # this is the old ifDescr, superceded by the IF-MIB name
        if_index = int(oid_in_branch(ifDescr, oid))
        if if_index:
            if if_index in self.interfaces.keys():
                # self.interfaces[if_index].ifDescr = str(val)
                # set new 'name'. Latter will later be overwritten with ifName bulkwalk
                self.interfaces[if_index].name = str(val)
            return True

        if_index = int(oid_in_branch(ifType, oid))
        if if_index:
            val = int(val)
            if if_index in self.interfaces.keys():
                self.interfaces[if_index].type = val
                if val != IF_TYPE_ETHERNET:
                    # non-Ethernet interfaces are NOT manageable, no matter who
                    self.interfaces[if_index].manageable = False
                    self.interfaces[if_index].unmanage_reason = "Access denied: not an Ethernet interface!"
            return True

        if_index = int(oid_in_branch(ifMtu, oid))
        if if_index:
            val = int(val)
            if if_index in self.interfaces.keys():
                self.interfaces[if_index].mtu = val
            return True

        # the old speed, but really we want HCSpeed from IF-MIB, see below
        if_index = int(oid_in_branch(ifSpeed, oid))
        if if_index:
            # save this in 1Mbps, as per IF-MIB hcspeed
            if if_index in self.interfaces.keys():
                self.interfaces[if_index].hc_speed = int(val) / 1000000
            return True

        # do we care about this one?
        if_index = int(oid_in_branch(ifPhysAddress, oid))
        if if_index:
            if if_index in self.interfaces.keys():
                self.interfaces[if_index].phys_addr = val
            return True

        if_index = int(oid_in_branch(ifAdminStatus, oid))
        if if_index:
            if if_index in self.interfaces.keys():
                self.interfaces[if_index].admin_status = int(val)
            return True

        if_index = int(oid_in_branch(ifOperStatus, oid))
        if if_index:
            if if_index in self.interfaces.keys():
                self.interfaces[if_index].oper_status = int(val)
            return True

        """
        if_index = int(oid_in_branch(IF_LAST_CHANGE, oid))
        if if_index:
            if if_index in self.interfaces.keys():
                self.interfaces[if_index].last_change = int(val)
            return True
        """

        if_index = int(oid_in_branch(ifName, oid))
        if if_index:
            if if_index in self.interfaces.keys():
                self.interfaces[if_index].name = str(val)
            return True

        if_index = int(oid_in_branch(ifAlias, oid))
        if if_index:
            if if_index in self.interfaces.keys():
                self.interfaces[if_index].alias = str(val)
            return True

        # ifMIB high speed counter:
        if_index = int(oid_in_branch(ifHighSpeed, oid))
        if if_index:
            if not self.switch.snmp_capabilities & CAPABILITIES_IF_MIB:
                self.switch.snmp_capabilities |= CAPABILITIES_IF_MIB
                self.switch.save()
            if if_index in self.interfaces.keys():
                self.interfaces[if_index].hc_speed = int(val)
            return True

        """
        if_index = int(oid_in_branch(ifConnectorPresent, oid))
        if if_index:
            val = int(val)
            if if_index in self.interfaces.keys():
                if val == SNMP_TRUE:
                    self.interfaces[if_index].has_connector = True
                else:
                    self.interfaces[if_index].has_connector = False
                    self.interfaces[if_index].manageable = False
            return True
        """

        # TO ADD:
        # ifStackHigherLayer = '.1.3.6.1.2.1.31.1.2.1.1'
        # ifStackLowerLayer =  '.1.3.6.1.2.1.31.1.2.1.2'
        # ifStackStatus =      '.1.3.6.1.2.1.31.1.2.1.3'

        #
        # 802.1Q / VLAN related
        #

        # these are part of "dot1qBase":
        sub_oid = oid_in_branch(dot1qNumVlans, oid)
        if sub_oid:
            self.system.vlan_count = int(val)
            return True

        sub_oid = oid_in_branch(dot1qGvrpStatus, oid)
        if sub_oid:
            if int(val) == GVRP_ENABLED:
                self.system.gvrp_enabled = True
            return True

        sub_oid = oid_in_branch(ieee8021QBridgeMvrpEnabledStatus, oid)
        if sub_oid:
            if int(val) == GVRP_ENABLED:
                self.system.gvrp_enabled = True
            return True

        # the per-switchport GVRP setting:
        port_id = int(oid_in_branch(dot1qPortGvrpStatus, oid))
        if port_id:
            if_index = self._get_if_index_from_port_id(port_id)
            if if_index in self.interfaces.keys() and int(val) == GVRP_ENABLED:
                self.interfaces[if_index].gvrp_enabled = True
            return True

        # List of all egress ports of a VLAN (tagged + untagged) as a hexstring
        # dot1qVlanCurrentEgressPorts
        sub_oid = oid_in_branch(dot1qVlanCurrentEgressPorts, oid)
        if sub_oid:
            (time_val, v) = sub_oid.split('.')
            vlan_id = int(v)
            if vlan_id not in self.vlans.keys():
                # not likely, we should know vlan by now, but just in case!
                self.vlans[vlan_id] = Vlan(vlan_id)
            self.vlans[vlan_id].current_egress_portlist.from_unicode(val)
            offset = 0
            for byte in val:
                byte = ord(byte)
                # which bits are set? A hack but it works!
                # note that the bits are actually in system order,
                # ie. bit 1 is first bit in stream, i.e. HIGH order bit!
                if(byte & 128):
                    port_id = (offset * 8) + 1
                    self._add_vlan_to_interface(port_id, vlan_id)
                if(byte & 64):
                    port_id = (offset * 8) + 2
                    self._add_vlan_to_interface(port_id, vlan_id)
                if(byte & 32):
                    port_id = (offset * 8) + 3
                    self._add_vlan_to_interface(port_id, vlan_id)
                if(byte & 16):
                    port_id = (offset * 8) + 4
                    self._add_vlan_to_interface(port_id, vlan_id)
                if(byte & 8):
                    port_id = (offset * 8) + 5
                    self._add_vlan_to_interface(port_id, vlan_id)
                if(byte & 4):
                    port_id = (offset * 8) + 6
                    self._add_vlan_to_interface(port_id, vlan_id)
                if(byte & 2):
                    port_id = (offset * 8) + 7
                    self._add_vlan_to_interface(port_id, vlan_id)
                if(byte & 1):
                    port_id = (offset * 8) + 8
                    self._add_vlan_to_interface(port_id, vlan_id)
                offset += 1
            return True

        # this is the bitmap of current untagged ports in vlans (see also above dot1qVlanStaticEgressPorts)
        sub_oid = oid_in_branch(dot1qVlanCurrentUntaggedPorts, oid)
        if sub_oid:
            (dummy, v) = sub_oid.split('.')
            vlan_id = int(v)
            if vlan_id not in self.vlans.keys():
                # not likely, but just in case:
                self.vlans[vlan_id] = Vlan(vlan_id)
            # store bitmap for later use
            self.vlans[vlan_id].untagged_ports_bitmap = val
            return True

        # see if this is static or dynamic vlan
        sub_oid = oid_in_branch(dot1qVlanStatus, oid)
        if sub_oid:
            (dummy, v) = sub_oid.split('.')
            vlan_id = int(v)
            status = int(val)
            if vlan_id in self.vlans.keys():
                self.vlans[vlan_id].status = status
            else:
                # unlikely to happen, we should know vlan by now!
                self.vlans[vlan_id] = Vlan(vlan_id)
                self.vlans[vlan_id].status = int(val)
            return True

        # The VLAN name
        vlan_id = int(oid_in_branch(dot1qVlanStaticName, oid))
        if vlan_id:
            # not yet sure how to handle this
            if vlan_id in self.vlans.keys():
                self.vlans[vlan_id].name = str(val)
            else:
                # vlan not found yet, create it
                self.vlans[vlan_id] = Vlan(vlan_id)
                self.vlans[vlan_id].name = str(val)
            return True

        # List of all static egress ports of a VLAN (tagged + untagged) as a hexstring
        # dot1qVlanStaticEgressPorts - READ-WRITE variable
        # we read and store this so we have it ready to WRITE by setting a bit value, when we update the vlan on a port!
        vlan_id = int(oid_in_branch(dot1qVlanStaticEgressPorts, oid))
        if vlan_id:
            if vlan_id not in self.vlans.keys():
                # not likely, we should know by now, but just in case.
                self.vlans[vlan_id] = Vlan(vlan_id)
            # store it!
            self.vlans[vlan_id].static_egress_portlist.from_unicode(val)
            return True

        """
        # this is the bitmap of static untagged ports in vlans (see also above dot1qVlanCurrentEgressPorts)
        vlan_id = int(oid_in_branch(dot1qVlanStaticUntaggedPorts, oid))
        if vlan_id:
            if vlan_id not in self.vlans.keys():
                # unlikely, we should know by now, but just in case
                self.vlans[vlan_id] = Vlan(vlan_id)
            # store for later use:
            # self.vlans[vlan_id].untagged_ports_bitmap = val
            return True
        """

        # List of all available vlans on this switch as by the command "show vlans"
        vlan_id = int(oid_in_branch(dot1qVlanStaticRowStatus, oid))
        if vlan_id:
            if not self.switch.snmp_capabilities & CAPABILITIES_QBRIDGE_MIB:
                self.switch.snmp_capabilities |= CAPABILITIES_QBRIDGE_MIB
                self.switch.save()
            # for now, just add to the dictionary,
            # we will fill in the initial name below at "VLAN_NAME"
            if vlan_id in self.vlans.keys():
                # currently we don't parse the status, so nothing to do here
                return True
            # else add entry, should never happen!
            self.vlans[vlan_id] = Vlan(vlan_id)
            # assume vlan_id = vlan_index = fdb_index, unless we learn otherwize
            self.vlan_id_by_index[vlan_id] = vlan_id
            self.dot1tp_fdb_to_vlan_index[vlan_id] = vlan_id
            return True

        # The VLAN ID assigned to ***untagged*** frames - dot1qPvid, indexed by dot1dBasePort
        # ie. lookup ifIndex with _get_if_index_from_port_id(port_id)
        # IMPORTANT: IF THE INTERFACE IS TAGGED, this value is 1, and typically incorrect!!!
        port_id = int(oid_in_branch(dot1qPvid, oid))
        if port_id:
            if_index = self._get_if_index_from_port_id(port_id)
            # not yet sure how to handle this
            untagged_vlan = int(val)
            if if_index in self.interfaces.keys():
                if untagged_vlan in self.vlans.keys():
                    self.interfaces[if_index].untagged_vlan = untagged_vlan
                else:
                    # vlan not defined on switch!
                    self.interfaces[if_index].disabled = True
                    self.interfaces[if_index].disabled_reason = "Untagged vlan %d is NOT defined on switch" % untagged_vlan
                    warning = "Undefined vlan %d on %s" % (untagged_vlan, self.interfaces[if_index].name)
                    self._add_warning(warning)
                    # log this as well
                    log = Log(group=self.group,
                        switch=self.switch,
                        ip_address=get_remote_ip(self.request),
                        if_index=if_index,
                        type=LOG_TYPE_ERROR,
                        action=LOG_UNDEFINED_VLAN,
                        description=f"ERROR: {warning}")
                    if self.request:
                        log.user = self.request.user
                    log.save()
                    # not sure what to do here
            return True

        # The .0 is the timefilter that we set to 0 to (hopefully) deactivate the filter
        # The set of ports that are transmitting traffic for this VLAN as either tagged or untagged frames.
        # CURRENT_VLAN_EGRESS_PORTS = QBRIDGENODES['dot1qVlanCurrentEgressPorts']['oid'] + '.0'
        # NOTE: this is a READ-ONLY variable!

        # Map the Q-BRIDGE port id to the MIB-II if_indexes.
        # PortID=0 indicates known ethernet, but unknown port, i.e. ignore
        port_id = int(oid_in_branch(dot1dBasePortIfIndex, oid))
        if port_id:
            # map port ID to interface ID
            if_index = int(val)
            self.qbridge_port_to_if_index[port_id] = if_index
            # and map Interface() object back to port ID as well:
            if if_index in self.interfaces.keys():
                self.interfaces[if_index].port_id = port_id
            return True

        """
        Handle the device IP addresses, e.g. interface ip, vlan ip, etc.
        """
        ip = oid_in_branch(ipAdEntIfIndex, oid)
        if ip:
            if_index = int(val)
            if if_index in self.interfaces.keys():
                self.ip4_to_if_index[ip] = if_index  # for lookup of netmask below
                self.interfaces[if_index].addresses_ip4[ip] = IP4Address(ip)
            return True

        ip = oid_in_branch(ipAdEntNetMask, oid)
        if ip:
            # depending on SNMP class, we either have a nice string (EasySNMP)
            # or a 4-byte binary address (pysnmp)
            if "pysnmp.proto.rfc1902.IpAddress" in str(type(val)):
                # ipaddr = IpAddress('')
                netmask = val.prettyOut(val)
            else:
                netmask = val
            # dprint("IP address %s netmask %s" % (ip, netmask))
            # we should have found the IP address already!
            if ip in self.ip4_to_if_index.keys():
                if_index = self.ip4_to_if_index[ip]
                if if_index in self.interfaces.keys():
                    # have we seen this IP on this interface (we should!)?
                    if ip in self.interfaces[if_index].addresses_ip4.keys():
                        ip_addr = self.interfaces[if_index].addresses_ip4[ip]
                        ip_addr.set_netmask(netmask)
                        self.interfaces[if_index].addresses_ip4[ip] = ip_addr  # save change!
            return True

        """
        ENTITY MIB, info about the device, eg stack or single unit, # of units, serials
        and other interesting pieces
        """

        dev_id = int(oid_in_branch(entPhysicalClass, oid))
        if dev_id:
            dev_type = int(val)
            if(dev_type == ENTITY_CLASS_STACK or dev_type == ENTITY_CLASS_CHASSIS or dev_type == ENTITY_CLASS_MODULE):
                # save this info!
                member = StackMember(dev_id, dev_type)
                self.stack_members[dev_id] = member
            return True

        dev_id = int(oid_in_branch(entPhysicalSerialNum, oid))
        if dev_id:
            serial = str(val)
            if dev_id in self.stack_members.keys():
                # save this info!
                self.stack_members[dev_id].serial = serial
            return True

        dev_id = int(oid_in_branch(entPhysicalSoftwareRev, oid))
        if dev_id:
            version = str(val)
            if dev_id in self.stack_members.keys():
                # save this info!
                self.stack_members[dev_id].version = version
            return True

        dev_id = int(oid_in_branch(entPhysicalModelName, oid))
        if dev_id:
            model = str(val)
            if dev_id in self.stack_members.keys():
                # save this info!
                self.stack_members[dev_id].model = model
            return True

        """
        SYSLOG-MSG-MIB - mostly mean to define notification, but we can read the log size
        """
        sub_oid = oid_in_branch(syslogMsgTableMaxSize, oid)
        if sub_oid:
            # this is the max number of syslog messages stored.
            self.syslog_max_msgs = int(val)
            return True
        """
        Note: the rest of the SYSLOG_MSG_MIB is meant to define OID's for sending
        SNMP traps with syslog messages, NOT to poll messages from snmp reads !!!
        """

        """
        PoE related entries:
        the pethMainPseEntry table entries with device-level PoE info
        the OID is <base><device-id>.1 = <value>,
        where <device-id> is stack member number, vendor and device specific!
        """

        pse_id = int(oid_in_branch(pethMainPsePower, oid))
        if pse_id:
            self.system.poe_capable = True
            self.system.poe_max_power += int(val)
            # store data about individual PSE unit:
            if pse_id not in self.system.poe_pse_devices.keys():
                self.system.poe_pse_devices[pse_id] = PoePSE(pse_id)
            # update max power
            self.system.poe_pse_devices[pse_id].max_power = int(val)
            return True

        pse_id = int(oid_in_branch(pethMainPseOperStatus, oid))
        if pse_id:
            if not self.switch.snmp_capabilities & CAPABILITIES_POE_MIB:
                self.switch.snmp_capabilities |= CAPABILITIES_POE_MIB
                self.switch.save()
            # not yet sure how to handle this, for now just read
            self.system.poe_capable = True
            self.system.poe_enabled = int(val)
            # store data about individual PSE unit:
            if pse_id not in self.system.poe_pse_devices.keys():
                self.system.poe_pse_devices[pse_id] = PoePSE(pse_id)
            # update status
            self.system.poe_pse_devices[pse_id].status = int(val)
            return True

        pse_id = int(oid_in_branch(pethMainPseConsumptionPower, oid))
        if pse_id:
            self.system.poe_capable = True
            self.system.poe_power_consumed += int(val)
            # store data about individual PSE unit:
            if pse_id not in self.system.poe_pse_devices.keys():
                self.system.poe_pse_devices[pse_id] = PoePSE(pse_id)
            # update max power
            self.system.poe_pse_devices[pse_id].power_consumed = int(val)
            return True

        pse_id = int(oid_in_branch(pethMainPseUsageThreshold, oid))
        if pse_id:
            self.system.poe_capable = True
            # store data about individual PSE unit:
            if pse_id not in self.system.poe_pse_devices.keys():
                self.system.poe_pse_devices[pse_id] = PoePSE(pse_id)
            # update max power
            self.system.poe_pse_devices[pse_id].threshold = int(val)
            return True

        """
        the pethPsePortEntry tables with port-level PoE info
        OID is followed by PortEntry index (pe_index). This is typically
        or module_num.port_num for modules switch chassis, or
        device_id.port_num for stack members.
        This gets mapped to an interface later on in
        self._map_poe_port_entries_to_interface(), which is typically device specific
        (i.e. implemented in the device-specific classes iin
        vendor/cisco/snmp.py, vendor/comware/snmp.py, etc.)
        """

        pe_index = oid_in_branch(pethPsePortAdminEnable, oid)
        if pe_index:
            self.poe_port_entries[pe_index] = PoePort(pe_index, int(val))
            return True

        pe_index = oid_in_branch(pethPsePortDetectionStatus, oid)
        if pe_index:
            if pe_index in self.poe_port_entries.keys():
                self.poe_port_entries[pe_index].detect_status = int(val)
            return True

        """
        These are currently not used:
        pe_index = oid_in_branch(pethPsePortPowerPriority, oid)
        if pe_index:
            if pe_index in self.poe_port_entries.keys():
                self.poe_port_entries[pe_index].priority = int(val)
            return True

        pe_index = oid_in_branch(pethPsePortType, oid)
        if pe_index:
            if pe_index in self.poe_port_entries.keys():
                self.poe_port_entries[pe_index].description = str(val)
            return True
        """

        #
        # LACP MIB parsing
        #
        """
        Parse a single OID with data returned from the LACP MIB
        Will return True if we have parsed this, and False if not.
        """

        # this gets the aggregator interface admin key or "index"
        aggr_if_index = int(oid_in_branch(dot3adAggActorAdminKey, oid))
        if aggr_if_index:
            # this interface is a aggregator!
            if aggr_if_index in self.interfaces.keys():
                self.interfaces[aggr_if_index].lacp_type = LACP_IF_TYPE_AGGREGATOR
                self.interfaces[aggr_if_index].lacp_admin_key = int(val)
                # some vendors (certain Cisco switches) set the IF-MIB::ifType to Virtual (53) instead of LAGG (161)
                # hardcode to LAGG:
                self.interfaces[aggr_if_index].type = IF_TYPE_LAGG
            return True

        # this get the member interfaces admin key ("index"), which maps back to the aggregator interface above!
        member_if_index = int(oid_in_branch(dot3adAggPortActorAdminKey, oid))
        if member_if_index:
            # this interface is an lacp member!
            if member_if_index in self.interfaces.keys():
                # can we find an aggregate with this key value ?
                lacp_key = int(val)
                for lacp_index, iface in self.interfaces.items():
                    if iface.lacp_type == LACP_IF_TYPE_AGGREGATOR and iface.lacp_admin_key == lacp_key:
                        # the current interface is a member of this aggregate iface !
                        self.interfaces[member_if_index].lacp_type = LACP_IF_TYPE_MEMBER
                        self.interfaces[member_if_index].lacp_master_index = lacp_index
                        self.interfaces[member_if_index].lacp_master_name = iface.name
                        # add our name to the list of the aggregate interface
                        self.interfaces[lacp_index].lacp_members[member_if_index] = self.interfaces[member_if_index].name
            return True

        """
        # LACP port membership, may only valid once an interface is "up" and has joined the aggregate
        member_if_index = int(oid_in_branch(dot3adAggPortAttachedAggID, oid))
        if member_if_index:
            lacp_if_index = int(val)
            if lacp_if_index > 0:
                dprint("Member ifIndex %s is part of LACP ifIndex %d" % (member_if_index, lacp_if_index))
                if member_if_index in self.interfaces.keys() and lacp_if_index in self.interfaces.keys():
                    # from this one read, we can get the aggregate ifIndex for the virtual interface
                    # (and name, for display convenience)
                    self.interfaces[member_if_index].lacp_master_index = lacp_if_index
                    self.interfaces[member_if_index].lacp_master_name = self.interfaces[lacp_if_index].name
                    # and also the member interface (i.e. the physical interface!)
                    self.interfaces[lacp_if_index].lacp_members[member_if_index] = self.interfaces[member_if_index].name
            return True
        """

        # we did not parse this. This can happen with Bulk Walks...
        return False

    #
    # Original "dot1d Bridge MIB" Known Ethernet MIB parsing
    #
    def _parse_mibs_dot1d_bridge_eth(self, oid, val):
        """
        Parse a single OID with data returned from the Q-Bridge Ethernet MIBs
        Will return True if we have parsed this, and False if not.
        """
        # Q-Bridge Ethernet addresses known
        eth_decimals = oid_in_branch(dot1dTpFdbPort, oid)
        if eth_decimals:
            # decimals returned are 6 numbers representing the MAC address!
            eth_string = decimal_to_hex_string_ethernet(eth_decimals)
            port_id = int(val)
            # PortID=0 indicates known ethernet, but unknown port, i.e. ignore
            if port_id:
                if_index = self.qbridge_port_to_if_index[int(val)]
                if if_index in self.interfaces.keys():
                    e = EthernetAddress(eth_decimals)
                    if self.vlan_id_context > 0:
                        e.vlan_id = self.vlan_id_context
                    self.interfaces[if_index].eth[eth_string] = e
                    self.eth_addr_count += 1
                # else:
                #    dprint("  if_index = %d: NOT FOUND!")
            return True
        return False

    #
    # Newer Q-Bridge Known Ethernet MIB parsing
    #
    def _parse_mibs_q_bridge_eth(self, oid, val):
        """
        Parse a single OID with data returned from the Q-Bridge Ethernet MIBs
        Will return True if we have parsed this, and False if not.
        """
        # Q-Bridge Ethernet addresses known
        fdb_eth_decimals = oid_in_branch(dot1qTpFdbPort, oid)
        if fdb_eth_decimals:
            # decimals returned are fdb index and then 6 numbers representing the MAC address!
            # e.g.    458752.120.72.89.101.150.155
            # fdb_index maps back to the vlan id!
            (fdb_index, eth_decimals) = fdb_eth_decimals.split('.', 1)
            eth_string = decimal_to_hex_string_ethernet(eth_decimals)
            port_id = int(val)
            # PortID=0 indicates known ethernet, but unknown port, i.e. ignore
            if port_id:
                if_index = self.qbridge_port_to_if_index[int(val)]
                if if_index in self.interfaces.keys():
                    e = EthernetAddress(eth_decimals)
                    if self.vlan_id_context > 0:
                        # we are explicitly in a vlan context! (vendor specific implementation)
                        e.vlan_id = self.vlan_id_context
                    else:
                        # see if we can use Forward DB mapping:
                        # double lookup: from fdb index find vlan index, then from vlan index find vlan id!
                        """
                        vlan_index = self.dot1tp_fdb_to_vlan_index.get(int(fdb_index), 0)
                        vlan_id = self.vlan_id_by_index.get(vlan_index, 0)
                        dprint("Eth found in fdb_index %d => vlan_index %d => vlan_id %d" % (int(fdb_index), vlan_index, vlan_id))
                        """
                        e.vlan_id = self.vlan_id_by_index.get(self.dot1tp_fdb_to_vlan_index.get(int(fdb_index), 0), 0)
                    self.interfaces[if_index].eth[eth_string] = e
                    self.eth_addr_count += 1
                # else:
                #    dprint("  if_index = %d: NOT FOUND!")
            return True
        return False

    def _parse_mibs_net_to_media(self, oid, val):
        """
        Parse a single OID with data returned from the (various) Net-To-Media (ie ARP) mibs
        Will return True if we have parsed this, and False if not.
        """
        # First the old style ipNetToMedia tables
        # we take some shortcuts here by not using the mappings through ipNetToMediaIfIndex and ipNetToMediaNetAddress
        if_ip_string = oid_in_branch(ipNetToMediaPhysAddress, oid)
        if if_ip_string:
            if not self.switch.snmp_capabilities & CAPABILITIES_NET2MEDIA_MIB:
                self.switch.snmp_capabilities |= CAPABILITIES_NET2MEDIA_MIB
                self.switch.save()
            parts = if_ip_string.split('.', 1)  # 1 means one split, two elements!
            if_index = int(parts[0])
            ip = str(parts[1])
            if if_index in self.interfaces.keys():
                mac_addr = bytes_to_hex_string_ethernet(val)
                self.interfaces[if_index].arp4[ip] = mac_addr
                # see if we can add this to a known ethernet address
                # time consuming, but useful
                for index, iface in self.interfaces.items():
                    if mac_addr in iface.eth.keys():
                        # Found existing MAC addr, adding IP4
                        iface.eth[mac_addr].address_ip4 = ip

            return True

        """
        Next (eventually) the newer ipNetToPhysical tables
        Note: we have not found any device yet that returns this!
        """
        return False

    #
    # LLDP MIB parsing
    #
    def _parse_mibs_lldp(self, oid, val):
        """
        Parse a single OID with data returned from the LLDP MIBs
        Will return True if we have parsed this, and False if not.
        This will be used upstream to cache or not cache this OID.
        """
        dprint("_parse_mibs_lldp() %s, len = %d, type = %s" % (str(oid), len(val), str(type(val))))

        # we are not looking at this at this time, already have it from IF MIB
        # lldp = oid_in_branch(lldpLocPortTable, oid)
        # if lldp:
        #    dprint("LLDP LOCAL PORT ENTRY %s = %s" % (lldp, str(val)))
        #    return True

        # this does not appear to be implemented in most gear:
        # lldp = oid_in_branch(lldpRemLocalPortNum, oid)
        # if lldp:
        #    dprint("LLDP REMOTE_LOCAL PORT ENTRY %s = %s" % (lldp, str(val)))
        #    return True

        # the following are indexed by  <remote-device-random-id>.<port-id>.1
        # if Q-BRIDGE is implemented, <port-id> is that port_id, mapped in self.qbridge_port_to_if_index[port_id]
        # if Q-BRIDGE is NOT implemented, <port-id> = <ifIndex>, ie without the mapping
        lldp_index = oid_in_branch(lldpRemPortId, oid)
        if lldp_index:
            if not self.switch.snmp_capabilities & CAPABILITIES_LLDP_MIB:
                self.switch.snmp_capabilities |= CAPABILITIES_LLDP_MIB
                self.switch.save()
            (extra_one, port_id, extra_two) = lldp_index.split('.')
            port_id = int(port_id)
            # store the new lldp object, based on the string index.
            # need to find the ifIndex first.
            # did we find Q-Bridge mappings?
            if_index = self._get_if_index_from_port_id(port_id)
            if if_index in self.interfaces.keys():
                # add new LLDP neighbor
                self.interfaces[if_index].lldp[lldp_index] = NeighborDevice(lldp_index, if_index)
                self.neighbor_count += 1
            return True

        lldp_index = oid_in_branch(lldpRemPortDesc, oid)
        if lldp_index:
            (extra_one, port_id, extra_two) = lldp_index.split('.')
            port_id = int(port_id)
            # at this point, we should have already found the lldp neighbor and created an object
            # did we find Q-Bridge mappings?
            if_index = self._get_if_index_from_port_id(port_id)
            if if_index in self.interfaces.keys():
                if lldp_index in self.interfaces[if_index].lldp.keys():
                    # now update with system name
                    self.interfaces[if_index].lldp[lldp_index].port_descr = str(val)
            return True

        lldp_index = oid_in_branch(lldpRemSysName, oid)
        if lldp_index:
            (extra_one, port_id, extra_two) = lldp_index.split('.')
            port_id = int(port_id)
            # at this point, we should have already found the lldp neighbor and created an object
            # did we find Q-Bridge mappings?
            if_index = self._get_if_index_from_port_id(port_id)
            if if_index in self.interfaces.keys():
                if lldp_index in self.interfaces[if_index].lldp.keys():
                    # now update with system name
                    self.interfaces[if_index].lldp[lldp_index].sys_name = str(val)
            return True

        lldp_index = oid_in_branch(lldpRemSysDesc, oid)
        if lldp_index:
            (extra_one, port_id, extra_two) = lldp_index.split('.')
            port_id = int(port_id)
            # at this point, we should have already found the lldp neighbor and created an object
            # did we find Q-Bridge mappings?
            if_index = self._get_if_index_from_port_id(port_id)
            if if_index in self.interfaces.keys():
                if lldp_index in self.interfaces[if_index].lldp.keys():
                    # now update with system name
                    self.interfaces[if_index].lldp[lldp_index].sys_descr = str(val)
            return True

        # parse enabled capabilities
        lldp_index = oid_in_branch(lldpRemSysCapEnabled, oid)
        if lldp_index:
            (extra_one, port_id, extra_two) = lldp_index.split('.')
            port_id = int(port_id)
            # at this point, we should have already found the lldp neighbor and created an object
            # did we find Q-Bridge mappings?
            if_index = self._get_if_index_from_port_id(port_id)
            if if_index in self.interfaces.keys():
                if lldp_index in self.interfaces[if_index].lldp.keys():
                    # now update with system name
                    self.interfaces[if_index].lldp[lldp_index].capabilities = bytes(val, 'utf-8')
            return True

        lldp_index = oid_in_branch(lldpRemChassisIdSubtype, oid)
        if lldp_index:
            (extra_one, port_id, extra_two) = lldp_index.split('.')
            port_id = int(port_id)
            val = int(val)
            # at this point, we should have already found the lldp neighbor and created an object
            # did we find Q-Bridge mappings?
            if_index = self._get_if_index_from_port_id(port_id)
            if if_index in self.interfaces.keys():
                if lldp_index in self.interfaces[if_index].lldp.keys():
                    # now update with system name
                    if self.interfaces[if_index].lldp[lldp_index].chassis_type > 0:
                        self._add_warning("Chassis Type for %d already %d, now %d!" %
                                          (llp_index, self.interfaces[if_index].lldp[lldp_index].chassis_type, val))
                    self.interfaces[if_index].lldp[lldp_index].chassis_type = val
            return True

        lldp_index = oid_in_branch(lldpRemChassisId, oid)
        if lldp_index:
            (extra_one, port_id, extra_two) = lldp_index.split('.')
            port_id = int(port_id)
            # at this point, we should have already found the lldp neighbor and created an object
            # did we find Q-Bridge mappings?
            if_index = self._get_if_index_from_port_id(port_id)
            if if_index in self.interfaces.keys():
                if lldp_index in self.interfaces[if_index].lldp.keys():
                    # now update with system name
                    self.interfaces[if_index].lldp[lldp_index].chassis_string = val
            return True

        return False

    def _add_vlan_to_interface(self, port_id, vlan_id):
        """
        Function to add a given vlan to the interface identified by the dot1D bridge port id
        """
        dprint("_add_vlan_to_interface() port %d vlan %d" % (port_id, vlan_id))
        # get the interface index first:
        if_index = self._get_if_index_from_port_id(port_id)
        if if_index in self.interfaces.keys():
            if self.interfaces[if_index].untagged_vlan == vlan_id:
                dprint("   PVID already set!")
                # interface already has this untagged vlan, not adding
                return True
            else:
                dprint("   Add as tagged!")
                self.interfaces[if_index].vlans.append(vlan_id)
                self.interfaces[if_index].is_tagged = True
            return True
        return False

    def _get_if_index_from_port_id(self, port_id):
        """
        Return the ifIndex from the Q-Bridge port_id. This assumes we have walked
        the Q-Bridge mib that maps bridge port id to interfaceId.
        """
        # if len(self.qbridge_port_to_if_index) > 0 and port_id in self.qbridge_port_to_if_index.keys():
        if port_id in self.qbridge_port_to_if_index.keys():
            return self.qbridge_port_to_if_index[int(port_id)]
        else:
            # we did not find the Q-BRIDGE mib. port_id = ifIndex !
            return port_id

    def _get_port_id_from_if_index(self, if_index):
        """
        Return the bridge PortId for the given interface index. This assumes we have walked
        the Q-Bridge mib that maps bridge port id to interfaceId.
        """
        if if_index in self.interfaces.keys() and len(self.qbridge_port_to_if_index) > 0:
            for (port_id, intf) in self.qbridge_port_to_if_index.items():
                if if_index == intf:
                    return port_id
        else:
            # we did not find the Q-BRIDGE mib. port_id = ifIndex !
            return if_index

    def _parse_system_oids(self):
        """
        parse the basic 6 system mib entries from the cache.
        ie.sys-descr, object-id, uptime, contact, name & location
        """
        dprint("_parse_system_oids()")
        self.system.description = self.get_cached_oid(sysDescr)
        self.system.object_id = self.get_cached_oid(sysObjectID)
        self.system.enterprise_info = get_switch_enterprise_info(self.system.object_id)
        # sysUpTime is ticks in 1/100th of second since boot
        self.system.sys_uptime = int(self.get_cached_oid(sysUpTime))
        self.system.time = time.time()
        # uptime is in seconds:
        self.system.uptime = datetime.timedelta(seconds=int(self.system.sys_uptime / 100))
        self.system.contact = self.get_cached_oid(sysContact)
        self.system.name = self.get_cached_oid(sysName)
        self.system.location = self.get_cached_oid(sysLocation)

    def _get_sys_uptime(self):
        """
        Get the current sysUpTime timetick for the device.
        """
        self._get(sysUpTime)
        # sysUpTime is ticks in 1/100th of second since boot
        self.system.sys_uptime = int(self.get_cached_oid(sysUpTime))
        self.system.time = time.time()

    def _get_system_data(self):
        """
        get just the System-MIB parts, ie OID, Location, etc.
        Return a negative value if error occured, or 1 if success
        """
        retval = self._get_branch_by_name('system')
        if retval < 0:
            self._add_warning("Error getting 'System-Mib' (system)")
            return retval   # error of some kind

        self._parse_system_oids()

        # see if the ObjectID changed
        if not self.system.object_id:
            # this 'should' never happen
            return 1
        if self.switch.snmp_oid != self.system.object_id:
            self.switch.snmp_oid = self.system.object_id
            self.switch.save()
            log = Log(action=LOG_NEW_OID_FOUND,
                description="New System ObjectID found",
                switch=self.switch,
                group=self.group,
                ip_address=get_remote_ip(self.request),
                type=LOG_TYPE_WARNING)
            if self.request:
                log.user = self.request.user
            log.save()

        # and see if the hostname changed
        if not self.system.name:
            return 1
        if self.switch.snmp_hostname != self.system.name:
            self.switch.snmp_hostname = self.system.name
            self.switch.save()
            log = Log(action=LOG_NEW_HOSTNAME_FOUND,
                description="New System Hostname found",
                switch=self.switch,
                group=self.group,
                ip_address=get_remote_ip(self.request),
                type=LOG_TYPE_WARNING)
            if self.request:
                log.user = self.request.user
            log.save()

        return 1

    def _get_vendor_data(self):
        """
        Placeholder for vendor-specific data, to be implented in sub-classes.
        The sub-class is responsible for parsing and caching snmp data,
        as is done in _parse_oid()
        """
        return

    def _get_entity_data(self):
        """
        read the various Entity OIDs for the basic data we want
        This reads information about the modules, software revisions, etc.
        Return a negative value if error occured, or 1 if success
        """
        # get physical device info
        retval = self._get_branch_by_name('entPhysicalClass')
        if retval < 0:
            self._add_warning("Error getting 'Entity-Class' ('entPhysicalClass')")
            return retval
        retval = self._get_branch_by_name('entPhysicalSerialNum')
        if retval < 0:
            self._add_warning("Error getting 'Entity-Serial' (entPhysicalSerialNum)")
            return retval
        retval = self._get_branch_by_name('entPhysicalSoftwareRev')
        if retval < 0:
            self._add_warning("Error getting 'Entity-Software' (entPhysicalSoftwareRev)")
            return retval
        retval = self._get_branch_by_name('entPhysicalModelName')
        if retval < 0:
            self._add_warning("Error getting 'Entity-Model' (entPhysicalModelName)")
            return retval

        return 1

    def _get_interface_data(self):
        """
        Get Interface MIB data from the switch. We are not reading the whole MIB-II branch at ifTable,
        but to speed it up, we run individual branches that we need ...
        Returns 1 on succes, -1 on failure
        """
        # it all starts with the interface indexes
        retval = self._get_branch_by_name('ifIndex')
        if retval < 0:
            self._add_warning("Error getting 'Interfaces' (%s)" % ifIndex)
            return retval
        # and the types
        retval = self._get_branch_by_name('ifType')
        if retval < 0:
            self._add_warning("Error getting 'Interface-Type' (%s)" % ifType)
            return retval

        # the status of the interface, admin up/down, link up/down
        retval = self._get_branch_by_name('ifAdminStatus')
        if retval < 0:
            self._add_warning("Error getting 'Interface-AdminStatus' (%s)" % ifAdminStatus)
            return retval
        retval = self._get_branch_by_name('ifOperStatus')
        if retval < 0:
            self._add_warning("Error getting 'Interface-OperStatus' (%s)" % ifOperStatus)
            return retval

        # find the interface name, start with the newer IF-MIB
        retval = self._get_branch_by_name('ifName')
        if retval < 0:
            self._add_warning("Error getting 'Interface-Names' (%s)" % ifName)
            return retval
        if retval == 0:  # newer IF-MIB entries no found, try the old
            retval = self._get_branch_by_name('ifDescr')
            if retval < 0:
                self._add_warning("Error getting 'Interface-Descriptions' (%s)" % ifDescr)
                return retval

        # this is the interface description
        retval = self._get_branch_by_name('ifAlias')
        if retval < 0:
            self._add_warning("Error getting 'Interface-Alias' (%s)" % ifAlias)
            return retval

        # speed is in new IF-MIB
        retval = self._get_branch_by_name('ifHighSpeed')
        if retval < 0:
            self._add_warning("Error getting 'Interface-HiSpeed' (%s)" % ifHighSpeed)
            return retval
        if retval == 0:    # new IF-MIB hcspeed entry not found, try old speed
            retval = self._get_branch_by_name('ifSpeed')
            if retval < 0:
                self._add_warning("Error getting 'Interface-Speed' (%s)" % ifSpeed)
                return retval

        # check the connector, if not, cannot be managed, another safety feature
        # retval = self._get_branch_by_name('ifConnectorPresent')
        # if retval < 0:
        #    self._add_warning("Error getting 'Interface-Connector' (%s)" % ifConnectorPresent)
        #    return retval

        # if not self._get_branch_by_name('ifStackEntry'):   # LACP / Aggregate / Port-Channel interfaces
        #    return False
        return 1

    def _get_vlans(self):
        """
        Read the list of defined vlans on the switch
        Returns error value (if < 0), or count of vlans found (0 or greater)
        """
        # first map dot1D-Bridge ports to ifIndexes, needed for Q-Bridge port-id to ifIndex
        retval = self._get_branch_by_name('dot1dBasePortIfIndex')
        if retval < 0:
            self._add_warning("Error getting 'Q-Bridge-PortId-Map' (dot1dBasePortIfIndex)")
            return retval
        # read existing vlan id's
        retval = self._get_branch_by_name('dot1qVlanStaticRowStatus')
        if retval < 0:
            self._add_warning("Error getting 'Q-Bridge-Vlan-Rows' (dot1qVlanStaticRowStatus)")
            return retval
        vlan_count = retval
        # if there are vlans, read the name and type
        if retval > 0:
            retval = self._get_branch_by_name('dot1qVlanStaticName')
            if retval < 0:
                # error occured (unlikely to happen)
                self._add_warning("Error getting 'Q-Bridge-Vlan-Names' (dot1qVlanStaticName)")
                # we have found VLANs, so we are going to ignore this!
            # read the vlan status, ie static, dynamic!
            retval = self._get_branch_by_name('dot1qVlanStatus')
            if retval < 0:
                self._add_warning("Error getting 'Q-Bridge-Vlan-Status' (dot1qVlanStatus)")
                # we have found VLANs, so we are going to ignore this!
        else:
            # retval = 0, no vlans found!
            self._add_warning("No VLANs found at 'Q-Bridge-Vlan-Rows' (dot1qVlanStaticRowStatus)")

        # check if we can change vlans
        self.vlan_change_implemented = self.can_change_interface_vlan()

        return vlan_count

    def _get_port_vlan_membership(self):
        """
        Read the Q-Bridge MIB vlan and switchport data. Again, to optimize, we read what we need.
        Returns 1 on success, -1 on failure
        """

        # read the PVID of UNTAGGED interfaces.
        retval = self._get_branch_by_name('dot1qPvid')
        if retval < 0:
            self._add_warning("Error getting 'Q-Bridge-Interface-PVID' (dot1qPvid)")
            return retval

        # THIS IS LIKELY NOT PROPERLY HANDLED !!!
        # read the current vlan untagged port mappings
        # retval = self._get_branch_by_name(dot1qVlanCurrentUntaggedPorts)
        # if retval < 0:
        #    self._add_warning("Error getting 'Q-Bridge-Vlan-Untagged-Interfaces' (%s)" % dot1qVlanCurrentUntaggedPorts)
        #    return retval

        # read the current vlan egress port mappings, tagged and untagged
        retval = self._get_branch_by_name('dot1qVlanCurrentEgressPorts')
        if retval < 0:
            self._add_warning("Error getting 'Q-Bridge-Vlan-Egress-Interfaces' (dot1qVlanCurrentEgressPorts)")
            return retval

        # read the 'static' vlan egress port mappings, tagged and untagged
        # this will be used when changing vlans on ports, could also ignore for now!
        # retval = self._get_branch_by_name(dot1qVlanStaticEgressPorts)
        # if retval < 0:
        #    self._add_warning("Error getting 'Q-Bridge-Vlan-Static-Egress-Interfaces' (%s)" % dot1qVlanStaticEgressPorts)
        #    return retval

        return 1

    def _get_vlan_data(self):
        """
        get all neccesary vlan info (names, id, ports on vlans, etc.) from the switch.
        returns -1 on error, or number to indicate vlans found.
        """
        # get the base 802.1q settings:
        retval = self._get_branch_by_name('dot1qBase')
        if self.system.vlan_count > 0:
            # first get vlan id and names
            self._get_vlans()
            # next, read the interface vlan data
            retval = self._get_port_vlan_membership()
            if retval < 0:
                return retval
            # if GVRP enabled, then read this data
            if self.system.gvrp_enabled:
                retval = self._get_branch_by_name('dot1qPortGvrpStatus')

        # check MVRP status:
        retval = self._get_branch_by_name('ieee8021QBridgeMvrpEnabledStatus')

        return self.system.vlan_count

    def _get_my_ip4_addresses(self):
        """
        Read the ipAddrEntry tables for the switch IP4 addresses
        Returns 1 on success, -1 on failure
        """
        retval = self._get_branch_by_name('ipAddrTable')  # small mib, read all entries below it
        if retval < 0:
            self._add_warning("Error getting 'IP-Address-Entries' (ipAddrTable)")
            return retval

        return 1

    def _map_poe_port_entries_to_interface(self):
        """
        This function maps the "pethPsePortEntry" indices that are stored in self.poe_port_entries{}
        to interface ifIndex values, so we can store them with the interface and display as needed.
        In general, you can generate the interface ending "x/y" from the index by substituting "." for "/"
        E.g. "5.12" from the index becomes "5/12", and you then search for an interface with matching ending
        e.g. GigabitEthernet5/12
        """
        for (pe_index, port_entry) in self.poe_port_entries.items():
            end = port_entry.index.replace('.', '/')
            count = len(end)
            for (if_index, iface) in self.interfaces.items():
                if iface.name[-count:] == end:
                    iface.poe_entry = port_entry
                    break

    def _get_poe_data(self):
        """
        Read Power-over-Etnernet data, still needs works
        Returns 1 on success, -1 on failure
        """
        # first the PSE entries, ie the power supplies
        retval = self._get_branch_by_name('pethMainPseEntry')
        if retval < 0:
            self._add_warning("Error getting 'PoE-PSE-Data' (pethMainPseEntry)")
            return retval
        if retval > 0:
            # found power supplies, look at port power data
            # this is under pethPsePortEntry, but we only need a few entries:
            retval = self._get_branch_by_name('pethPsePortAdminEnable')
            if retval < 0:
                self._add_warning("Error getting 'PoE-Port-Admin-Status' (pethPsePortAdminEnable)")
            if retval > 0:  # ports with PoE capabilities found!
                retval = self._get_branch_by_name('pethPsePortDetectionStatus')
                if retval < 0:
                    self._add_warning("Error getting 'PoE-Port-Detect-Status' (pethPsePortDetectionStatus)")
                """ Currently not used:
                retval = self._get_branch_by_name('pethPsePortPowerPriority')
                if retval < 0:
                    self._add_warning("Error getting 'PoE-Port-Detect-Status' (pethPsePortPowerPriority)")
                retval = self._get_branch_by_name('pethPsePortType')
                if retval < 0:
                    self._add_warning("Error getting 'PoE-Port-Description' (pethPsePortType)")
                """
        return 1

    def _get_known_ethernet_addresses(self):
        """
        Read the Bridge-MIB for known ethernet address on the switch.
        Returns 1 on success, -1 on failure
        """

        # next, read the known ethernet addresses, and add to the Interfaces.
        # Do NOT cache and use a custom parser for speed

        # First, the newer dot1q bridge mib
        retval = self._get_branch_by_name('dot1qTpFdbPort', False, self._parse_mibs_q_bridge_eth)
        if retval < 0:
            self._add_warning("Error getting 'Q-Bridge-EthernetAddresses' (dot1qTpFdbPort)")
            return -1
        # If nothing found,check the older dot1d bridge mib
        if retval == 0:
            retval = self._get_branch_by_name('dot1dTpFdbPort', False, self._parse_mibs_dot1d_bridge_eth)
            if retval < 0:
                self._add_warning("Error getting 'Bridge-EthernetAddresses' (dot1dTpFdbPort)")
                return -1
        return 1

    def _get_arp_data(self):
        """
        Read the arp tables from both old style ipNetToMedia,
        and eventually, new style ipNetToPhysical
        Returns 1 on success, -1 on failure
        """
        retval = self._get_branch_by_name('ipNetToMediaPhysAddress', False, self._parse_mibs_net_to_media)
        if retval < 0:
            self._add_warning("Error getting 'ARP-Table' (ipNetToMediaPhysAddress)")
            return retval
        return 1

    def _get_lldp_data(self):
        """
        Read parts of the LLDP mib for neighbors on interfaces
        Note that this needs to be called after _get_known_ethernet_addresses()
        as we need the Bridge-to-IfIndex mapping that is loaded there!
        Returns 1 on success, -1 on failure
        """
        # Probably don't need this part, already got most from MIB-2
        # retval = not self._get_branch_by_name(lldpLocPortTable):
        #    return False

        # this does not appear to be implemented in most gear:
        # retval = not self._get_branch_by_name(lldpRemLocalPortNum):
        #    return False

        # this should catch all the remote device info:
        # retval = not self._get_branch_by_name(lldpRemEntry):
        #    return False
        # return True

        # go read and parse LLDP data, we do NOT (False) want to cache this data!
        # we have a custom parser, so we do not have to run this through the long and slow default parser!
        retval = self._get_branch_by_name('lldpRemPortId', False, self._parse_mibs_lldp)
        if retval < 0:
            self._add_warning("Error getting 'LLDP-Remote-Ports' (lldpRemPortId)")
            return retval
        if retval > 0:  # there are neighbors entries! Go get the details.
            retval = self._get_branch_by_name('lldpRemPortDesc', False, self._parse_mibs_lldp)
            if retval < 0:
                self._add_warning("Error getting 'LLDP-Remote-Port-Description' (lldpRemPortDesc)")
                return retval
            retval = self._get_branch_by_name('lldpRemSysName', False, self._parse_mibs_lldp)
            if retval < 0:
                self._add_warning("Error getting 'LLDP-Remote-System-Name' (lldpRemSysName)")
                return retval
            retval = self._get_branch_by_name('lldpRemSysDesc', False, self._parse_mibs_lldp)
            if retval < 0:
                self._add_warning("Error getting 'LLDP-Remote-System-Decription' (lldpRemSysDesc)")
                return retval
            # get the enabled remote device capabilities
            retval = self._get_branch_by_name('lldpRemSysCapEnabled', False, self._parse_mibs_lldp)
            if retval < 0:
                self._add_warning("Error getting 'LLDP-Remote-System-Capabilities' (lldpRemSysCapEnabled)")
                return retval
            # and info about the remote chassis:
            retval = self._get_branch_by_name('lldpRemChassisIdSubtype', False, self._parse_mibs_lldp)
            if retval < 0:
                self._add_warning("Error getting 'LLDP-Remote-Chassis-Type' (lldpRemChassisIdSubtype)")
                return retval
            retval = self._get_branch_by_name('lldpRemChassisId', False, self._parse_mibs_lldp)
            if retval < 0:
                self._add_warning("Error getting 'LLDP-Remote-Chassis-Id' (lldpRemChassisId)")
                return retval

        return 1

    def _get_lacp_data(self):
        """
        Read the IEEE LACP mib, single mib counter gives us enough to identify
        the physical interfaces that are an LACP member.
        """

        # Get the admin key or "index" for aggregate interfaces
        retval = self._get_branch_by_name('dot3adAggActorAdminKey')
        if retval < 0:
            self._add_warning("Error getting 'LACP-Aggregate-Admin-Key' (dot3adAggActorAdminKey)")
            return retval

        # Get the admin key or "index" for physical member interfaces
        # this maps back to the logical or actor aggregates above in dot3adAggActorAdminKey
        retval = self._get_branch_by_name('dot3adAggPortActorAdminKey')
        if retval < 0:
            self._add_warning("Error getting 'LACP-Port-Admin-Key' (dot3adAggPortActorAdminKey)")
            return retval

        """
        # this is a shortcut to find aggregates and members all in one, but does not work everyone.
        retval = self._get_branch_by_name('dot3adAggPortAttachedAggID')
        if retval < 0:
            self._add_warning("Error getting 'LACP-Port-AttachedAggID' (dot3adAggPortAttachedAggID)")
            return retval
        """

        return retval

    def _get_syslog_msgs(self):
        """
        Read the SYSLOG-MSG-MIB: note this is meant for notifications, but we can read log size!
        """
        retval = self._get_branch_by_name('syslogMsgTableMaxSize')
        if retval < 0:
            self._add_warning("Error getting Log Size Info (syslogMsgTableMaxSize)")
        return retval

    def _test_read(self):
        """
        Test if read works
        Returns True or False
        """
        try:
            self._get(self.SYSOBJECTID)
            return True
        except SnmpError as error:
            return False

    def _test_write(self):
        """
        Test if write works, by re-writing SystemLocation
        Return True on success, False on failure
        """
        value = self._get(self.SYSLOCATION)
        retval = self._set(self.SYSLOCATION, value, 's')
        if retval != -1:
            return True
        return False

    def _set_allowed_vlans(self):
        """
        set the list of vlans defined on the switch that are allowed per the SwitchGroup.vlangroups/vlans
        self.vlans = {} dictionary of vlans on the current switch, i.e. Vlan() objects, but
        self.group.vlans and self.group.vlangroups is a list of allowed VLAN() Django objects (see switches/models.py)
        """

        dprint("_set_allowed_vlans()")
        # check the vlans on the switch (self.vlans) agains switchgroup.vlan_groups and switchgroup.vlans
        if self.group.read_only and self.request and not self.request.user.is_superuser:
            # Read-Only Group, no vlan allowed!
            return
        for switch_vlan_id in self.vlans.keys():
            if self.request and self.request.user.is_superuser:
                self.allowed_vlans[int(switch_vlan_id)] = self.vlans[switch_vlan_id]
            else:
                # first the switchgroup.vlan_groups:
                found_vlan = False
                for vlan_group in self.group.vlan_groups.all():
                    for group_vlan in vlan_group.vlans.all():
                        if int(group_vlan.vid) == int(switch_vlan_id):
                            self.allowed_vlans[int(switch_vlan_id)] = self.vlans[switch_vlan_id]
                            found_vlan = True
                            continue
                # check if this switch vlan is in the list of allowed vlans
                if not found_vlan:
                    for group_vlan in self.group.vlans.all():
                        if int(group_vlan.vid) == int(switch_vlan_id):
                            # save using the switch vlan name, which is possibly different from the VLAN group name!
                            self.allowed_vlans[int(switch_vlan_id)] = self.vlans[switch_vlan_id]
                            continue
        return

    def _can_manage_interface(self, iface):
        """
        Function meant to check if this interface can be managed.
        This allows for vendor-specific override in the vendor subclass, to detect e.g. stacking ports
        called from _set_interfaces_permissions() to check for each interface.
        Returns True by default, but if False, then _set_interfaces_permissions()
        will not allow any attribute of this interface to be managed (even then admin!)
        """
        return True

    def _set_interfaces_permissions(self):
        """
        For all found interfaces, check out rules to see if this user should be able see or edit them
        """
        dprint("_set_interfaces_permissions()")
        switch = self.switch
        group = self.group
        if self.request:
            user = self.request.user
        else:
            # we are running as a task, simulate 'admin'
            # permissions were checked when form was generated/submitted
            user = User.objects.get(pk=1)

        # find allowed vlans for this user
        self._set_allowed_vlans()

        # apply the permission rules to all interfaces
        for if_index in self.interfaces:
            iface = self.interfaces[if_index]

            # Layer 3 (routed mode) interfaces are denied (but shown)!
            if iface.is_routed:
                iface.manageable = False
                iface.allow_poe_toggle = False
                iface.can_edit_alias = False
                iface.visible = True
                iface.unmanage_reason = "Access denied: interface in routed mode!"
                continue

            if iface.type != IF_TYPE_ETHERNET and settings.HIDE_NONE_ETHERNET_INTERFACES:
                iface.manageable = False
                iface.allow_poe_toggle = False
                iface.can_edit_alias = False
                iface.visible = False
                continue

            # next check vendor-specific restrictions. This allows denying Stacking ports, etc.
            if not self._can_manage_interface(iface):
                iface.manageable = False
                iface.allow_poe_toggle = False
                iface.can_edit_alias = False
                iface.visible = True
                continue

            # Read-Only switch cannot be overwritten, not even by SuperUser!
            if group.read_only or switch.read_only or user.profile.read_only:
                iface.manageable = False
                iface.unmanage_reason = "Access denied: Read-Only"

            # super-users have access to all other attributes of interfaces!
            if user.is_superuser:
                iface.visible = True
                iface.allow_poe_toggle = True
                iface.can_edit_alias = True
                continue

            # globally allow PoE toggle:
            if settings.ALWAYS_ALLOW_POE_TOGGLE:
                iface.allow_poe_toggle = True

            # we can also enable PoE toggle on user, group or switch, if allowed somewhere:
            if switch.allow_poe_toggle or group.allow_poe_toggle or user.profile.allow_poe_toggle:
                iface.allow_poe_toggle = True

            # we can also modify interface description, if allowed everywhere:
            if switch.edit_if_descr and group.edit_if_descr and user.profile.edit_if_descr:
                iface.can_edit_alias = True

            # Next apply any rules that HIDE first !!!

            # check interface types first, only show ethernet
            # this hides vlan, loopback etc. interfaces for the regular user.
            if iface.type not in visible_interfaces.keys():
                iface.visible = False
                iface.manageable = False  # just to be safe :-)
                iface.unmanage_reason = "Switch is not visible!"    # should never show!
                continue

            # see if this _get_snmp_session matches the interface name, e.g. GigabitEthernetx/x/x
            if settings.IFACE_HIDE_REGEX_IFNAME != "":
                match = re.match(settings.IFACE_HIDE_REGEX_IFNAME, iface.name)
                if match:
                    iface.manageable = False  # match, so we cannot modify! Show anyway...
                    iface.unmanage_reason = "Access denied: interface name matches admin setting!"
                    continue

            # see if this regex matches the interface 'ifAlias' aka. the interface description
            if settings.IFACE_HIDE_REGEX_IFDESCR != "":
                match = re.match(settings.IFACE_HIDE_REGEX_IFDESCR, iface.alias)
                if match:
                    iface.manageable = False  # match, so we cannot modify! Show anyway...
                    iface.unmanage_reason = "Access denied: interface description matches admin setting!"
                    continue

            # see if we should hide interfaces with speeds above this value in Mbps.
            if int(settings.IFACE_HIDE_SPEED_ABOVE) > 0 and int(iface.hc_speed) > int(settings.IFACE_HIDE_SPEED_ABOVE):
                iface.manageable = False  # match, so we cannot modify! Show anyway...
                iface.unmanage_reason = "Access denied: interface speed is denied by admin setting!"
                continue

            # check if this vlan is in the group allowed vlans list:
            if int(iface.untagged_vlan) not in self.allowed_vlans.keys():
                iface.manageable = False  # match, so we cannot modify! Show anyway...
                iface.unmanage_reason = "Access denied: vlan is not allowed!"
                continue

        dprint("_set_interfaces_permissions() done!")
        return

    def _clear_session_oid_cache(self):
        """
        call the static function to clear our our web session database
        """
        return clear_session_oid_cache(self.request)

    def _probe_mibs(self):
        """
        Probe the various mibs to see if they are supported
        Returns True if we can probe snmp, False if not
        """
        # this will read the SystemMIB and update the System OID of the switch
        retval = self._get_system_data()
        if retval != -1:
            self.switch.snmp_oid = self.get_cached_oid(sysObjectID)
            self.switch.save()
            return True
        return False

    def _add_warning(self, warning):
        """
        Add a warning to the list!
        """
        self.warnings.append(warning)
        # add a log message
        log = Log(group=self.group,
            switch=self.switch,
            ip_address=get_remote_ip(self.request),
            type=LOG_TYPE_WARNING,
            action=LOG_WARNING_SNMP_ERROR,
            description=warning)
        if self.request:
            log.user = self.request.user
        log.save()
        # done!
        return

    #
    # "Public" interface methods
    #

    def add_vendor_data(self, category, name, value):
        """
        This adds a vendor specific piece of information to the "Info" tab.
        Items are ordered by category heading, then name/value pairs
        """
        vdata = VendorData(name, value)
        if category not in self.vendor_data.keys():
            self.vendor_data[category] = []
        self.vendor_data[category].append(vdata)

    def can_change_interface_vlan(self):
        """
        Return True if we can change a vlan on an interface, False if not
        """
        # for standard MIB version, return True
        return True

    def can_save_config(self):
        """
        If True, this instance can save the running config to startup
        Ie. "write mem" is implemented via an SNMP interfaces
        This should be implemented in a vendor-specific sub-class. We just return False here.
        """
        return False

    def save_running_config(self):
        """
        Vendor-agnostic interface to save the current config to startup
        To be implemented by sub-classes, eg CISCO-SNMP, H3C-SNMP
        Returns 0 is this succeeds, -1 on failure. self.error() will be set in that case
        """
        return -1

    def get_switch_basic_info(self):
        """
        If not found in the local cache (from the session),
        then bulk-walk the needed MIBs to get the basics of this switch:
        System, Interfaces, Aliases, Qbridge and PoE MIBs
        """
        self.error.clear()
        if not self.cached_oid_data:
            self.basic_info_read_time = time.time()
            retval = self._get_system_data()
            if retval != -1:
                retval = self._get_interface_data()
                if retval != -1:
                    retval = self._get_vlan_data()
                    if retval != -1:
                        retval = self._get_my_ip4_addresses()
                        if retval != -1:
                            retval = self._get_lacp_data()
                            if retval != -1:
                                retval = self._get_poe_data()
                                if retval != -1:
                                    # try to map poe port info to actual interfaces
                                    self._map_poe_port_entries_to_interface()
                                    # time it took to read all this.
                                    self.basic_info_duration = int((time.time() - self.basic_info_read_time) + 0.5)
                                    # cache the data in the session,
                                    # so we can avoid reading the switch all the time
                                    self._set_http_session_cache()
                                    # set the permissions to the interfaces:
                                    self._set_interfaces_permissions()
                                    self.switch.save()  # update counters
                                    return True
            return False
        else:
            # set the permissions to the interfaces:
            self._set_interfaces_permissions()
            return True

    def get_switch_hardware_details(self):
        """
        Get all (possible) hardware info, stacking details, etc.
        """
        # call the vendor-specific data first, if implemented
        self._get_vendor_data()
        # read Syslog MIB
        self._get_syslog_msgs()
        # next read the standard Entity MIB hardware info
        retval = self._get_entity_data()
        if retval > 0:
            # need to store this in the session
            self.hwinfo_needed = False
            self._set_http_session_cache()
            return True
        return False

    def get_switch_client_data(self):
        """
        Get additional information about switch ports, eg. ethernet address, counters...
        Note this is never cached, so anytime we get fresh, "live" data!
        """
        # now load the ethernet tables every time, without caching
        start_time = time.time()
        retval = self._get_known_ethernet_addresses()
        if retval != -1:  # no error
            # read LLDP as well
            retval = self._get_lldp_data()
            if retval != -1:
                # and the arp tables (after we found ethernet address, so we can update with IP)
                retval = self._get_arp_data()
                self.detailed_info_duration = int((time.time() - start_time) + 0.5)
                if retval != -1:
                    self.switch.save()  # update counters
                    return True
        return False

    def get_interface_by_index(self, index):
        """
        Return the Interface() object for the given interface ifIndex
        """
        if index in self.interfaces.keys():
            return self.interfaces[index]
        return False

    def get_switch_vlans(self):
        """
        Return the vlans defined on this switch
        """
        return self.vlans

    def get_vlan_by_id(self, vlan_id):
        """
        Return the Vlan() object for the given id
        """
        if vlan_id in self.vlans.keys():
            return self.vlans[vlan_id]
        return False

    def set_interface_untagged_vlan(self, if_index, old_vlan_id, new_vlan_id):
        """
        Change the VLAN via the Q-BRIDGE MIB (ie generic)
        Return -1 if invalid interface, or value of _set() call
        """
        iface = self.get_interface_by_index(if_index)
        # now get the Q-Bridge PortID
        if iface:
            port_id = self._get_port_id_from_if_index(if_index)
            # set this switch port on the new vlan:
            # Q-BIRDGE mib: VlanIndex = Unsigned32
            dprint("Setting NEW VLAN on port")
            retval = self._set("%s.%s" % (snmp_mib_variables['dot1qPvid'], str(port_id)), int(new_vlan_id), 'u')
            if retval == -1:
                return retval

            # some switches need a little "settling time" here (value is in seconds)
            time.sleep(0.5)

            # Remove port from list of ports on old vlan,
            # i.e. read current Egress PortList bitmap first:
            (error_status, snmpval) = self._get("%s.%s" % (snmp_mib_variables['dot1qVlanStaticEgressPorts'], old_vlan_id))
            if error_status:
                # Hmm, not sure what to do
                return -1

            # now calculate new bitmap by removing this switch port
            old_vlan_portlist = PortList()
            old_vlan_portlist.from_unicode(snmpval.value)
            dprint("OLD VLAN Current Egress Ports = %s" % old_vlan_portlist.to_hex_string())
            # unset bit for port, i.e. remove from active portlist on vlan:
            old_vlan_portlist[port_id] = 0

            # now send update to switch:
            # use PySNMP to do this work:
            octet_string = OctetString(hexValue=old_vlan_portlist.to_hex_string())
            pysnmp = pysnmpHelper(self.switch)
            (error_status, details) = pysnmp.set("%s.%s" % (snmp_mib_variables['dot1qVlanStaticEgressPorts'], old_vlan_id), octet_string)
            if error_status:
                self.error.status = True
                self.error.description = "Error in setting port (dot1qVlanStaticEgressPorts)"
                self.error.details = details
                return -1

            # and re-read the dot1qVlanCurrentEgressPorts, all ports
            # tagged/untagged on the old and new vlan
            # note the 0 to hopefull deactivate time filter!
            dprint("Get OLD VLAN Current Egress Ports")
            (error_status, snmpval) = self._get("%s.0.%s" %
                                                (snmp_mib_variables['dot1qVlanCurrentEgressPorts'], old_vlan_id))
            dprint("Get NEW VLAN Current Egress Ports")
            (error_status, snmpval) = self._get("%s.0.%s" %
                                                (snmp_mib_variables['dot1qVlanCurrentEgressPorts'], new_vlan_id))
            return 0

        # interface not found, return False!
        return -1

    def display_name(self):
        return "%s for %s" % (self.name, self.switch.name)

    def __str__(self):
        return self.display_name
# --- End of SnmpConnector() ---


def oid_in_branch(mib_branch, oid):
    """
    Check if a given OID is in the branch, if so, return the 'ending' portion after the mib_branch
    E.g. in many cases, the oid end is the 'ifIndex' or vlan_id, or such.
    mib_branch should contain starting DOT (easysnmp returns the OID with starting dot), but NOT trailing dot !!!
    """
    if not isinstance(oid, str):
        return False
    mib_branch += "."  # make sure the OID branch terminates with a . for the next series of data
    oid_len = len(oid)
    branch_len = len(mib_branch)
    if (oid_len > branch_len and oid[:branch_len] == mib_branch):  # need to check for trailing .
        return oid[branch_len:]    # get data past the "root" oid + the period (+1)
    return False


def _clear_session_save_needed(request):
    """
    Clear the session variable that indicates the switch config needs saving
    """
    if request and 'save_needed' in request.session.keys():
        del request.session['save_needed']


def clear_session_oid_cache(request):
    """
    clear all session data storage, because we want to re-read switch
    or because we changed switches
    """
    if request:
        if 'switch_id' in request.session.keys():
            del request.session['switch_id']
        if 'oid_cache' in request.session.keys():
            del request.session['oid_cache']
        _clear_session_save_needed(request)


def get_switch_enterprise_info(system_oid):
    """
    Return the Enterprise name from the Object ID given
    """
    sub_oid = oid_in_branch(enterprises, system_oid)
    if sub_oid:
        parts = sub_oid.split('.', 1)  # 1 means one split, two elements!
        enterprise_id = int(parts[0])
        # here we go:
        if enterprise_id in enterprise_id_info.keys():
            return enterprise_id_info[enterprise_id]
        else:
            return 'Unknown'
    else:
        # sub oid, ie enterprise data, not found!
        return 'Not found'
