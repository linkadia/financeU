from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0003_newsarticle_translations"),
    ]

    operations = [
        migrations.DeleteModel(name="Article"),
        migrations.DeleteModel(name="Lesson"),
        migrations.DeleteModel(name="Course"),
    ]
