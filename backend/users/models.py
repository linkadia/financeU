import uuid
from calendar import monthrange

from django.db import models
from django.utils import timezone


def add_month(value):
    month = value.month + 1
    year = value.year
    if month > 12:
        month = 1
        year += 1
    day = min(value.day, monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def default_renewal_date():
    return add_month(timezone.localdate())

class UserProfile(models.Model):
    STATUS_ACTIVE = "activo"
    STATUS_INACTIVE = "inactivo"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Activo"),
        (STATUS_INACTIVE, "Inactivo"),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    username = models.CharField(max_length=80, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=120, blank=True)
    operator_token = models.CharField(max_length=255, blank=True, editable=False)
    password_hash = models.CharField(max_length=128, blank=True)
    estado = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        db_index=True,
    )
    fecha_renovacion = models.DateField(default=default_renewal_date)
    onboarding_completed = models.BooleanField(default=False)
    onboarding_interests = models.JSONField(default=list, blank=True)
    onboarding_risk_profile = models.CharField(max_length=40, blank=True)
    onboarding_goal = models.CharField(max_length=60, blank=True)
    selected_agent = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username or self.email

    @property
    def is_subscription_active(self):
        return self.estado == self.STATUS_ACTIVE

    def can_access_platform(self, today=None):
        today = today or timezone.localdate()
        return self.is_subscription_active or today < self.fecha_renovacion

    def refresh_renewal_date_if_active(self, today=None):
        today = today or timezone.localdate()
        if not self.is_subscription_active:
            return False

        changed = False
        while self.fecha_renovacion <= today:
            self.fecha_renovacion = add_month(self.fecha_renovacion)
            changed = True
        return changed
