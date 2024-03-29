# Generated by hand!

from django.db import migrations

from counters.models import Counter
from counters.constants import COUNTER_VLAN_MANAGE


def add_new_counters(apps, schema_editor):
    # add a few default counters to live throughout the app lifetime.
    c = Counter()
    c.name = COUNTER_VLAN_MANAGE
    c.description = "Number of VLAN edits on devices"
    c.save()


def remove_counters(apps, schema_editor):
    # and remove them if you want to migrate backwards
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('counters', '0001_initial'),
    ]

    operations = [migrations.RunPython(add_new_counters, remove_counters)]
