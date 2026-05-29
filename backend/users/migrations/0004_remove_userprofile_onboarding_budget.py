from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_userprofile_onboarding"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="userprofile",
            name="onboarding_budget",
        ),
    ]
