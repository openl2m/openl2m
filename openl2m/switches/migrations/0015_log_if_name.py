# Generated by Django 3.0.9 on 2020-08-25 23:46

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('switches', '0014_auto_20200710_1036'),
    ]

    operations = [
        migrations.AddField(
            model_name='log',
            name='if_name',
            field=models.CharField(blank=True, max_length=64, verbose_name='Interface name'),
        ),
    ]
