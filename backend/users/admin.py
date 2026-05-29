from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    exclude = ("public_id", "operator_token")
    list_display = ("username", "email", "estado", "fecha_renovacion", "created_at")
    list_filter = ("estado", "fecha_renovacion", "created_at")
    search_fields = ("username", "email", "display_name")
