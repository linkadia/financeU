from django.db import models

class Subscription(models.Model):
    STATUS_CHOICES = [
        ("inactive", "Inactive"),
        ("active", "Active"),
        ("past_due", "Past due"),
        ("cancelled", "Cancelled"),
    ]

    user_email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="inactive")
    plan_name = models.CharField(max_length=80, default="Weekly")
    price = models.DecimalField(max_digits=6, decimal_places=2, default=3.99)
    currency = models.CharField(max_length=10, default="EUR")
    provider = models.CharField(max_length=80, default="Carrier Billing")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_email} - {self.status}"
