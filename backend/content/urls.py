from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NewsArticleViewSet

router = DefaultRouter()
router.register("news", NewsArticleViewSet, basename="news")

urlpatterns = [
    path("", include(router.urls)),
]
