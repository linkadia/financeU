from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class NewsArticle(models.Model):
    class Difficulty(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    class NewsType(models.TextChoices):
        CRYPTO = "crypto", "Crypto"
        STOCK_MARKET = "stock_market", "Stock market"
        FOREX = "forex", "Forex"
        INVESTING_BASICS = "investing_basics", "Investing basics"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    source_url = models.URLField(max_length=500, null=True, blank=True)
    source_name = models.CharField(max_length=120)
    headline = models.CharField(max_length=255)
    subtitle = models.TextField(null=True, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    image_alt = models.CharField(max_length=255, null=True, blank=True)
    image_source = models.CharField(max_length=255, null=True, blank=True)
    short_summary = models.TextField()
    advanced_summary = models.TextField()
    beginner_summary = models.TextField()
    translations = models.JSONField(default=dict, blank=True)
    difficulty = models.CharField(
        max_length=20,
        choices=Difficulty.choices,
        db_index=True,
    )
    news_type = models.CharField(
        max_length=30,
        choices=NewsType.choices,
        db_index=True,
    )
    importance_score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        db_index=True,
    )
    published_at = models.DateTimeField(db_index=True)
    processed_at = models.DateTimeField()
    original_language = models.CharField(max_length=10)
    original_content = models.TextField(null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    mentioned_assets = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    external_id = models.CharField(max_length=255, null=True, blank=True)
    content_hash = models.CharField(max_length=64, unique=True)
    ai_metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at"]
        indexes = [
            models.Index(fields=["news_type", "difficulty", "status"]),
            models.Index(fields=["status", "-published_at"], name="content_new_status_04d6dd_idx"),
            models.Index(fields=["status", "news_type", "-published_at"], name="content_new_status_6814d5_idx"),
        ]

    def __str__(self):
        return f"{self.headline} ({self.source_name})"
