from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginView, PasswordResetRequestView, UserProfileViewSet

router = DefaultRouter()
router.register("profiles", UserProfileViewSet, basename="profiles")

urlpatterns = [
    path("login/", LoginView.as_view(), name="user-login"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="user-password-reset"),
    path("", include(router.urls)),
]
