from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MarketAssetViewSet, SignalViewSet

router = DefaultRouter()
router.register("assets", MarketAssetViewSet, basename="assets")
router.register("signals", SignalViewSet, basename="signals")

urlpatterns = [
    path("", include(router.urls)),
]
