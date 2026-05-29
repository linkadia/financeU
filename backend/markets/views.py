from rest_framework import viewsets
from .models import MarketAsset, Signal
from .serializers import MarketAssetSerializer, SignalSerializer

class MarketAssetViewSet(viewsets.ModelViewSet):
    queryset = MarketAsset.objects.all()
    serializer_class = MarketAssetSerializer


class SignalViewSet(viewsets.ModelViewSet):
    queryset = Signal.objects.all().order_by("-created_at")
    serializer_class = SignalSerializer
