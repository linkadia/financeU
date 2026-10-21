import ipaddress

# pyrefly: ignore [missing-import]
from django.db import models
from django.utils import timezone


def mask_ip_address(value):
    """Keep only the network part of an IP so the record does not store the full address."""
    try:
        address = ipaddress.ip_address((value or "").strip())
    except ValueError:
        return None

    prefix = 24 if address.version == 4 else 48
    network = ipaddress.ip_network(f"{address}/{prefix}", strict=False)
    return str(network.network_address)


class CookieConsentRecord(models.Model):
    """Append-only proof of every choice made in the cookie banner.

    Each accept, reject or change adds a new row, so the full history of a
    browser's consent can be shown for its consent_id.
    """

    ACTION_ACCEPT_ALL = "accept_all"
    ACTION_REJECT_ALL = "reject_all"
    ACTION_CUSTOM = "custom"
    ACTION_CHOICES = [
        (ACTION_ACCEPT_ALL, "Aceptar todo"),
        (ACTION_REJECT_ALL, "Rechazar todo"),
        (ACTION_CUSTOM, "Preferencias guardadas"),
    ]

    event_id = models.UUIDField(unique=True)
    consent_id = models.UUIDField(db_index=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    analytics = models.BooleanField()
    ads_measurement = models.BooleanField(default=False, verbose_name="Medición publicitaria")
    marketing = models.BooleanField()
    policy_version = models.CharField(max_length=20)
    language = models.CharField(max_length=10, blank=True)
    page_path = models.CharField(max_length=255, blank=True)
    # Informative only: the browser clock is not trusted, created_at is the proof.
    client_recorded_at = models.DateTimeField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=512, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Registro de consentimiento de cookies"
        verbose_name_plural = "Registros de consentimiento de cookies"

    def __str__(self):
        recorded_at = timezone.localtime(self.created_at).strftime("%Y-%m-%d %H:%M") if self.created_at else "pendiente"
        return f"{self.consent_id} · {self.get_action_display()} · {recorded_at}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError("Cookie consent records are append-only.")
        super().save(*args, **kwargs)
