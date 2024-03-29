# Generated by Django 4.2.6 on 2023-10-31 22:31

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0012_alter_profile_last_ldap_dn'),
    ]

    operations = [
        migrations.CreateModel(
            name='Token',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('expires', models.DateTimeField(blank=True, null=True, verbose_name='expires')),
                ('last_used', models.DateTimeField(blank=True, null=True, verbose_name='last used')),
                (
                    'key',
                    models.CharField(
                        max_length=40,
                        unique=True,
                        validators=[django.core.validators.MinLengthValidator(40)],
                        verbose_name='key',
                    ),
                ),
                (
                    'write_enabled',
                    models.BooleanField(
                        default=True,
                        help_text='Permit create/update/delete operations using this key',
                        verbose_name='write enabled',
                    ),
                ),
                ('description', models.CharField(blank=True, max_length=200, verbose_name='description')),
                (
                    'allowed_ips',
                    models.CharField(
                        blank=True,
                        help_text='Allowed IPv4/IPv6 networks from where the token can be used. Leave blank for no restrictions. Ex: "10.1.1.0/24, 192.168.10.16/32, 2001:DB8:1::/64"',
                        max_length=200,
                        verbose_name='allowed IPs',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name='tokens', to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={
                'verbose_name': 'token',
                'verbose_name_plural': 'tokens',
            },
        ),
    ]
