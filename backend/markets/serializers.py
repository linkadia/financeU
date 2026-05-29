from rest_framework import serializers
from .models import MarketAsset, Signal

class MarketAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketAsset
        fields = "__all__"


class SignalSerializer(serializers.ModelSerializer):
    asset_detail = MarketAssetSerializer(source="asset", read_only=True)

    class Meta:
        model = Signal
        fields = "__all__"
