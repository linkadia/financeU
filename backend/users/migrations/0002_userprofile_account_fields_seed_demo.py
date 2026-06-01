from django.contrib.auth.hashers import make_password
from django.db import migrations, models


def seed_demo_user(apps, schema_editor):
    UserProfile = apps.get_model("users", "UserProfile")
    profile = (
        UserProfile.objects.filter(username="Admin").first()
        or UserProfile.objects.filter(email="admin@finanu.local").first()
    )
    if profile is None:
        profile = UserProfile(email="admin@finanu.local")

    profile.username = "Admin"
    profile.display_name = "Admin"
    profile.phone = ""
    profile.birth_date = None
    profile.password_hash = make_password("admin1234")
    profile.save()


def remove_demo_user(apps, schema_editor):
    UserProfile = apps.get_model("users", "UserProfile")
    UserProfile.objects.filter(username="Admin", email="admin@finanu.local").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="birth_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="password_hash",
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="phone",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="username",
            field=models.CharField(blank=True, max_length=80, null=True, unique=True),
        ),
        migrations.RunPython(seed_demo_user, remove_demo_user),
    ]
