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
"""constants.py defines Arista-specific SNMP-related variables. These are mostly MIB OIDs and their value definitions."""

from switches.connect.snmp.constants import snmp_mib_variables, enterprise_id_info

#
# Arista networks
# MIBs are at https://www.arista.com/en/support/product-documentation/arista-snmp-mibs
#
ENTERPRISE_ID_ARISTA = 30065
enterprise_id_info[ENTERPRISE_ID_ARISTA] = "Arista Networks"

# VRF info from https://www.arista.com/assets/data/docs/MIBS/ARISTA-VRF-MIB.txt
arista = "Enterprise 30065"
aristaMibs = "arista 3"
aristaVrfMIB = "aristaMibs 18"

aristaVrfMibObjects = "aristaVrfMIB 1"

aristaVrfTable = ".1.3.6.1.4.1.30065.3.18.1.1"  # "aristaVrfMibObjects 1"
snmp_mib_variables["aristaVrfTable"] = aristaVrfTable

aristaVrfEntry = ".1.3.6.1.4.1.30065.3.18.1.1.1"
snmp_mib_variables["aristaVrfEntry"] = aristaVrfEntry  # "aristaVrfTable 1", indexed by vrfName

aristaVrfName = ".1.3.6.1.4.1.30065.3.18.1.1.1.1"
snmp_mib_variables["aristaVrfName"] = aristaVrfName

aristaVrfRoutingStatus = ".1.3.6.1.4.1.30065.3.18.1.1.1.2"
snmp_mib_variables["aristaVrfRoutingStatus"] = aristaVrfRoutingStatus
# these are bit locations, if set IPv4 or 6 is enabled:
# VRF_ROUTING_IPV4 = 0
# VRF_ROUTING_IPV6 = 1
ARISTA_VRF_ROUTING_IPV4_BIT = 0x1
ARISTA_VRF_ROUTING_IPV6_BIT = 0x2

aristaVrfRouteDistinguisher = ".1.3.6.1.4.1.30065.3.18.1.1.1.3"
snmp_mib_variables["aristaVrfRouteDistinguisher"] = aristaVrfRouteDistinguisher

aristaVrfState = ".1.3.6.1.4.1.30065.3.18.1.1.1.4"
snmp_mib_variables["aristaVrfState"] = aristaVrfState

ARISTA_VRF_ACTIVE = 1
ARISTA_VRF_INACTIVE = 2


# the VRF IF Table entries have the lists of interfaces that are part of a VRF
# indexed by interface id, value is the VRF name:
# aristaVrfIfTable = aristaVrfMibObjects 2
# aristaVrfIfEntry = aristaVrfIfTable 1
# aristaVrfIfMembership = aristaVrfIfEntry 1

aristaVrfIfMembership = ".1.3.6.1.4.1.30065.3.18.1.2.1.1"
# eg:
# .1.3.6.1.4.1.30065.3.18.1.2.1.1.999001 = STRING: "MGMT"
# interface index 999001 is member of "MGMT"
snmp_mib_variables["aristaVrfIfMembership"] = aristaVrfIfMembership

# Arista Config-COPY mib
# https://www.arista.com/assets/data/docs/MIBS/ARISTA-CONFIG-COPY-MIB.txt
# https://mibs.observium.org/mib/ARISTA-CONFIG-COPY-MIB/

# aristaMibs = .1.3.6.1.4.1.30065.3
# aristaConfigCopyMIB = aristaMibs 7
# aristaConfigCopyCommandTable = aristaConfigCopyMIB 1
# aristaConfigCopyCommandEntry = aristaConfigCopyCommandTable 1

# aristaConfigCopyCommandEntry OBJECT-TYPE
#     SYNTAX          AristaConfigCopyCommandEntry
#     MAX-ACCESS      not-accessible
#     STATUS          current
#     DESCRIPTION     "A copy request.

#                     A management station should generate a unique ID and name
#                     (as the index) for each copy request. This prevents multiple
#                     management stations or applications from using same index
#                     and causing conflicts in same row.

#                     After an unique index is generated, the management station
#                     could create a row with that index and setup a copy request.

