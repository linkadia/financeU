from django.db import models

class MarketAsset(models.Model):
    ASSET_TYPES = [
        ("CRYPTO", "Crypto"),
        ("FOREX", "Forex"),
        ("ETF", "ETF"),
        ("INDEX", "Index"),
    ]

    symbol = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=120)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)
    price = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    change_24h = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class Signal(models.Model):
    DIRECTIONS = [
        ("BUY", "Buy"),
        ("SELL", "Sell"),
        ("HOLD", "Hold"),
    ]

    asset = models.ForeignKey(MarketAsset, related_name="signals", on_delete=models.CASCADE)
    direction = models.CharField(max_length=10, choices=DIRECTIONS)
    rationale = models.TextField(blank=True)
    risk_level = models.CharField(max_length=30, default="Medium")
    confidence = models.PositiveIntegerField(default=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset.symbol} {self.direction}"
