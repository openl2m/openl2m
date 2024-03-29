# Generated by Django 3.2.7 on 2021-10-01 21:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('switches', '0027_alter_switch_connector_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='commandtemplate',
            name='list5_description',
            field=models.CharField(
                blank=True,
                help_text='Command template pick list 5 description.',
                max_length=64,
                verbose_name='Description',
            ),
        ),
        migrations.AddField(
            model_name='commandtemplate',
            name='list5_name',
            field=models.CharField(
                blank=True, help_text='Command template pick list 5 name.', max_length=64, verbose_name='Name'
            ),
        ),
        migrations.AddField(
            model_name='commandtemplate',
            name='list5_values',
            field=models.CharField(
                blank=True,
                help_text='Command template pick list 5 comma-separated values.',
                max_length=100,
                verbose_name='Values',
            ),
        ),
        migrations.AlterField(
            model_name='commandtemplate',
            name='template',
            field=models.CharField(
                help_text='The command template. Use {{field[1-8]}} or {{list[1-5]}} as needed.',
                max_length=64,
                verbose_name='Command Template',
            ),
        ),
    ]
