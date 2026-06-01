from rest_framework import serializers
from django.contrib.auth.hashers import check_password, make_password
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, required=False)

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
        password = validated_data.pop("password")
        if not validated_data.get("display_name"):
            validated_data["display_name"] = validated_data.get("username", "")
        validated_data["password_hash"] = make_password(password)
        return super().create(validated_data)


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
