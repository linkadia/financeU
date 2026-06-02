from django.contrib import admin

from .models import FinancialDataRun, FinancialProduct, FinancialProductSnapshot


@admin.register(FinancialProduct)
class FinancialProductAdmin(admin.ModelAdmin):
    list_display = (
        "symbol",
        "name_en",
        "name_pl",
        "category",
        "subcategory",
        "unit",
        "display_order",
        "is_active",
        "is_featured",
    )
    list_filter = ("category", "subcategory", "is_active", "is_featured")
    search_fields = ("symbol", "name_en", "name_pl")
    ordering = ("display_order",)


@admin.register(FinancialProductSnapshot)
class FinancialProductSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "product_category",
        "current_value",
        "previous_value",
        "change_percent",
        "effective_at_raw",
        "source_name",
        "validation_status",
        "created_at",
    )
    list_filter = (
        "product__category",
        "product__subcategory",
        "validation_status",
        "source_name",
        "created_at",
    )
    search_fields = ("product__symbol", "product__name_en", "product__name_pl", "source_name")
    readonly_fields = (
        "change_absolute",
        "change_percent",
        "effective_at_raw",
        "previous_reference_at_raw",
        "effective_date",
        "previous_reference_date",
        "effective_datetime",
        "previous_reference_datetime",
        "raw_row",
        "validation_errors",
        "created_at",
    )

    @admin.display(description="Category")
    def product_category(self, obj):
        return obj.product.category


@admin.register(FinancialDataRun)
class FinancialDataRunAdmin(admin.ModelAdmin):
    list_display = (
        "provider",
        "status",
        "requested_at",
        "items_received",
        "items_imported",
        "items_updated",
        "items_failed",
        "created_at",
    )
    list_filter = ("provider", "status", "created_at")
    readonly_fields = ("raw_response", "errors", "created_at")
