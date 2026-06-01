from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginView, UserProfileViewSet

router = DefaultRouter()
router.register("profiles", UserProfileViewSet, basename="profiles")

urlpatterns = [
    path("login/", LoginView.as_view(), name="user-login"),
    path("", include(router.urls)),
]