#                     Once a copy request is setup correctly with both source and
#                     destination URIs, it can be queued by setting the row status
#                     to active. The row creation, copy request setup and row
#                     activation can be done in one or multiple SET requests.

#                     The status of the copy request may change after the request
#                     is queued. It can be retrieved at any time before the request
#                     is aged out by the agent.
#
# aristaConfigCopyCommandEntry = .1.3.6.1.4.1.30065.3.7.1.1

# Note: we set a unique name using the table index for the word "save":
# default "job ID" that exists on Arista switches is "7.100.101.102.97.117.108.116"
# where 7 is length of string, and 100.101.102.97.117.108.116 decodes to ascii "default"!
default_job_id = "7.100.101.102.97.117.108.116"
# we create a new job with the index save:
save_job_id = "4.115.97.118.101"  # "save", length 4

# The source URI of a copy request.
# The URI format is: scheme://[username:password@]host/path

# Supported URI schemes are: file, flash, extension, system,
# ftp, http, https and tftp. username and password may be
# required for a network URI scheme (e.g. ftp).

aristaConfigCopyName = ".1.3.6.1.4.1.30065.3.7.1.1.1"
aristaConfigCopyId = ".1.3.6.1.4.1.30065.3.7.1.1.2"

# For convenience, two aliases are supported:
#     startup-config -> flash://startup-config
#     running-config -> system://running-config "
aristaConfigCopySourceUri = ".1.3.6.1.4.1.30065.3.7.1.1.3"
aristaConfigCopyDestUri = ".1.3.6.1.4.1.30065.3.7.1.1.4"

# "The state of a copy request."
aristaConfigCopyState = ".1.3.6.1.4.1.30065.3.7.1.1.5"
# ConfigCopyState ::= TEXTUAL-CONVENTION
# inactive:   no copy request has been queued yet. This is
#             the default state when a row is created.
# scheduled:  the copy request has been scheduled to run, but
#             has not started yet (probably waiting for ealier
#             copy requests to complete).
# running:    the copy request has been started.
# completed:  the copy request is completed with success.
# failed:     the copy request failed (probably because network
#             problem, timeout, permission denial, etc.)
ConfigCopyState_inactive = 0
ConfigCopyState_scheduled = 1
ConfigCopyState_running = 2
ConfigCopyState_completed = 3
ConfigCopyState_failed = 4

aristaConfigCopyTimeout = ".1.3.6.1.4.1.30065.3.7.1.1.6"
aristaConfigCopyTimeStarted = ".1.3.6.1.4.1.30065.3.7.1.1.7"
aristaConfigCopyTimeCompleted = ".1.3.6.1.4.1.30065.3.7.1.1.8"
aristaConfigCopyFailureCause = ".1.3.6.1.4.1.30065.3.7.1.1.9"
aristaConfigCopyFailureMessage = ".1.3.6.1.4.1.30065.3.7.1.1.10"

# "The row status of a copy request.
# A new copy request is instantiated by creating a new row.
# An existing copy request is queued by activating a row, or
# cancelled by destroying a row."
aristaConfigCopyRowStatus = ".1.3.6.1.4.1.30065.3.7.1.1.11"


# from https://www.reddit.com/r/Arista/comments/v6tfs9/save_config_via_snmp/
# src_oid = '1.3.6.1.4.1.30065.3.7.1.1.3.7.100.101.102.97.117.108.116.0' = "running-config"
# dst_oid = '1.3.6.1.4.1.30065.3.7.1.1.4.7.100.101.102.97.117.108.116.0' = "startup-config"
# status_oid = '1.3.6.1.4.1.30065.3.7.1.1.11.7.100.101.102.97.117.108.116.0' = 1 (start job)
# where 100.101.102.97.117.108.116 = "default" encoded as ascii, the default job.
#
# The first two are the src and dst filenames. In the case of saving the config,
# these are of course 'running-config' and 'startup-config' respectively. Both of those OIDs are OctetString.
# After you set those, you just need to set the status_oid to 1 (Active).
# This is an Integer32. Setting this to 1 is what "executes" the job.
# The end portion of those OIDs (7.100.101.102.97.117....) decode to...stuff.
# But part of it in ASCII is "default". So I'm guessing those OIDs are the "default" job that's always present.
