from django.db import migrations, models
import django.db.models


class Migration(migrations.Migration):

    dependencies = [
        ("marketdata", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="financialdatarun",
            name="items_updated",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddConstraint(
            model_name="financialproductsnapshot",
            constraint=models.UniqueConstraint(
                condition=django.db.models.Q(("effective_at_raw__isnull", False)),
                fields=("product", "effective_at_raw"),
                name="unique_snapshot_product_effective_raw",
            ),
        ),
    ]
