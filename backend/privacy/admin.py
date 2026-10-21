from django.contrib import admin

from .models import CookieConsentRecord


@admin.register(CookieConsentRecord)
class CookieConsentRecordAdmin(admin.ModelAdmin):
    list_display = (
        "consent_id",
        "action",
        "analytics",
        "marketing",
        "policy_version",
        "language",
        "created_at",
    )
    list_filter = ("action", "analytics", "marketing", "policy_version", "created_at")
    search_fields = ("consent_id", "event_id")
    date_hierarchy = "created_at"
    readonly_fields = tuple(field.name for field in CookieConsentRecord._meta.fields)
    fieldsets = (
        ("Decisión", {"fields": ("consent_id", "event_id", "action", "analytics", "marketing", "policy_version")}),
        ("Contexto", {"fields": ("language", "page_path", "client_recorded_at", "created_at", "ip_address", "user_agent")}),
    )

    # Records are evidence: they can be viewed (and purged), never created or edited by hand.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
