import uuid
import hashlib
import secrets
from calendar import monthrange

# pyrefly: ignore [missing-import]
from django.db import models
# pyrefly: ignore [missing-import]
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
    integrator_tid = models.CharField(max_length=128, blank=True, db_index=True)
    integrator_sid = models.CharField(max_length=128, blank=True, db_index=True)
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


class SubscriptionEntitlement(models.Model):
    STATUS_PENDING_REGISTRATION = "pending_registration"
    STATUS_ACTIVE = "active"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING_REGISTRATION, "Pending registration"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    TOKEN_PREFIX = "financu_st_"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.OneToOneField(
        UserProfile,
        on_delete=models.SET_NULL,
        related_name="subscription_entitlement",
        blank=True,
        null=True,
    )
    tid = models.CharField(max_length=128, db_index=True)
    sid = models.CharField(max_length=128, db_index=True)
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING_REGISTRATION,
        db_index=True,
    )
    signup_token_hash = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        null=True,
        editable=False,
    )
    signup_token_created_at = models.DateTimeField(blank=True, null=True)
    access_until = models.DateField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    external_user_id = models.CharField(max_length=128, blank=True)
    msisdn_hash = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=2, blank=True)
    last_event_id = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tid", "sid"],
                name="unique_subscription_entitlement_tid_sid",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "access_until"]),
        ]

    def __str__(self):
        return f"{self.tid}/{self.sid}"

    @classmethod
    def hash_signup_token(cls, token):
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def issue_signup_token(cls):
        return f"{cls.TOKEN_PREFIX}{secrets.token_urlsafe(32)}"

    @classmethod
    def get_by_signup_token(cls, token):
        if not token:
            return None
        return cls.objects.filter(signup_token_hash=cls.hash_signup_token(token)).first()

    def generate_signup_token(self):
        token = self.issue_signup_token()
        self.signup_token_hash = self.hash_signup_token(token)
        self.signup_token_created_at = timezone.now()
        return token

    def can_be_used_for_signup(self, today=None):
        today = today or timezone.localdate()
        if self.status != self.STATUS_PENDING_REGISTRATION:
            return False
        if self.user_id:
            return False
        if not self.signup_token_hash:
            return False
        if self.access_until and self.access_until < today:
            return False
        return True

    def mark_registered(self, user):
        self.user = user
        self.status = self.STATUS_ACTIVE
        self.signup_token_hash = None
        self.save(
            update_fields=[
                "user",
                "status",
                "signup_token_hash",
                "updated_at",
            ]
        )


class IntegrationEvent(models.Model):
    TYPE_CREATED = "created"
    TYPE_RENEWED = "renewed"
    TYPE_CANCELLED = "cancelled"
    TYPE_CHOICES = [
        (TYPE_CREATED, "Created"),
        (TYPE_RENEWED, "Renewed"),
        (TYPE_CANCELLED, "Cancelled"),
    ]

    STATUS_PROCESSED = "processed"
    STATUS_IGNORED = "ignored"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PROCESSED, "Processed"),
        (STATUS_IGNORED, "Ignored"),
        (STATUS_FAILED, "Failed"),
    ]

    event_id = models.CharField(max_length=128, unique=True)
    event_type = models.CharField(max_length=32, choices=TYPE_CHOICES, db_index=True)
    operator = models.CharField(max_length=80, blank=True)
    integrator = models.CharField(max_length=80, blank=True)
    service = models.CharField(max_length=80, blank=True)
    tid = models.CharField(max_length=128, db_index=True)
    sid = models.CharField(max_length=128, db_index=True)
    occurred_at = models.DateTimeField()
    raw_payload = models.JSONField(default=dict)
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_PROCESSED,
        db_index=True,
    )
    action = models.CharField(max_length=80, blank=True)
    error_message = models.TextField(blank=True)
    entitlement = models.ForeignKey(
        SubscriptionEntitlement,
        on_delete=models.SET_NULL,
        related_name="events",
        blank=True,
        null=True,
    )
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["tid", "sid", "occurred_at"]),
        ]

    def __str__(self):
        return f"{self.event_id} ({self.event_type})"
