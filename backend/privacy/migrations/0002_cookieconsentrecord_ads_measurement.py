from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("privacy", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="cookieconsentrecord",
            name="ads_measurement",
            field=models.BooleanField(default=False, verbose_name="Medición publicitaria"),
        ),
    ]
