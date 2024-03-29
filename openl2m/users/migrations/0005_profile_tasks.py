# Generated by Django 2.2.8 on 2020-01-16 00:10

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0004_profile_edit_if_descr'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='tasks',
            field=models.BooleanField(
                default=False,
                help_text='If Tasks is set, this user can schedule change tasks on switches.',
                verbose_name='Allow tasks to schedule changes',
            ),
        ),
    ]
