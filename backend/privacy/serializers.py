from rest_framework import serializers

from .models import CookieConsentRecord


class CookieConsentRecordSerializer(serializers.ModelSerializer):
    # Uniqueness is handled atomically by the view so retries can return the existing record.
    event_id = serializers.UUIDField()

    class Meta:
        model = CookieConsentRecord
        fields = [
            "event_id",
            "consent_id",
            "action",
            "analytics",
            "marketing",
            "policy_version",
            "language",
            "page_path",
            "client_recorded_at",
            "created_at",
        ]
        read_only_fields = ["created_at"]
        extra_kwargs = {
            "language": {"default": ""},
            "page_path": {"default": ""},
            "client_recorded_at": {"default": None},
        }

    def validate_page_path(self, value):
        # Query strings can carry signup tokens, so only the path is stored.
        path = value.split("?", 1)[0].split("#", 1)[0]
        if path and (not path.startswith("/") or path.startswith("//") or "\\" in path):
            raise serializers.ValidationError("Must be a site-relative path.")
        return path

    def validate(self, attrs):
        if attrs["marketing"]:
            raise serializers.ValidationError({"marketing": "Marketing is not currently used."})
        expected = {
            CookieConsentRecord.ACTION_ACCEPT_ALL: True,
            CookieConsentRecord.ACTION_REJECT_ALL: False,
        }.get(attrs["action"])
        if expected is not None and attrs["analytics"] is not expected:
            raise serializers.ValidationError(
                {"action": "Action does not match the selected categories."}
            )
        return attrs
