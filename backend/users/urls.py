from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserProfileViewSet, login

router = DefaultRouter()
router.register("profiles", UserProfileViewSet, basename="profiles")

urlpatterns = [
    path("login/", login, name="user-login"),
    path("", include(router.urls)),
]
