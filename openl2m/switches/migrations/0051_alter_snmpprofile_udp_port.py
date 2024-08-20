# Generated by Django 5.0.7 on 2024-08-02 23:18

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('switches', '0050_switch_command_count_switch_last_command_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='snmpprofile',
            name='udp_port',
            field=models.PositiveIntegerField(
                default=161,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(65535),
                ],
                verbose_name='SNMP Udp port',
            ),
        ),
    ]