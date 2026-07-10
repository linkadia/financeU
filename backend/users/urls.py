from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IntegrationSubscriptionEventView,
    LoginView,
    PasswordResetRequestView,
    SignupTokenValidationView,
    UserProfileViewSet,
)

router = DefaultRouter()
router.register("profiles", UserProfileViewSet, basename="profiles")

urlpatterns = [
    path(
        "integration/subscription-events/",
        IntegrationSubscriptionEventView.as_view(),
        name="integration-subscription-events",
    ),
    path(
        "signup-token/validate/",
        SignupTokenValidationView.as_view(),
        name="signup-token-validate",
    ),
    path("login/", LoginView.as_view(), name="user-login"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="user-password-reset"),
    path("", include(router.urls)),
]
