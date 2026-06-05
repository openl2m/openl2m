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
"""constants.py defines Aruba AOS-CX-specific SNMP-related variables. These are mostly MIB OIDs and their value definitions."""

from switches.connect.snmp.constants import snmp_mib_variables, enterprise_id_info

#
# Aruba 'new style' devices
#
ENTERPRISE_ID_HP_ENTERPRISE = 47196
# Note: this is registered as 'Hewlett Packard Enterprise',
# but now doing business as Aruba.
enterprise_id_info[ENTERPRISE_ID_HP_ENTERPRISE] = "Aruba (HPE)"

# AOS-CX uses the ieee QBridge Mibs for vlan info (ieee8021QBridgeVlan)
# defind in switches.connect.snmp.constants.*
# see more at https://oidref.com/1.3.111.2.802.1.1.4.1.4

# AOS-CX also uses numerous HP/ProCurve snmp counters.
# this are defined in switches.connect.snmp.procurve.constants

#
# ARUBAWIRED-VSX-MIB has VSX stacking info
#
arubaWiredVsxMIB = ".1.3.6.1.4.1.47196.4.1.1.3.7"

# arubaWiredVsxConfig = "".1.3.6.1.4.1.47196.4.1.1.3.7.1"

# arubaWiredVsxIslConfig = ".1.3.6.1.4.1.47196.4.1.1.3.7.1.1"
arubaWiredVsxIslPort = ".1.3.6.1.4.1.47196.4.1.1.3.7.1.1.1"

# arubaWiredVsxKeepAliveConfig = ".1.3.6.1.4.1.47196.4.1.1.3.7.1.2"
arubaWiredVsxKeepAliveSrcIPAddrType = ".1.3.6.1.4.1.47196.4.1.1.3.7.1.2.1"
arubaWiredVsxKeepAliveVrf = ".1.3.6.1.4.1.47196.4.1.1.3.7.1.2.3"
arubaWiredVsxKeepAlivePeerIPAddrType = ".1.3.6.1.4.1.47196.4.1.1.3.7.1.2.5"
arubaWiredVsxKeepAlivePeerIPAddr = ".1.3.6.1.4.1.47196.4.1.1.3.7.1.2.6"

# arubaWiredVsxAggregatorConfig = ".1.3.6.1.4.1.47196.4.1.1.3.7.1.3"
# nothing of interest here...

# arubaWiredVsxGlobalConfiguration = ".1.3.6.1.4.1.47196.4.1.1.3.7.1.4"
arubaWiredVsxDeviceRole = ".1.3.6.1.4.1.47196.4.1.1.3.7.1.4.1"
VSX_ROLE_PRIMARY = 1  # 1	primary
VSX_ROLE_SECONDARY = 2  # 2	secondary
VSX_ROLE_NOT_SET = 3  # 3	notConfigured
VSX_Roles = {
    VSX_ROLE_PRIMARY: "Primary",
    VSX_ROLE_SECONDARY: "Secondary",
    VSX_ROLE_NOT_SET: "Not Configured",
}

arubaWiredVsxConfigSync = ".1.3.6.1.4.1.47196.4.1.1.3.7.1.4.2"
VSX_SYNC_ENABLED = 1  # 1	enabled
VSX_SYNC_DISABLED = 2  # 2	disabled
VSX_SyncState = {
    VSX_SYNC_ENABLED: "Enabled",
    VSX_SYNC_DISABLED: "Disabled",
}

# arubaWiredVsxStatus = ".1.3.6.1.4.1.47196.4.1.1.3.7.2"

# arubaWiredVsxIslStatus = ".1.3.6.1.4.1.47196.4.1.1.3.7.2.1"
arubaWiredVsxIslOperState = ".1.3.6.1.4.1.47196.4.1.1.3.7.2.1.1"
VSX_ISL_STATE_INIT = 1  # 1	init
VSX_ISL_STATE_OUT_SYNC = 2  # 2	outSync
VSX_ISL_STATE_IN_SYNC = 3  # 3	inSync
VSX_IslStates = {
    VSX_ISL_STATE_INIT: "Init",
    VSX_ISL_STATE_OUT_SYNC: "Out-of-Sync",
    VSX_ISL_STATE_IN_SYNC: "In-Sync",
}

# arubaWiredVsxKeepAliveStatus = ".1.3.6.1.4.1.47196.4.1.1.3.7.2.2"
arubaWiredVsxKeepAliveOperState = ".1.3.6.1.4.1.47196.4.1.1.3.7.2.2.1"
VSX_KA_STATE_INIT = 1  # 1	init
VSX_KA_STATE_CONFIGURED = 2  # 2	configured
VSX_KA_STATE_SYNCHED = 3  # 3	inSyncEstablished
VSX_KA_STATE_NOT_SYNCHED = 4  # 4	outofSyncEstablished
VSX_KA_STATE_INIT_ESTABLISHED = 5  # 5	initEstablished
VSX_KA_STATE_FAILED = 6  # 6	failed
VSX_KA_STATE_STOPPED = 7  # 7	stopped
VSX_KaStates = {
    VSX_KA_STATE_INIT: "Init",
    VSX_KA_STATE_CONFIGURED: "Configured",
    VSX_KA_STATE_SYNCHED: "In-Sync Established",
    VSX_KA_STATE_NOT_SYNCHED: "Out-of-Sync Established",
    VSX_KA_STATE_INIT_ESTABLISHED: "Init Established",
    VSX_KA_STATE_FAILED: "Failed",
    VSX_KA_STATE_STOPPED: "Stopped",
}

