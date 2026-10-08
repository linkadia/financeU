from django.contrib import admin
from .models import IntegrationEvent, SubscriptionEntitlement, UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    exclude = ("public_id", "operator_token")
    list_display = (
        "username",
        "email",
        "has_mobile_fingerprint",
        "estado",
        "fecha_renovacion",
        "integrator_tid",
        "integrator_sid",
        "created_at",
    )
    list_filter = ("estado", "fecha_renovacion", "created_at")
    search_fields = (
        "username",
        "email",
        "display_name",
        "integrator_tid",
        "integrator_sid",
    )
    readonly_fields = ("msisdn_hash",)

    @admin.display(boolean=True, description="Móvil asociado")
    def has_mobile_fingerprint(self, obj):
        return bool(obj.msisdn_hash)


@admin.register(SubscriptionEntitlement)
class SubscriptionEntitlementAdmin(admin.ModelAdmin):
    list_display = (
        "tid",
        "sid",
        "has_mobile_fingerprint",
        "status",
        "user",
        "access_until",
        "cancelled_at",
        "last_event_id",
        "updated_at",
    )
    list_filter = ("status", "access_until", "cancelled_at", "created_at")
    search_fields = ("tid", "sid", "external_user_id", "msisdn_hash", "last_event_id")
    readonly_fields = (
        "public_id",
        "msisdn_hash",
        "signup_token_hash",
        "signup_token_created_at",
        "created_at",
        "updated_at",
    )

    @admin.display(boolean=True, description="Móvil recibido")
    def has_mobile_fingerprint(self, obj):
        return bool(obj.msisdn_hash)


@admin.register(IntegrationEvent)
class IntegrationEventAdmin(admin.ModelAdmin):
    list_display = (
        "event_id",
        "event_type",
        "action",
        "tid",
        "sid",
        "status",
        "processed_at",
    )
    list_filter = ("event_type", "status", "action", "processed_at")
    search_fields = ("event_id", "tid", "sid", "operator", "integrator", "service")
    readonly_fields = ("processed_at", "raw_payload")
