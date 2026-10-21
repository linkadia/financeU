# Initial consent history schema.

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CookieConsentRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_id', models.UUIDField(unique=True)),
                ('consent_id', models.UUIDField(db_index=True)),
                ('action', models.CharField(choices=[('accept_all', 'Aceptar todo'), ('reject_all', 'Rechazar todo'), ('custom', 'Preferencias guardadas')], max_length=20)),
                ('analytics', models.BooleanField()),
                ('marketing', models.BooleanField()),
                ('policy_version', models.CharField(max_length=20)),
                ('language', models.CharField(blank=True, max_length=10)),
                ('page_path', models.CharField(blank=True, max_length=255)),
                ('client_recorded_at', models.DateTimeField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.CharField(blank=True, max_length=512)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'verbose_name': 'Registro de consentimiento de cookies',
                'verbose_name_plural': 'Registros de consentimiento de cookies',
                'ordering': ['-created_at', '-id'],
            },
        ),
    ]
