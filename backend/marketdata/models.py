from django.db import models
from django.db.models import Q


class FinancialProduct(models.Model):
    class Category(models.TextChoices):
        CRYPTO = "CRYPTO", "Crypto"
        INDEX = "INDEX", "Index"
        FOREX = "FOREX", "Forex"
        GENERAL = "GENERAL", "General"

    class Subcategory(models.TextChoices):
        COIN = "COIN", "Coin"
        STOCK_INDEX = "STOCK_INDEX", "Stock index"
        ETF = "ETF", "ETF"
        FX_PAIR = "FX_PAIR", "FX pair"
        METAL = "METAL", "Metal"
        COMMODITY = "COMMODITY", "Commodity"
        MACRO = "MACRO", "Macro"
        RATE = "RATE", "Rate"
        GDP = "GDP", "GDP"
        INFLATION = "INFLATION", "Inflation"
        UNEMPLOYMENT = "UNEMPLOYMENT", "Unemployment"
        HOUSING = "HOUSING", "Housing"
        BOND = "BOND", "Bond"
        RISK_PREMIUM = "RISK_PREMIUM", "Risk premium"
        OTHER = "OTHER", "Other"

    class UpdateFrequency(models.TextChoices):
        DAILY = "DAILY", "Daily"
        WEEKLY = "WEEKLY", "Weekly"
        MONTHLY = "MONTHLY", "Monthly"
        QUARTERLY = "QUARTERLY", "Quarterly"
        EVENT_BASED = "EVENT_BASED", "Event based"
        UNKNOWN = "UNKNOWN", "Unknown"

    class DataGranularity(models.TextChoices):
        REALTIME = "REALTIME", "Realtime"
        DAILY_CLOSE = "DAILY_CLOSE", "Daily close"
        MONTHLY = "MONTHLY", "Monthly"
        QUARTERLY = "QUARTERLY", "Quarterly"
        EVENT = "EVENT", "Event"
        UNKNOWN = "UNKNOWN", "Unknown"

    symbol = models.CharField(max_length=40, unique=True, db_index=True)
    name_en = models.CharField(max_length=160)
    name_pl = models.CharField(max_length=160)
    slug = models.SlugField(max_length=80, unique=True)
    category = models.CharField(max_length=20, choices=Category.choices, db_index=True)
    subcategory = models.CharField(max_length=30, choices=Subcategory.choices, db_index=True)
    unit = models.CharField(max_length=40)
    unit_label_en = models.CharField(max_length=120, blank=True)
    unit_label_pl = models.CharField(max_length=120, blank=True)
    description_en = models.TextField(blank=True)
    description_pl = models.TextField(blank=True)
    default_detail_en = models.CharField(max_length=160, blank=True)
    default_detail_pl = models.CharField(max_length=160, blank=True)
    update_frequency = models.CharField(
        max_length=20,
        choices=UpdateFrequency.choices,
        default=UpdateFrequency.UNKNOWN,
    )
    data_granularity = models.CharField(
        max_length=20,
        choices=DataGranularity.choices,
        default=DataGranularity.UNKNOWN,
    )
    display_order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "symbol"]
        indexes = [
            models.Index(fields=["category", "subcategory"]),
            models.Index(fields=["is_active", "is_featured", "display_order"]),
        ]

    def __str__(self):
        return f"{self.symbol} - {self.name_en}"


class FinancialDataRun(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        PARTIAL_SUCCESS = "PARTIAL_SUCCESS", "Partial success"
        FAILED = "FAILED", "Failed"

    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    provider = models.CharField(max_length=40, default="gemini")
    requested_at = models.DateTimeField(null=True, blank=True)
    items_expected = models.PositiveIntegerField(default=0)
    items_received = models.PositiveIntegerField(default=0)
    items_imported = models.PositiveIntegerField(default=0)
    items_updated = models.PositiveIntegerField(default=0)
    items_skipped = models.PositiveIntegerField(default=0)
    items_failed = models.PositiveIntegerField(default=0)
    raw_response = models.JSONField(default=dict, blank=True)
    errors = models.JSONField(default=list, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.provider} {self.status} {self.created_at:%Y-%m-%d %H:%M:%S}"


class FinancialProductSnapshot(models.Model):
    class ValidationStatus(models.TextChoices):
        VALID = "VALID", "Valid"
        PARTIAL = "PARTIAL", "Partial"
        INVALID = "INVALID", "Invalid"

    product = models.ForeignKey(
        FinancialProduct,
        related_name="snapshots",
        on_delete=models.CASCADE,
    )
    run = models.ForeignKey(
        FinancialDataRun,
        related_name="snapshots",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    current_value = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)
    previous_value = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)
    change_absolute = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)
    change_percent = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True)
    effective_at_raw = models.CharField(max_length=80, null=True, blank=True)
    previous_reference_at_raw = models.CharField(max_length=80, null=True, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    previous_reference_date = models.DateField(null=True, blank=True)
    effective_datetime = models.DateTimeField(null=True, blank=True)
    previous_reference_datetime = models.DateTimeField(null=True, blank=True)
    source_name = models.CharField(max_length=160, null=True, blank=True)
    source_url = models.URLField(max_length=500, null=True, blank=True)
    quality_note = models.TextField(null=True, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    raw_row = models.JSONField(default=list, blank=True)
    validation_status = models.CharField(
        max_length=20,
        choices=ValidationStatus.choices,
        default=ValidationStatus.VALID,
        db_index=True,
    )
    validation_errors = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["product__display_order", "-created_at"]
        indexes = [
            models.Index(fields=["product", "-created_at"]),
            models.Index(
                fields=["product", "validation_status", "-effective_date", "-effective_datetime", "-created_at"],
                name="market_snap_latest_idx",
            ),
            models.Index(
                fields=["product", "-effective_date", "-created_at"],
                name="market_snap_history_idx",
            ),
            models.Index(fields=["effective_date"]),
            models.Index(fields=["validation_status", "created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "effective_at_raw"],
                condition=Q(effective_at_raw__isnull=False),
                name="unique_snapshot_product_effective_raw",
            ),
        ]

    def __str__(self):
        return f"{self.product.symbol} {self.current_value} ({self.effective_at_raw})"