#
# the ARUBAWIRED-POE mib is used for PoE reporting:
# see https://mibs.observium.org/mib/ARUBAWIRED-POE-MIB/
#

# the power drawn, in milliwatts:
arubaWiredPoePethPsePortPowerDrawn = ".1.3.6.1.4.1.47196.4.1.1.3.8.1.1.1.7"
snmp_mib_variables["arubaWiredPoePethPsePortPowerDrawn"] = arubaWiredPoePethPsePortPowerDrawn

# from ARUBAWIRED-VSFv2-MIB
# https://mibs.observium.org/mib/ARUBAWIRED-VSFv2-MIB/
arubaWiredVsfv2MemberPartNumber = ".1.3.6.1.4.1.47196.4.1.1.3.15.1.2.1.4"
snmp_mib_variables["arubaWiredVsfv2MemberPartNumber"] = arubaWiredVsfv2MemberPartNumber

arubaWiredVsfv2MemberProductName = ".1.3.6.1.4.1.47196.4.1.1.3.15.1.2.1.6"
snmp_mib_variables["arubaWiredVsfv2MemberProductName"] = arubaWiredVsfv2MemberProductName

# the OIDs for "write mem"
arubaWiredVsfv2ConfigOperationType = ".1.3.6.1.4.1.47196.4.1.1.3.20.1.0.1.1.18.5"
arubaWiredVsfv2ConfigOperationSetSource = ".1.3.6.1.4.1.47196.4.1.1.3.20.1.0.1.1.2.5"
arubaWiredVsfv2ConfigOperationSetDestination = ".1.3.6.1.4.1.47196.4.1.1.3.20.1.0.1.1.3.5"
ARUBA_CONFIG_ACTION_WRITE = 4
ARUBA_CONFIG_TYPE_STARTUP = 2
ARUBA_CONFIG_TYPE_RUNNING = 3

#
# Transceiver interface info, from v10.14.1000 and newer
# see https://arubanetworking.hpe.com/techdocs/AOS-CX/10.14/HTML/snmp_mib/Content/Chp_MIB_sppt/new-mib-xcvr.htm
# Note: as of July 2025, the above table is incorrect, it misses a 1 in the OID:
# eg ...27.1.1.1.2 should be ...27.1.1.1.1.2
#
# from the ARUBAWIRED-PM-MIB.mib, the "arubaWiredPmXcvrTable"
# arubaWiredPmMIB = wndFeatures . 27 = .1.3.6.1.4.1.47196.4.1.1.3.27
# arubaWiredPmObjects = arubaWiredPmMIB 1 = .27.1
# arubaWiredPmXcvrInfo = arubaWiredPmObjects 1 = 27.1.1
# arubaWiredPmXcvrTable = arubaWiredPmXcvrInfo 1  = 27.1.1.1
# arubaWiredPmXcvrEntry = arubaWiredPmXcvrTable 1 = 27.1.1.1.1
arubaWiredPmXcvrEntry = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1"
snmp_mib_variables["arubaWiredPmXcvrEntry"] = arubaWiredPmXcvrEntry
# entries:
arubaWiredPmXcvrPortIfIndex = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.1"
arubaWiredPmXcvrPortDesc = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.2"
arubaWiredPmXcvrDescription = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.3"
arubaWiredPmXcvrProductNum = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.4"
arubaWiredPmXcvrSerialNum = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.5"
arubaWiredPmXcvrPartNum = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.6"
arubaWiredPmXcvrType = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.7"
arubaWiredPmXcvrConnectorType = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.8"
arubaWiredPmXcvrConnectorStatus = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.9"
arubaWiredPmXcvrConnectorStatusReason = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.10"
arubaWiredPmXcvrCableType = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.11"
arubaWiredPmXcvrWavelength = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.12"
arubaWiredPmXcvrSmfTxDist = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.13"
arubaWiredPmXcvrMmfOm1TxDist = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.14"
arubaWiredPmXcvrMmfOm2TxDist = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.15"
arubaWiredPmXcvrMmfOm3TxDist = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.16"
arubaWiredPmXcvrMmfOm4TxDist = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.17"
arubaWiredPmXcvrMmfOm5TxDist = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.18"
arubaWiredPmXcvrCableLength = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.19"
arubaWiredPmXcvrMaxSpeed = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.20"
arubaWiredPmXcvrMaxPower = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.21"
arubaWiredPmXcvrAdapterType = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.22"
arubaWiredPmXcvrAdapterStatus = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.23"
arubaWiredPmXcvrAdapterStatusReason = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.24"
arubaWiredPmXcvrAdapterProductNum = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.25"
arubaWiredPmXcvrAdapterSerialNum = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.26"
arubaWiredPmXcvrThermalClass = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.27"
arubaWiredPmXcvrDiagnostics = ".1.3.6.1.4.1.47196.4.1.1.3.27.1.1.1.1.28"
