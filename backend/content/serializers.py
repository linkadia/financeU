from rest_framework import serializers
from .models import NewsArticle


class NewsArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticle
        fields = "__all__"


class PublicNewsArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsArticle
        fields = [
            "id",
            "source_url",
            "source_name",
            "headline",
            "subtitle",
            "image_url",
            "image_alt",
            "short_summary",
            "advanced_summary",
            "beginner_summary",
            "translations",
            "difficulty",
            "news_type",
            "importance_score",
            "published_at",
            "original_language",
            "tags",
            "mentioned_assets",
        ]
