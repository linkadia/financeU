from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("markets", "0001_initial"),
    ]

    operations = [
        migrations.DeleteModel(name="Signal"),
        migrations.DeleteModel(name="MarketAsset"),
    ]
