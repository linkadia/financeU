from django.contrib import admin
from .models import Article, Course, Lesson, NewsArticle

admin.site.register(Article)
admin.site.register(Course)
admin.site.register(Lesson)


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = (
        "headline",
        "source_name",
        "news_type",
        "difficulty",
        "importance_score",
        "status",
        "image_url",
        "published_at",
    )
    list_filter = (
        "news_type",
        "difficulty",
        "status",
        "source_name",
        ("image_url", admin.EmptyFieldListFilter),
        "published_at",
    )
    search_fields = (
        "headline",
        "source_name",
        "image_url",
        "image_alt",
        "image_source",
        "tags",
        "mentioned_assets",
    )
