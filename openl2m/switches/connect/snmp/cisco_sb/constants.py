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
"""constants.py defines Cisco-Small-Business switches specific SNMP-related variables.
   These are mostly MIB OIDs and their value definitions."""

from switches.connect.snmp.constants import snmp_mib_variables

# This Cisco device OID start indicates the Small Business 'family' of equipment:
ciscoSB = ".1.3.6.1.4.1.9.6.1"

# here is an OLD list of device oid's in this SB group:
# https://www.cisco.com/c/en/us/support/docs/smb/switches/cisco-small-business-200-series-smart-switches/smb5512-cisco-small-business-switches-model-object-identifiers-oids.html

#
# Cisco SB devices, "Small Business" switches
# Only tested on CBS-350 switch.
#
# https://mibs.observium.org/mib/CISCOSB-MIB/ = .1.3.6.1.4.1.9.6.1.101
#

#
# Interface / Port related
# from the CISCOSB-rlInterfaces mib
#
# this show the physical port type, eg copper, fiber.
swIfTransceiverType = ".1.3.6.1.4.1.9.6.1.101.43.1.1.7"
snmp_mib_variables["swIfTransceiverType"] = swIfTransceiverType
SB_TX_TYPE_COPPER = 1
SB_TX_TYPE_FIBER = 2
SB_TX_TYPE_COMBO = 3  # this really is combo/unknown
SB_TX_TYPE_COMBO_FIBER = 4  # an optical transciever is used.
sb_tx_type = {}
sb_tx_type[SB_TX_TYPE_COPPER] = "Copper"
sb_tx_type[SB_TX_TYPE_FIBER] = "FiberOptics"
sb_tx_type[SB_TX_TYPE_COMBO] = "Fiber/Copper Combo Port"  # combo port without transceiver
sb_tx_type[SB_TX_TYPE_COMBO_FIBER] = "FiberOptics Combo"  # combo port with optical transceiver installed.

#
# VLAN related
#
# see https://mibs.observium.org/mib/CISCOSB-vlan-MIB/
# and https://github.com/librenms/librenms/blob/master/mibs/cisco/CISCOSB-vlan-MIB
# and all high-level entries at https://mibbrowser.online/mibdb_search.php?mib=CISCOSB-MIB

# see if the CISCOSB-vlan-MIB exists:
# vlan = ".1.3.6.1.4.1.9.6.1.101.48"
vlanMibVersion = ".1.3.6.1.4.1.9.6.1.101.48.1"
snmp_mib_variables["vlanMibVersion"] = vlanMibVersion

# vlan state, ie access, general, trunk
vlanPortModeState = ".1.3.6.1.4.1.9.6.1.101.48.22.1.1"
snmp_mib_variables["vlanPortModeState"] = vlanPortModeState
SB_VLAN_MODE_GENERAL = 10
SB_VLAN_MODE_ACCESS = 11
SB_VLAN_MODE_TRUNK = 12
sb_vlan_mode = {}
sb_vlan_mode[SB_VLAN_MODE_GENERAL] = "General"
sb_vlan_mode[SB_VLAN_MODE_ACCESS] = "Access"
sb_vlan_mode[SB_VLAN_MODE_TRUNK] = "Trunk"

# access mode ports set the vlan on this mib:
vlanAccessPortModeVlanId = ".1.3.6.1.4.1.9.6.1.101.48.62.1.1"
snmp_mib_variables["vlanAccessPortModeVlanId"] = vlanAccessPortModeVlanId

# trunk mode ports set the PVID/untagged vlan on this mib:
vlanTrunkPortModeNativeVlanId = ".1.3.6.1.4.1.9.6.1.101.48.61.1.1"
snmp_mib_variables["vlanTrunkPortModeNativeVlanId"] = vlanTrunkPortModeNativeVlanId

#
# Small Business COPY MIB, save configs!
# https://github.com/librenms/librenms/blob/master/mibs/cisco/CISCOSB-COPY-MIB
# https://mibs.observium.org/mib/CISCOSB-COPY-MIB/
# rlCopy = .1.3.6.1.4.1.9.6.1.101.87
#
# the save running-config process is described at
# https://www.cisco.com/c/en/us/support/docs/smb/switches/Catalyst-switches/kmgmt3810-triggering-configuration-file-copies-to-tftp-server-via-snmp.html
# and
# https://community.cisco.com/t5/switches-small-business/how-to-save-config-through-snmp/td-p/1667917
# (the latter has old pre-Cisco OIDs !)
#

# rlCopyRowStatus = 4 = createAndGo (initiates the process)
createAndGo = 4
rlCopyRowStatus = ".1.3.6.1.4.1.9.6.1.101.87.2.1.17"
snmp_mib_variables["rlCopyRowStatus"] = rlCopyRowStatus
#rlCopySourceLocation = 1 = local (source is the switch)
local = 1
rlCopySourceLocation = ".1.3.6.1.4.1.9.6.1.101.87.2.1.3"
snmp_mib_variables["rlCopySourceLocation"] = rlCopySourceLocation
# rlCopySourceFileType = 2 = runningConfig
runningConfig = 2
rlCopySourceFileType = ".1.3.6.1.4.1.9.6.1.101.87.2.1.7"
snmp_mib_variables["rlCopySourceFileType"] = rlCopySourceFileType
# rlCopyDestinationLocation = 1 = local
rlCopyDestinationLocation = ".1.3.6.1.4.1.9.6.1.101.87.2.1.8"
snmp_mib_variables["rlCopyDestinationLocation"] = rlCopyDestinationLocation
# rlCopyDestinationFileType = 3 = startupConfig
startupConfig = 3
rlCopyDestinationFileType = ".1.3.6.1.4.1.9.6.1.101.87.2.1.12"
snmp_mib_variables["rlCopyDestinationFileType"] = rlCopyDestinationFileType
