from django.contrib.auth.hashers import check_password
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import UserProfile
from .serializers import UserProfileSerializer, UserSettingsSerializer

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

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


@api_view(["POST"])
def login(request):
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

    return Response(
        {
            "id": profile.id,
            "username": profile.username,
            "email": profile.email,
            "display_name": profile.display_name,
            "onboarding_completed": profile.onboarding_completed,
            "onboarding_interests": profile.onboarding_interests,
            "onboarding_risk_profile": profile.onboarding_risk_profile,
            "onboarding_goal": profile.onboarding_goal,
            "selected_agent": profile.selected_agent,
        }
    )
