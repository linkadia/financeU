from django.db import migrations, models


def copy_existing_text_to_translations(apps, schema_editor):
    NewsArticle = apps.get_model("content", "NewsArticle")

    for article in NewsArticle.objects.all().iterator():
        fallback = {
            "headline": article.headline,
            "subtitle": article.subtitle or "",
            "short_summary": article.short_summary,
            "beginner_summary": article.beginner_summary,
            "advanced_summary": article.advanced_summary,
        }
        article.translations = {
            "en": fallback,
            "pl": fallback,
        }
        article.save(update_fields=["translations"])


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0002_newsarticle"),
    ]

    operations = [
        migrations.AddField(
            model_name="newsarticle",
            name="translations",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.RunPython(copy_existing_text_to_translations, migrations.RunPython.noop),
    ]
