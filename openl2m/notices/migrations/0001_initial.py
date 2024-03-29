# Generated by Django 4.1.5 on 2023-02-21 19:22

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Notice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=True)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('title', models.CharField(max_length=100, unique=True, verbose_name='name')),
                (
                    'priority',
                    models.PositiveSmallIntegerField(
                        choices=[[10, 'DEBUG'], [20, 'Information'], [25, 'Success'], [30, 'Warning'], [40, 'Error']],
                        default=20,
                        help_text='Proirity of this notice, as defined by Message Levels',
                        verbose_name='Notice priority',
                    ),
                ),
                ('content', models.TextField(blank=True, verbose_name='content')),
            ],
            options={
                'ordering': ['start_time'],
            },
        ),
    ]
