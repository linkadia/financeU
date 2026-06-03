from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0004_remove_legacy_content_models"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="newsarticle",
            index=models.Index(fields=["status", "-published_at"], name="content_new_status_04d6dd_idx"),
        ),
        migrations.AddIndex(
            model_name="newsarticle",
            index=models.Index(fields=["status", "news_type", "-published_at"], name="content_new_status_6814d5_idx"),
        ),
    ]
