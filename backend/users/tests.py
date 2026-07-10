import hashlib
import hmac
import json
from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth.hashers import check_password, make_password
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .models import IntegrationEvent, SubscriptionEntitlement, UserProfile


INTEGRATION_SECRET = "test-integration-secret"


def signed_event_body(payload, secret=INTEGRATION_SECRET):
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return body, f"sha256={signature}"


def base_subscription_event(**overrides):
    payload = {
        "event_id": "int_evt_20260709_000001",
        "event_type": "created",
        "occurred_at": "2026-07-09T10:30:00Z",
        "operator": "test-operator",
        "integrator": "test-integrator",
        "service": "financu",
        "tid": "TID-123456789",
        "sid": "SID-987654321",
        "subscription": {
            "status": "active",
            "access_until": None,
        },
        "customer": {
            "external_user_id": "customer-001",
            "msisdn_hash": "hash-001",
            "country": "ES",
        },
    }
    payload.update(overrides)
    return payload


def minimal_subscription_event(**overrides):
    payload = {
        "event_id": "int_evt_20260709_minimal_001",
        "event_type": "created",
        "occurred_at": "2026-07-09T10:30:00Z",
        "tid": "TID-MINIMAL-123",
        "sid": "SID-MINIMAL-456",
    }
    payload.update(overrides)
    return payload


@override_settings(
    INTEGRATOR_WEBHOOK_SECRET=INTEGRATION_SECRET,
    FRONTEND_SIGNUP_URL="https://app.financu.com/signup",
)
class IntegrationSubscriptionEventTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def post_event(self, payload, signature=None):
        body, valid_signature = signed_event_body(payload)
        return self.client.post(
            reverse("integration-subscription-events"),
            data=body,
            content_type="application/json",
            HTTP_X_FINANU_SIGNATURE=signature or valid_signature,
        )

    def test_created_event_creates_pending_entitlement_and_signup_url(self):
        response = self.post_event(base_subscription_event())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], "signup_token_created")
        self.assertTrue(response.data["signup_token"].startswith("financu_st_"))
        self.assertEqual(
            response.data["signup_url"],
            f"https://app.financu.com/signup?token={response.data['signup_token']}",
        )

        entitlement = SubscriptionEntitlement.objects.get(
            tid="TID-123456789",
            sid="SID-987654321",
        )
        self.assertEqual(
            entitlement.status,
            SubscriptionEntitlement.STATUS_PENDING_REGISTRATION,
        )
        self.assertTrue(entitlement.signup_token_hash)
        self.assertEqual(entitlement.external_user_id, "customer-001")
        self.assertEqual(IntegrationEvent.objects.count(), 1)

    def test_created_event_accepts_minimal_payload(self):
        response = self.post_event(minimal_subscription_event())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], "signup_token_created")
        self.assertTrue(response.data["signup_token"].startswith("financu_st_"))
        entitlement = SubscriptionEntitlement.objects.get(
            tid="TID-MINIMAL-123",
            sid="SID-MINIMAL-456",
        )
        self.assertEqual(
            entitlement.status,
            SubscriptionEntitlement.STATUS_PENDING_REGISTRATION,
        )

    def test_duplicate_event_is_not_processed_twice(self):
        payload = base_subscription_event()
        self.post_event(payload)

        response = self.post_event(payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], "already_processed")
        self.assertEqual(IntegrationEvent.objects.count(), 1)
        self.assertEqual(SubscriptionEntitlement.objects.count(), 1)

    def test_invalid_signature_is_rejected(self):
        response = self.post_event(
            base_subscription_event(),
            signature="sha256=invalid",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"], "invalid_integration_signature")
        self.assertEqual(IntegrationEvent.objects.count(), 0)

    def test_signup_requires_valid_token_and_consumes_it(self):
        created_response = self.post_event(base_subscription_event())
        signup_token = created_response.data["signup_token"]

        missing_token_response = self.client.post(
            reverse("profiles-list"),
            {
                "username": "cliente-token",
                "email": "cliente-token@example.com",
                "password": "password123",
            },
            format="json",
        )
        self.assertEqual(missing_token_response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            reverse("profiles-list"),
            {
                "username": "cliente-token",
                "email": "cliente-token@example.com",
                "password": "password123",
                "signup_token": signup_token,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        profile = UserProfile.objects.get(username="cliente-token")
        self.assertEqual(profile.integrator_tid, "TID-123456789")
        self.assertEqual(profile.integrator_sid, "SID-987654321")
        self.assertEqual(profile.estado, UserProfile.STATUS_ACTIVE)

        entitlement = SubscriptionEntitlement.objects.get(user=profile)
        self.assertEqual(entitlement.status, SubscriptionEntitlement.STATUS_ACTIVE)
        self.assertIsNone(entitlement.signup_token_hash)

        reuse_response = self.client.post(
            reverse("profiles-list"),
            {
                "username": "cliente-token-2",
                "email": "cliente-token-2@example.com",
                "password": "password123",
                "signup_token": signup_token,
            },
            format="json",
        )
        self.assertEqual(reuse_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signup_token_validation_endpoint(self):
        created_response = self.post_event(base_subscription_event())
        signup_token = created_response.data["signup_token"]

        response = self.client.get(
            reverse("signup-token-validate"),
            {"token": signup_token},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["valid"])

    def test_cancel_event_marks_registered_user_inactive(self):
        created_response = self.post_event(base_subscription_event())
        signup_token = created_response.data["signup_token"]
        self.client.post(
            reverse("profiles-list"),
            {
                "username": "cliente-cancelado",
                "email": "cliente-cancelado@example.com",
                "password": "password123",
                "signup_token": signup_token,
            },
            format="json",
        )

        cancel_payload = base_subscription_event(
            event_id="int_evt_20260709_000002",
            event_type="cancelled",
            occurred_at="2026-07-09T12:15:00Z",
            subscription={
                "status": "cancelled",
                "access_until": "2026-07-31",
            },
        )
        response = self.post_event(cancel_payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], "subscription_cancelled")
        profile = UserProfile.objects.get(username="cliente-cancelado")
        self.assertEqual(profile.estado, UserProfile.STATUS_INACTIVE)
        self.assertEqual(profile.fecha_renovacion, date(2026, 7, 31))
        entitlement = profile.subscription_entitlement
        self.assertEqual(entitlement.status, SubscriptionEntitlement.STATUS_CANCELLED)
        self.assertIsNone(entitlement.signup_token_hash)


class LoginSubscriptionTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def create_profile(self, **overrides):
        defaults = {
            "username": "cliente",
            "email": "cliente@example.com",
            "display_name": "Cliente",
            "password_hash": make_password("password123"),
            "fecha_renovacion": timezone.localdate() + timedelta(days=1),
        }
        defaults.update(overrides)
        return UserProfile.objects.create(**defaults)

    def login(self):
        return self.client.post(
            reverse("user-login"),
            {"identifier": "cliente", "password": "password123"},
            format="json",
        )

    def test_inactive_user_can_login_until_paid_period_ends(self):
        self.create_profile(estado=UserProfile.STATUS_INACTIVE)

        response = self.login()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado"], UserProfile.STATUS_INACTIVE)

    def test_inactive_user_cannot_login_after_renewal_date(self):
        self.create_profile(
            estado=UserProfile.STATUS_INACTIVE,
            fecha_renovacion=timezone.localdate(),
        )

        response = self.login()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], "subscription_inactive")

    @patch("users.models.timezone.localdate", return_value=date(2026, 6, 3))
    def test_active_user_refreshes_renewal_from_previous_renewal_date(self, _localdate):
        profile = self.create_profile(fecha_renovacion=date(2026, 6, 1))

        response = self.login()

        profile.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile.fecha_renovacion, date(2026, 7, 1))


class PasswordResetRequestTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def create_profile(self, **overrides):
        defaults = {
            "username": "cliente",
            "email": "cliente@example.com",
            "display_name": "Cliente",
            "password_hash": make_password("password123"),
            "fecha_renovacion": timezone.localdate() + timedelta(days=1),
        }
        defaults.update(overrides)
        return UserProfile.objects.create(**defaults)

    def test_password_reset_requires_email(self):
        response = self.client.post(reverse("user-password-reset"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "missing_email")

    def test_password_reset_returns_not_found_for_unknown_email(self):
        response = self.client.post(
            reverse("user-password-reset"),
            {"email": "missing@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "user_not_found")

    @override_settings(DEBUG=True)
    def test_password_reset_generates_temporary_password_for_existing_email(self):
        profile = self.create_profile()

        response = self.client.post(
            reverse("user-password-reset"),
            {"email": "CLIENTE@example.com"},
            format="json",
        )

        profile.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        temporary_password = response.data["temporary_password"]
        self.assertEqual(len(temporary_password), 14)
        self.assertTrue(check_password(temporary_password, profile.password_hash))

    @override_settings(DEBUG=False, DEFAULT_FROM_EMAIL="no-reply@example.com")
    @patch("users.views.send_mail")
    def test_password_reset_sends_email_without_exposing_password_in_production(self, send_mail):
        profile = self.create_profile()

        response = self.client.post(
            reverse("user-password-reset"),
            {"email": "cliente@example.com"},
            format="json",
        )

        profile.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("temporary_password", response.data)
        send_mail.assert_called_once()
        email_body = send_mail.call_args.args[1]
        temporary_password = email_body.split("Temporary password: ")[1].split("\n", 1)[0]
        self.assertTrue(check_password(temporary_password, profile.password_hash))
