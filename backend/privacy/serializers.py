from rest_framework import serializers

from .models import CookieConsentRecord


class CookieConsentRecordSerializer(serializers.ModelSerializer):
    # Uniqueness is handled atomically by the view so retries can return the existing record.
    event_id = serializers.UUIDField()
    # Optional at field level for queued 1.0 events; later versions require the field.
    ads_measurement = serializers.BooleanField(required=False)
    policy_version = serializers.ChoiceField(choices=("1.0", "1.1", "1.2"))

    class Meta:
        model = CookieConsentRecord
        fields = [
            "event_id",
            "consent_id",
            "action",
            "analytics",
            "ads_measurement",
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
            raise serializers.ValidationError({"marketing": "Advertising personalization is not used."})
        if attrs["policy_version"] == "1.0":
            if attrs.get("ads_measurement", False):
                raise serializers.ValidationError({"ads_measurement": "Policy 1.0 did not request advertising measurement consent."})
            attrs["ads_measurement"] = False
        elif "ads_measurement" not in attrs:
            raise serializers.ValidationError({"ads_measurement": "An explicit value is required for this policy version."})
        if attrs["policy_version"] == "1.2" and attrs["ads_measurement"]:
            raise serializers.ValidationError({"ads_measurement": "Advertising measurement is not used in this app."})
        expected = {
            CookieConsentRecord.ACTION_ACCEPT_ALL: True,
            CookieConsentRecord.ACTION_REJECT_ALL: False,
        }.get(attrs["action"])
        categories = [attrs["analytics"]]
        if attrs["policy_version"] == "1.1":
            categories.append(attrs["ads_measurement"])
        if expected is not None and any(value is not expected for value in categories):
            raise serializers.ValidationError(
                {"action": "Action does not match the selected categories."}
            )
        return attrs
