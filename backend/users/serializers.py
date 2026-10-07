import re

from django.contrib.auth.hashers import check_password, make_password
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import serializers

from .models import SubscriptionEntitlement, UserProfile
from .msisdn import FINGERPRINT_PREFIX, fingerprint_from_msisdn, normalize_polish_msisdn

class UserProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, required=False)
    signup_token = serializers.CharField(write_only=True, required=False, allow_blank=True)
    msisdn = serializers.CharField(write_only=True, required=False, allow_blank=True)

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
            "msisdn",
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

    def validate_msisdn(self, value):
        if not value:
            return value
        try:
            return normalize_polish_msisdn(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate(self, attrs):
        if self.instance is None:
            if not attrs.get("signup_token") and not attrs.get("msisdn"):
                raise serializers.ValidationError(
                    {"error": "signup_proof_required"}
                )
            if attrs.get("signup_token") and attrs.get("msisdn"):
                raise serializers.ValidationError(
                    {"error": "signup_proof_conflict"}
                )
        elif "signup_token" in attrs or "msisdn" in attrs:
            raise serializers.ValidationError(
                {"detail": "Signup credentials cannot be changed on a profile."}
            )
        return attrs

    @staticmethod
    def subscription_error():
        return serializers.ValidationError(
            {
                "detail": "No eligible subscription is available for this registration.",
                "error": "subscription_not_eligible",
            }
        )

    def create(self, validated_data):
        if "password" not in validated_data:
            raise serializers.ValidationError({"password": "Password is required."})
        signup_token = validated_data.pop("signup_token", "")
        msisdn = validated_data.pop("msisdn", "")
        password = validated_data.pop("password")

        try:
            with transaction.atomic():
                if signup_token:
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
                else:
                    fingerprint = fingerprint_from_msisdn(msisdn)
                    if UserProfile.objects.filter(msisdn_hash=fingerprint).exists():
                        raise self.subscription_error()
                    if SubscriptionEntitlement.objects.filter(
                        msisdn_hash=fingerprint,
                        registered_at__isnull=False,
                    ).exists():
                        raise self.subscription_error()
                    candidates = list(
                        SubscriptionEntitlement.objects.select_for_update()
                        .filter(
                            msisdn_hash=fingerprint,
                            user__isnull=True,
                            registered_at__isnull=True,
                            payment_confirmed_at__isnull=False,
                            access_until__gt=timezone.localdate(),
                            status__in=(
                                SubscriptionEntitlement.STATUS_PENDING_REGISTRATION,
                                SubscriptionEntitlement.STATUS_CANCELLED,
                            ),
                        )
                        .order_by("id")[:2]
                    )
                    eligible = [
                        candidate
                        for candidate in candidates
                        if candidate.can_be_used_for_mobile_signup()
                    ]
                    if len(eligible) != 1:
                        raise self.subscription_error()
                    entitlement = eligible[0]

                fingerprint = (
                    entitlement.msisdn_hash
                    if entitlement.msisdn_hash.startswith(FINGERPRINT_PREFIX)
                    else None
                )
                if fingerprint:
                    if UserProfile.objects.filter(msisdn_hash=fingerprint).exists():
                        raise self.subscription_error()
                    if SubscriptionEntitlement.objects.filter(
                        msisdn_hash=fingerprint,
                        registered_at__isnull=False,
                    ).exists():
                        raise self.subscription_error()
                    validated_data["msisdn_hash"] = fingerprint

                if not validated_data.get("display_name"):
                    validated_data["display_name"] = validated_data.get("username", "")
                validated_data["password_hash"] = make_password(password)
                validated_data["integrator_tid"] = entitlement.tid
                validated_data["integrator_sid"] = entitlement.sid
                validated_data["estado"] = (
                    UserProfile.STATUS_INACTIVE
                    if entitlement.status == SubscriptionEntitlement.STATUS_CANCELLED
                    else UserProfile.STATUS_ACTIVE
                )
                if entitlement.access_until:
                    validated_data["fecha_renovacion"] = entitlement.access_until

                profile = super().create(validated_data)
                entitlement.mark_registered(profile)
                return profile
        except IntegrityError as exc:
            raise self.subscription_error() from exc


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

    def validate_customer(self, value):
        msisdn_hash = value.get("msisdn_hash")
        if "msisdn_hash" in value and (
            not isinstance(msisdn_hash, str)
            or not re.fullmatch(r"[0-9a-f]{64}", msisdn_hash)
        ):
            raise serializers.ValidationError(
                "customer.msisdn_hash must be a lowercase SHA-256 hex digest."
            )
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
