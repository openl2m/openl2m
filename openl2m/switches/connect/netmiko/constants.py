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
# the various device types supported by the current Netmiko library (July 2019)
NETMIKO_DEVICE_TYPES = (
    ('a10', 'a10'),
    ('accedian', 'accedian'),
    ('alcatel_aos', 'alcatel_aos'),
    ('alcatel_sros', 'alcatel_sros'),
    ('apresia_aeos', 'apresia_aeos'),
    ('arista_eos', 'arista_eos'),
    ('aruba_os', 'aruba_os'),
    ('avaya_ers', 'avaya_ers'),
    ('avaya_vsp', 'avaya_vsp'),
    ('brocade_fastiron', 'brocade_fastiron'),
    ('brocade_netiron', 'brocade_netiron'),
    ('brocade_nos', 'brocade_nos'),
    ('brocade_vdx', 'brocade_vdx'),
    ('brocade_vyos', 'brocade_vyos'),
    ('calix_b6', 'calix_b6'),
    ('checkpoint_gaia', 'checkpoint_gaia'),
    ('ciena_saos', 'ciena_saos'),
    ('cisco_asa', 'cisco_asa'),
    ('cisco_ios', 'cisco_ios'),
    ('cisco_nxos', 'cisco_nxos'),
    ('cisco_s300', 'cisco_s300'),
    ('cisco_tp', 'cisco_tp'),
    ('cisco_wlc', 'cisco_wlc'),
    ('cisco_xe', 'cisco_xe'),
    ('cisco_xr', 'cisco_xr'),
    ('cloudgenix_ion', 'cloudgenix_ion'),
    ('coriant', 'coriant'),
    ('dell_dnos9', 'dell_dnos9'),
    ('dell_force10', 'dell_force10'),
    ('dell_isilon', 'dell_isilon'),
    ('dell_os10', 'dell_os10'),
    ('dell_os6', 'dell_os6'),
    ('dell_os9', 'dell_os9'),
    ('dell_powerconnect', 'dell_powerconnect'),
    ('eltex', 'eltex'),
    ('endace', 'endace'),
    ('enterasys', 'enterasys'),
    ('extreme', 'extreme'),
    ('extreme_ers', 'extreme_ers'),
    ('extreme_exos', 'extreme_exos'),
    ('extreme_netiron', 'extreme_netiron'),
    ('extreme_nos', 'extreme_nos'),
    ('extreme_slx', 'extreme_slx'),
    ('extreme_vdx', 'extreme_vdx'),
    ('extreme_vsp', 'extreme_vsp'),
    ('extreme_wing', 'extreme_wing'),
    ('f5_linux', 'f5_linux'),
    ('f5_ltm', 'f5_ltm'),
    ('f5_tmsh', 'f5_tmsh'),
    ('flexvnf', 'flexvnf'),
    ('fortinet', 'fortinet'),
    ('generic_termserver', 'generic_termserver'),
    ('hp_comware', 'hp_comware'),
    ('hp_procurve', 'hp_procurve'),
    ('huawei', 'huawei'),
    ('huawei_vrpv8', 'huawei_vrpv8'),
    ('ipinfusion_ocnos', 'ipinfusion_ocnos'),
    ('juniper', 'juniper'),
    ('juniper_junos', 'juniper_junos'),
    ('linux', 'linux'),
    ('mellanox', 'mellanox'),
    ('mikrotik_routeros', 'mikrotik_routeros'),
    ('mikrotik_switchos', 'mikrotik_switchos'),
    ('mrv_lx', 'mrv_lx'),
    ('mrv_optiswitch', 'mrv_optiswitch'),
    ('netapp_cdot', 'netapp_cdot'),
    ('netscaler', 'netscaler'),
    ('oneaccess_oneos', 'oneaccess_oneos'),
    ('ovs_linux', 'ovs_linux'),
    ('paloalto_panos', 'paloalto_panos'),
    ('pluribus', 'pluribus'),
    ('quanta_mesh', 'quanta_mesh'),
    ('rad_etx', 'rad_etx'),
    ('ruckus_fastiron', 'ruckus_fastiron'),
    ('ubiquiti_edge', 'ubiquiti_edge'),
    ('ubiquiti_edgeswitch', 'ubiquiti_edgeswitch'),
    ('vyatta_vyos', 'vyatta_vyos'),
    ('vyos', 'vyos'),
)

"""
the vendors supported by our Napalm libraries.
Note: if you add a vendor here, you will also need to add the proper commands
to the napalm_commands dictionary in napalm/commands.py
"""
NAPALM_DEVICE_TYPES = (
    ('', 'None'),
    ('eos', 'Arista EOS'),
    ('aoscx', 'Aruba AOS-CX'),
    ('ios', 'Cisco IOS'),
    ('iosxr', 'Cisco IOS-XR'),
    ('nxos_ssh', 'Cisco NX-OS SSH'),
    ('dellos10', 'Dell OS10'),
    ('procurve', 'HP Procurve'),
    ('junos', 'Juniper JunOS'),
)
