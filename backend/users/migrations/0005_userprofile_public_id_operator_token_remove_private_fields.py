import uuid

from django.db import migrations, models


def populate_public_ids(apps, schema_editor):
    UserProfile = apps.get_model("users", "UserProfile")
    for profile in UserProfile.objects.filter(public_id__isnull=True):
        profile.public_id = uuid.uuid4()
        profile.save(update_fields=["public_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_remove_userprofile_onboarding_budget"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="public_id",
            field=models.UUIDField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="operator_token",
            field=models.CharField(blank=True, editable=False, max_length=255),
        ),
        migrations.RunPython(populate_public_ids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="userprofile",
            name="public_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.RemoveField(
            model_name="userprofile",
            name="birth_date",
        ),
        migrations.RemoveField(
            model_name="userprofile",
            name="phone",
        ),
    ]
