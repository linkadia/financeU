from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_userprofile_account_fields_seed_demo"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="onboarding_budget",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="onboarding_completed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="onboarding_goal",
            field=models.CharField(blank=True, max_length=60),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="onboarding_interests",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="onboarding_risk_profile",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="selected_agent",
            field=models.CharField(blank=True, max_length=40),
        ),
    ]
