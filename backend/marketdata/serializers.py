from rest_framework import serializers

from .models import FinancialProduct, FinancialProductSnapshot


class SnapshotSummarySerializer(serializers.ModelSerializer):
    effective_at = serializers.SerializerMethodField()

    class Meta:
        model = FinancialProductSnapshot
        fields = (
            "current_value",
            "previous_value",
            "change_absolute",
            "change_percent",
            "effective_at",
            "source_name",
            "validation_status",
        )

    def get_effective_at(self, obj):
        return obj.effective_at_raw or obj.effective_datetime or obj.effective_date


class ProductMarketSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    default_detail = serializers.SerializerMethodField()
    unit_label = serializers.SerializerMethodField()
    current_value = serializers.SerializerMethodField()
    previous_value = serializers.SerializerMethodField()
    change_absolute = serializers.SerializerMethodField()
    change_percent = serializers.SerializerMethodField()
    effective_at = serializers.SerializerMethodField()
    source_name = serializers.SerializerMethodField()
    validation_status = serializers.SerializerMethodField()

    class Meta:
        model = FinancialProduct
        fields = (
            "symbol",
            "slug",
            "name",
            "name_en",
            "name_pl",
            "category",
            "subcategory",
            "unit",
            "unit_label",
            "default_detail",
            "display_order",
            "is_featured",
            "current_value",
            "previous_value",
            "change_absolute",
            "change_percent",
            "effective_at",
            "source_name",
            "validation_status",
        )

    def get_name(self, obj):
        lang = self.context.get("lang", "en")
        return obj.name_pl if lang == "pl" else obj.name_en

    def get_default_detail(self, obj):
        lang = self.context.get("lang", "en")
        return obj.default_detail_pl if lang == "pl" else obj.default_detail_en

    def get_unit_label(self, obj):
        lang = self.context.get("lang", "en")
        label = obj.unit_label_pl if lang == "pl" else obj.unit_label_en
        return label or obj.unit

    def latest_snapshot(self, obj):
        if hasattr(obj, "_latest_snapshot_cache"):
            return obj._latest_snapshot_cache

        snapshot = obj.snapshots.order_by("-created_at").first()
        obj._latest_snapshot_cache = snapshot
        return snapshot

    def get_current_value(self, obj):
        snapshot = self.latest_snapshot(obj)
        return snapshot.current_value if snapshot else None

    def get_previous_value(self, obj):
        snapshot = self.latest_snapshot(obj)
        return snapshot.previous_value if snapshot else None

    def get_change_absolute(self, obj):
        snapshot = self.latest_snapshot(obj)
        return snapshot.change_absolute if snapshot else None

    def get_change_percent(self, obj):
        snapshot = self.latest_snapshot(obj)
        return snapshot.change_percent if snapshot else None

    def get_effective_at(self, obj):
        snapshot = self.latest_snapshot(obj)
        if not snapshot:
            return None
        return snapshot.effective_at_raw or snapshot.effective_datetime or snapshot.effective_date

    def get_source_name(self, obj):
        snapshot = self.latest_snapshot(obj)
        return snapshot.source_name if snapshot else None

    def get_validation_status(self, obj):
        snapshot = self.latest_snapshot(obj)
        return snapshot.validation_status if snapshot else None


class SnapshotHistorySerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source="product.symbol", read_only=True)
    name = serializers.SerializerMethodField()
    default_detail = serializers.SerializerMethodField()
    unit_label = serializers.SerializerMethodField()
    category = serializers.CharField(source="product.category", read_only=True)
    subcategory = serializers.CharField(source="product.subcategory", read_only=True)
    unit = serializers.CharField(source="product.unit", read_only=True)
    effective_at = serializers.SerializerMethodField()

    class Meta:
        model = FinancialProductSnapshot
        fields = (
            "symbol",
            "name",
            "category",
            "subcategory",
            "unit",
            "unit_label",
            "default_detail",
            "current_value",
            "previous_value",
            "change_absolute",
            "change_percent",
            "effective_at",
            "source_name",
            "validation_status",
            "created_at",
        )

    def get_name(self, obj):
        lang = self.context.get("lang", "en")
        return obj.product.name_pl if lang == "pl" else obj.product.name_en

    def get_default_detail(self, obj):
        lang = self.context.get("lang", "en")
        return obj.product.default_detail_pl if lang == "pl" else obj.product.default_detail_en

    def get_unit_label(self, obj):
        lang = self.context.get("lang", "en")
        label = obj.product.unit_label_pl if lang == "pl" else obj.product.unit_label_en
        return label or obj.product.unit

    def get_effective_at(self, obj):
        return obj.effective_at_raw or obj.effective_datetime or obj.effective_date


class LatestMarketSnapshotSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField(source="product.symbol", read_only=True)
    name = serializers.SerializerMethodField()
    category = serializers.CharField(source="product.category", read_only=True)
    subcategory = serializers.CharField(source="product.subcategory", read_only=True)
    unit = serializers.CharField(source="product.unit", read_only=True)
    unit_label = serializers.SerializerMethodField()
    default_detail = serializers.SerializerMethodField()
    direction = serializers.SerializerMethodField()
    display_order = serializers.IntegerField(source="product.display_order", read_only=True)

    class Meta:
        model = FinancialProductSnapshot
        fields = (
            "symbol",
            "name",
            "category",
            "subcategory",
            "unit",
            "unit_label",
            "default_detail",
            "current_value",
            "previous_value",
            "change_absolute",
            "change_percent",
            "direction",
            "effective_at_raw",
            "effective_date",
            "effective_datetime",
            "source_name",
            "validation_status",
            "display_order",
        )

    def get_name(self, obj):
        lang = self.context.get("lang", "en")
        return obj.product.name_pl if lang == "pl" else obj.product.name_en

    def get_unit_label(self, obj):
        lang = self.context.get("lang", "en")
        label = obj.product.unit_label_pl if lang == "pl" else obj.product.unit_label_en
        return label or obj.product.unit

    def get_default_detail(self, obj):
        lang = self.context.get("lang", "en")
        return obj.product.default_detail_pl if lang == "pl" else obj.product.default_detail_en

    def get_direction(self, obj):
        if obj.change_absolute is None:
            return "UNKNOWN"
        if obj.change_absolute > 0:
            return "UP"
        if obj.change_absolute < 0:
            return "DOWN"
        return "FLAT"
