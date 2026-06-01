from django.contrib.auth.hashers import check_password
from django.db.models import Q
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
                {"detail": "Username or email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = UserProfile.objects.filter(
            Q(username__iexact=identifier)
            | Q(email__iexact=identifier)
        ).first()

        if not profile or not check_password(password, profile.password_hash):
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not profile.can_access_platform():
            return Response(
                {
                    "detail": (
                        "Tu suscripcion esta inactiva. Para acceder de nuevo, "
                        "renueva la suscripcion mensual."
                    ),
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
