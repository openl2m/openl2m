# Generated by Django 4.2.1 on 2023-06-05 23:50

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("switches", "0036_alter_log_action"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Task",
        ),
    ]
