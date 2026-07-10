from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils.dateparse import parse_date
from rest_framework import serializers

from .models import SubscriptionEntitlement, UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, required=False)
    signup_token = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "username",
            "email",
            "display_name",
            "estado",
            "fecha_renovacion",
            "onboarding_completed",
            "onboarding_interests",
            "onboarding_risk_profile",
            "onboarding_goal",
            "selected_agent",
            "password",
            "signup_token",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "estado",
            "fecha_renovacion",
            "onboarding_completed",
            "onboarding_interests",
            "onboarding_risk_profile",
            "onboarding_goal",
            "selected_agent",
        ]
        extra_kwargs = {
            "username": {"required": True, "allow_blank": False},
            "email": {"required": True},
        }

    def create(self, validated_data):
        if "password" not in validated_data:
            raise serializers.ValidationError({"password": "Password is required."})
        signup_token = validated_data.pop("signup_token", "")
        password = validated_data.pop("password")

        with transaction.atomic():
            entitlement = (
                SubscriptionEntitlement.objects.select_for_update()
                .filter(
                    signup_token_hash=SubscriptionEntitlement.hash_signup_token(
                        signup_token
                    )
                )
                .first()
            )

            if not entitlement or not entitlement.can_be_used_for_signup():
                raise serializers.ValidationError(
                    {
                        "signup_token": "Invalid or expired signup token.",
                        "error": "invalid_signup_token",
                    }
                )

            if not validated_data.get("display_name"):
                validated_data["display_name"] = validated_data.get("username", "")
            validated_data["password_hash"] = make_password(password)
            validated_data["integrator_tid"] = entitlement.tid
            validated_data["integrator_sid"] = entitlement.sid
            validated_data["estado"] = UserProfile.STATUS_ACTIVE
            if entitlement.access_until:
                validated_data["fecha_renovacion"] = entitlement.access_until

            profile = super().create(validated_data)
            entitlement.mark_registered(profile)
            return profile


class IntegrationSubscriptionEventSerializer(serializers.Serializer):
    event_id = serializers.CharField(max_length=128)
    event_type = serializers.ChoiceField(
        choices=["created", "renewed", "cancelled"]
    )
    occurred_at = serializers.DateTimeField()
    operator = serializers.CharField(max_length=80, required=False, allow_blank=True)
    integrator = serializers.CharField(max_length=80, required=False, allow_blank=True)
    service = serializers.CharField(max_length=80, required=False, allow_blank=True)
    tid = serializers.CharField(max_length=128)
    sid = serializers.CharField(max_length=128)
    subscription = serializers.DictField(required=False)
    customer = serializers.DictField(required=False)

    def validate_subscription(self, value):
        access_until = value.get("access_until")
        if access_until:
            parsed_access_until = parse_date(str(access_until))
            if not parsed_access_until:
                raise serializers.ValidationError(
                    "subscription.access_until must use YYYY-MM-DD format."
                )
            value["access_until"] = parsed_access_until
        return value


class UserSettingsSerializer(serializers.ModelSerializer):
    current_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    new_password = serializers.CharField(write_only=True, min_length=8, required=False, allow_blank=True)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "username",
            "email",
            "display_name",
            "estado",
            "fecha_renovacion",
            "onboarding_completed",
            "onboarding_interests",
            "onboarding_risk_profile",
            "onboarding_goal",
            "selected_agent",
            "current_password",
            "new_password",
        ]
        read_only_fields = ["id", "estado", "fecha_renovacion", "onboarding_completed"]

    def validate(self, attrs):
        current_password = attrs.pop("current_password", "")
        new_password = attrs.pop("new_password", "")

        if new_password:
            if not current_password:
                raise serializers.ValidationError(
                    {"current_password": "Current password is required to change your password."}
                )
            if not check_password(current_password, self.instance.password_hash):
                raise serializers.ValidationError(
                    {"current_password": "Current password is incorrect."}
                )
            attrs["password_hash"] = make_password(new_password)

        return attrs
