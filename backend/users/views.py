from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db.models import Q
from django.utils.crypto import get_random_string
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from .models import UserProfile
from .serializers import UserProfileSerializer, UserSettingsSerializer
from .throttling import LoginUserIpThrottle

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle, ScopedRateThrottle]
    throttle_scope_by_action = {
        # The create action is the current registration endpoint.
        "create": "signup",
        # Settings includes profile edits and password changes, so it is tighter.
        "user_settings": "settings",
        "complete_onboarding": "onboarding",
    }

    def get_throttles(self):
        # A scoped throttle lets the SPA burst on normal profile reads while
        # keeping sensitive actions like signup and settings more conservative.
        self.throttle_scope = self.throttle_scope_by_action.get(self.action, "profiles")
        return super().get_throttles()

    @action(detail=True, methods=["get", "patch"], url_path="settings")
    def user_settings(self, request, pk=None):
        profile = self.get_object()

        if request.method == "GET":
            return Response(UserSettingsSerializer(profile).data)

        serializer = UserSettingsSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(UserSettingsSerializer(profile).data)

    @action(detail=True, methods=["post"], url_path="complete-onboarding")
    def complete_onboarding(self, request, pk=None):
        profile = self.get_object()
        interests = request.data.get("interests", [])
        risk_profile = request.data.get("risk_profile", "")
        goal = request.data.get("goal", "")
        selected_agent = request.data.get("selected_agent", "")

        if not isinstance(interests, list):
            return Response(
                {"detail": "Interests must be a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        missing_fields = [
            field
            for field, value in {
                "interests": interests,
                "risk_profile": risk_profile,
                "goal": goal,
                "selected_agent": selected_agent,
            }.items()
            if not value
        ]
        if missing_fields:
            return Response(
                {"detail": f"Missing onboarding fields: {', '.join(missing_fields)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile.onboarding_interests = interests
        profile.onboarding_risk_profile = risk_profile
        profile.onboarding_goal = goal
        profile.selected_agent = selected_agent
        profile.onboarding_completed = True
        profile.save(
            update_fields=[
                "onboarding_interests",
                "onboarding_risk_profile",
                "onboarding_goal",
                "selected_agent",
                "onboarding_completed",
            ]
        )

        return Response(UserProfileSerializer(profile).data)


class LoginView(APIView):
    throttle_classes = [ScopedRateThrottle, LoginUserIpThrottle]
    throttle_scope = "login"

    def post(self, request):
        identifier = (
            request.data.get("identifier")
            or request.data.get("username")
            or ""
        ).strip()
        password = request.data.get("password", "")

        if not identifier or not password:
            return Response(
                {
                    "detail": "Username or email and password are required.",
                    "error": "missing_login_fields",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = UserProfile.objects.filter(
            Q(username__iexact=identifier)
            | Q(email__iexact=identifier)
        ).first()

        if not profile or not check_password(password, profile.password_hash):
            return Response(
                {
                    "detail": "Invalid username or password.",
                    "error": "invalid_credentials",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not profile.can_access_platform():
            return Response(
                {
                    "detail": "Subscription is inactive.",
                    "error": "subscription_inactive",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if profile.refresh_renewal_date_if_active():
            profile.save(update_fields=["fecha_renovacion"])

        return Response(
            {
                "id": profile.id,
                "username": profile.username,
                "email": profile.email,
                "display_name": profile.display_name,
                "estado": profile.estado,
                "fecha_renovacion": profile.fecha_renovacion,
                "onboarding_completed": profile.onboarding_completed,
                "onboarding_interests": profile.onboarding_interests,
                "onboarding_risk_profile": profile.onboarding_risk_profile,
                "onboarding_goal": profile.onboarding_goal,
                "selected_agent": profile.selected_agent,
            }
        )


class PasswordResetRequestView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request):
        email = (request.data.get("email") or "").strip()

        if not email:
            return Response(
                {
                    "detail": "Email is required.",
                    "error": "missing_email",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = UserProfile.objects.filter(email__iexact=email).first()

        if not profile:
            return Response(
                {
                    "detail": "User does not exist.",
                    "error": "user_not_found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        temporary_password = get_random_string(
            14,
            allowed_chars="abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789",
        )
        if not settings.DEBUG:
            send_mail(
                "Your FinancU temporary password",
                (
                    "We received a password reset request for your FinancU account.\n\n"
                    f"Temporary password: {temporary_password}\n\n"
                    "Sign in with this temporary password and update it from your profile settings."
                ),
                settings.DEFAULT_FROM_EMAIL,
                [profile.email],
                fail_silently=False,
            )

        profile.password_hash = make_password(temporary_password)
        profile.save(update_fields=["password_hash"])

        payload = {
            "message": "Temporary password generated.",
        }
        if settings.DEBUG:
            payload["temporary_password"] = temporary_password

        return Response(payload)
