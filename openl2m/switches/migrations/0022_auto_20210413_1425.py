# Generated by Django 3.1.7 on 2021-04-13 21:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('switches', '0021_auto_20210315_1705'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='action',
            field=models.PositiveSmallIntegerField(
                choices=[
                    [0, 'View Switch Groups'],
                    [1, 'View Switch'],
                    [2, 'View Interface'],
                    [3, 'View PoE'],
                    [4, 'View Vlans'],
                    [5, 'View LLDP'],
                    [6, 'Viewing All Logs'],
                    [7, 'Viewing Site Statistics'],
                    [8, 'Viewing Tasks'],
                    [9, 'Viewing Task Details'],
                    [10, 'Searching for Switch Name'],
                    [100, 'Reloading Switch Data'],
                    [101, 'New System ObjectID Found'],
                    [102, 'New System Name Found'],
                    [90, 'Login'],
                    [91, 'Logout'],
                    [92, 'Inactivity Logout'],
                    [93, 'Login Failed'],
                    [94, 'LDAP Login'],
                    [103, 'Interface Disable'],
                    [104, 'Interface Enable'],
                    [105, 'Interface Toggle'],
                    [106, 'Interface PoE Disable'],
                    [107, 'Interface PoE Enable'],
                    [108, 'Interface PoE Toggle'],
                    [109, 'Interface PVID Vlan Change'],
                    [110, 'Interface Description Change'],
                    [111, 'Saving Configuration'],
                    [112, 'Execute Command'],
                    [113, 'Port PoE Fault'],
                    [114, 'LDAP New SwitchGroup'],
                    [115, 'Bulk Edit'],
                    [116, 'Bulk Edit Task Submit'],
                    [117, 'Bulk Edit Task Started'],
                    [118, 'Bulk Edit Task Ended OK'],
                    [119, 'Bulk Edit Task Ended With Errors'],
                    [120, 'Task Deleted'],
                    [121, 'Task Terminated'],
                    [122, 'Email Sent'],
                    [256, 'Undefined Vlan'],
                    [257, 'Vlan Name Mismatch'],
                    [258, 'SNMP Error'],
                    [259, 'LDAP User->SwitchGroup Error'],
                    [260, 'LDAP SwitchGroup Error'],
                    [261, 'Bulk Edit Job Start Error'],
                    [262, 'Email Error'],
                    [301, 'Napalm Driver'],
                    [302, 'Napalm Open'],
                    [303, 'Napalm Facts'],
                    [304, 'Napalm Interfaces'],
                    [305, 'Napalm Vlans'],
                    [306, 'Napalm Interface IP'],
                    [307, 'Napalm MAC'],
                    [308, 'Napalm ARP'],
                    [309, 'Napalm LLDP'],
                ],
                default=1,
                verbose_name='Activity or Action to log',
            ),
        ),
        migrations.AlterField(
            model_name='switch',
            name='napalm_device_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('', 'None'),
                    ('eos', 'Arista EOS'),
                    ('aoscx', 'Aruba AOS-CX'),
                    ('ios', 'Cisco IOS'),
                    ('iosxr', 'Cisco IOS-XR'),
                    ('nxos_ssh', 'Cisco NX-OS SSH'),
                    ('dellos10', 'Dell OS10'),
                    ('procurve', 'HP Procurve'),
                    ('junos', 'Juniper JunOS'),
                ],
                default='',
                help_text='The device type to use if Napalm connector is used.',
                max_length=64,
                null=True,
                verbose_name='Napalm Device Type',
            ),
        ),
    ]
