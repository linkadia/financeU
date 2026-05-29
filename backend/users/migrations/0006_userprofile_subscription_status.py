from calendar import monthrange

from django.db import migrations, models
from django.utils import timezone

import users.models


def add_month(value):
    month = value.month + 1
    year = value.year
    if month > 12:
        month = 1
        year += 1
    day = min(value.day, monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def populate_renewal_dates(apps, schema_editor):
    UserProfile = apps.get_model("users", "UserProfile")
    for profile in UserProfile.objects.all():
        if profile.created_at:
            created_date = timezone.localtime(profile.created_at).date()
        else:
            created_date = timezone.localdate()
        profile.fecha_renovacion = add_month(created_date)
        profile.save(update_fields=["fecha_renovacion"])


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_userprofile_public_id_operator_token_remove_private_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="estado",
            field=models.CharField(
                choices=[("activo", "Activo"), ("inactivo", "Inactivo")],
                db_index=True,
                default="activo",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="fecha_renovacion",
            field=models.DateField(
                default=users.models.default_renewal_date,
                null=True,
            ),
        ),
        migrations.RunPython(populate_renewal_dates, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="userprofile",
            name="fecha_renovacion",
            field=models.DateField(default=users.models.default_renewal_date),
        ),
    ]
