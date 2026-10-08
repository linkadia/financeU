import hashlib
import hmac
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth.hashers import check_password, make_password
from django.db import OperationalError, close_old_connections
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .models import IntegrationEvent, SubscriptionEntitlement, UserProfile, add_month
from .msisdn import fingerprint_from_sha256, sha256_msisdn


INTEGRATION_SECRET = "test-integration-secret"
MSISDN_SECRET = "test-msisdn-secret"
MOBILE_NUMBER = "48500000000"
MOBILE_SHA256 = "8fb9d70275a9b255efeaea4fb5a467960e5ab642896e015ed1b0495831c79bc1"


def signed_event_body(payload, secret=INTEGRATION_SECRET):
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return body, f"sha256={signature}"


def base_subscription_event(**overrides):
    payload = {
        "event_id": "int_evt_20260709_000001",
        "event_type": "created",
        "occurred_at": timezone.now().isoformat(),
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


def mobile_subscription_event(**overrides):
    payload = base_subscription_event(
        event_id="mobile-event-001",
        occurred_at=timezone.now().isoformat(),
        tid="MOBILE-TID-001",
        sid="MOBILE-SID-001",
        subscription={"status": "active"},
        customer={"msisdn_hash": MOBILE_SHA256, "country": "PL"},
    )
    payload.update(overrides)
    return payload


@override_settings(
    INTEGRATOR_WEBHOOK_SECRET=INTEGRATION_SECRET,
    MSISDN_HMAC_KEY=MSISDN_SECRET,
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

    @override_settings(MSISDN_HMAC_KEY="")
    def test_token_operator_without_mobile_supports_monthly_subscription_lifecycle(self):
        payload = base_subscription_event(
            occurred_at="2026-10-08T10:00:00Z",
            operator="other-operator",
            customer={},
        )
        created = self.post_event(payload)
        self.assertEqual(created.status_code, status.HTTP_200_OK)
        with patch("users.models.timezone.localdate", return_value=date(2026, 10, 8)):
            signup = self.client.post(reverse("profiles-list"), {
                "username": "other-operator-token",
                "email": "other-operator-token@example.com",
                "password": "password123",
                "signup_token": created.data["signup_token"],
            }, format="json")
        self.assertEqual(signup.status_code, status.HTTP_201_CREATED)
        profile = UserProfile.objects.get(username="other-operator-token")
        self.assertIsNone(profile.msisdn_hash)
        self.assertIsNone(profile.fecha_renovacion)
        self.assertEqual(profile.integrator_tid, payload["tid"])
        self.assertEqual(profile.integrator_sid, payload["sid"])
        entitlement = profile.subscription_entitlement
        self.assertEqual(entitlement.msisdn_hash, "")
        self.assertIsNotNone(entitlement.payment_confirmed_at)
        self.assertEqual(entitlement.access_until, date(2026, 11, 8))

        cancelled = self.post_event(base_subscription_event(
            event_id="other-operator-cancel", event_type="cancelled",
            occurred_at="2026-10-20T10:00:00Z",
            subscription={"status": "cancelled"}, customer={},
        ))
        self.assertEqual(cancelled.status_code, status.HTTP_200_OK)
        profile.refresh_from_db()
        self.assertTrue(profile.can_access_platform(today=date(2026, 11, 7)))
        self.assertFalse(profile.can_access_platform(today=date(2026, 11, 8)))

        renewed = self.post_event(base_subscription_event(
            event_id="other-operator-new-payment", event_type="renewed",
            occurred_at="2026-11-10T10:00:00Z", customer={},
        ))
        self.assertEqual(renewed.status_code, status.HTTP_200_OK)
        profile.refresh_from_db()
        self.assertEqual(profile.estado, UserProfile.STATUS_ACTIVE)
        self.assertIsNone(profile.fecha_renovacion)
        self.assertIsNone(profile.msisdn_hash)
        self.assertTrue(profile.can_access_platform(today=date(2027, 11, 10)))
        self.assertEqual(UserProfile.objects.filter(integrator_tid=payload["tid"]).count(), 1)

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

    def test_mobile_hash_vector_is_wrapped_and_not_retained_in_event(self):
        self.assertEqual(sha256_msisdn(MOBILE_NUMBER), MOBILE_SHA256)
        response = self.post_event(mobile_subscription_event())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entitlement = SubscriptionEntitlement.objects.get(tid="MOBILE-TID-001")
        expected = "v1:" + hmac.new(
            MSISDN_SECRET.encode(), MOBILE_SHA256.encode(), hashlib.sha256
        ).hexdigest()
        self.assertEqual(entitlement.msisdn_hash, expected)
        self.assertNotEqual(entitlement.msisdn_hash, MOBILE_SHA256)
        self.assertEqual(entitlement.access_until, add_month(timezone.localdate()))
        self.assertIsNotNone(entitlement.payment_confirmed_at)
        self.assertNotIn(MOBILE_SHA256, str(IntegrationEvent.objects.get().raw_payload))
        self.assertNotIn(MOBILE_SHA256, str(response.data))

    def test_mobile_payment_defaults_to_calendar_month(self):
        for index, (occurred_at, expected_end) in enumerate((
            ("2026-10-08T10:44:42Z", date(2026, 11, 8)),
            ("2026-01-31T10:00:00Z", date(2026, 2, 28)),
            ("2028-01-31T10:00:00Z", date(2028, 2, 29)),
            ("2026-12-31T10:00:00Z", date(2027, 1, 31)),
        )):
            with self.subTest(occurred_at=occurred_at):
                response = self.post_event(mobile_subscription_event(
                    event_id=f"monthly-event-{index}",
                    tid=f"MONTHLY-TID-{index}",
                    occurred_at=occurred_at,
                ))
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                entitlement = SubscriptionEntitlement.objects.get(tid=f"MONTHLY-TID-{index}")
                self.assertEqual(entitlement.access_until, expected_end)

    def test_explicit_paid_period_overrides_monthly_default(self):
        response = self.post_event(mobile_subscription_event(
            subscription={"status": "active", "access_until": "2026-11-20"},
            occurred_at="2026-10-08T10:44:42Z",
        ))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entitlement = SubscriptionEntitlement.objects.get(tid="MOBILE-TID-001")
        self.assertEqual(entitlement.access_until, date(2026, 11, 20))

    def test_invalid_mobile_hash_and_missing_hmac_key_fail_closed(self):
        invalid = mobile_subscription_event(
            customer={"msisdn_hash": MOBILE_SHA256.upper(), "country": "PL"}
        )
        self.assertEqual(self.post_event(invalid).status_code, status.HTTP_400_BAD_REQUEST)
        null_hash = mobile_subscription_event(customer={"msisdn_hash": None})
        self.assertEqual(self.post_event(null_hash).status_code, status.HTTP_400_BAD_REQUEST)

        with override_settings(MSISDN_HMAC_KEY=""):
            missing_key = self.post_event(mobile_subscription_event())
        self.assertEqual(missing_key.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(SubscriptionEntitlement.objects.count(), 0)

    def test_mobile_signup_claims_paid_subscription_once(self):
        self.post_event(mobile_subscription_event())
        signup = self.client.post(
            reverse("profiles-list"),
            {
                "username": "cliente-mobile",
                "email": "cliente-mobile@example.com",
                "password": "password123",
                "msisdn": "+48 500 000 000",
            },
            format="json",
        )

        self.assertEqual(signup.status_code, status.HTTP_201_CREATED)
        profile = UserProfile.objects.get(username="cliente-mobile")
        entitlement = profile.subscription_entitlement
        self.assertEqual(profile.msisdn_hash, fingerprint_from_sha256(MOBILE_SHA256))
        self.assertIsNone(profile.fecha_renovacion)
        self.assertEqual(entitlement.status, SubscriptionEntitlement.STATUS_ACTIVE)
        self.assertIsNotNone(entitlement.registered_at)
        self.assertNotIn("msisdn_hash", signup.data)
        self.assertNotIn("msisdn", signup.data)

        duplicate = self.client.post(
            reverse("profiles-list"),
            {
                "username": "cliente-mobile-2",
                "email": "cliente-mobile-2@example.com",
                "password": "password123",
                "msisdn": MOBILE_NUMBER,
            },
            format="json",
        )
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(duplicate.data["error"], "subscription_not_eligible")
        self.assertEqual(UserProfile.objects.filter(msisdn_hash=profile.msisdn_hash).count(), 1)

        second_payment = mobile_subscription_event(
            event_id="mobile-event-002",
            tid="MOBILE-TID-002",
            sid="MOBILE-SID-002",
        )
        self.assertEqual(self.post_event(second_payment).status_code, status.HTTP_200_OK)
        second_claim = self.client.post(
            reverse("profiles-list"),
            {
                "username": "cliente-mobile-3",
                "email": "cliente-mobile-3@example.com",
                "password": "password123",
                "msisdn": MOBILE_NUMBER,
            },
            format="json",
        )
        self.assertEqual(second_claim.data["error"], "subscription_not_eligible")

    def test_mobile_signup_rejects_unknown_unpaid_expired_and_ambiguous_numbers(self):
        signup_data = {
            "username": "mobile-unavailable",
            "email": "mobile-unavailable@example.com",
            "password": "password123",
            "msisdn": MOBILE_NUMBER,
        }
        unknown = self.client.post(reverse("profiles-list"), signup_data, format="json")
        self.assertEqual(unknown.data["error"], "subscription_not_eligible")

        self.post_event(mobile_subscription_event(subscription={"status": "pending"}))
        unpaid = self.client.post(reverse("profiles-list"), signup_data, format="json")
        self.assertEqual(unpaid.data["error"], "subscription_not_eligible")

        entitlement = SubscriptionEntitlement.objects.get(tid="MOBILE-TID-001")
        entitlement.payment_confirmed_at = timezone.now()
        entitlement.access_until = timezone.localdate()
        entitlement.save(update_fields=["payment_confirmed_at", "access_until"])
        expired = self.client.post(reverse("profiles-list"), signup_data, format="json")
        self.assertEqual(expired.data["error"], "subscription_not_eligible")

        entitlement.access_until = timezone.localdate() + timedelta(days=2)
        entitlement.save(update_fields=["access_until"])
        SubscriptionEntitlement.objects.create(
            tid="MOBILE-TID-002",
            sid="MOBILE-SID-002",
            msisdn_hash=entitlement.msisdn_hash,
            payment_confirmed_at=timezone.now(),
            access_until=entitlement.access_until,
        )
        ambiguous = self.client.post(reverse("profiles-list"), signup_data, format="json")
        self.assertEqual(ambiguous.data["error"], "subscription_not_eligible")
        self.assertFalse(UserProfile.objects.filter(username="mobile-unavailable").exists())

    def test_mobile_signup_after_cancellation_uses_remaining_paid_period(self):
        self.post_event(mobile_subscription_event())
        paid_until = timezone.localdate() + timedelta(days=2)
        cancel = mobile_subscription_event(
            event_id="mobile-cancel-001",
            event_type="cancelled",
            subscription={"status": "cancelled", "access_until": paid_until.isoformat()},
            customer={},
        )
        self.assertEqual(self.post_event(cancel).status_code, status.HTTP_200_OK)

        signup = self.client.post(
            reverse("profiles-list"),
            {
                "username": "cliente-baja",
                "email": "cliente-baja@example.com",
                "password": "password123",
                "msisdn": "500000000",
            },
            format="json",
        )
        self.assertEqual(signup.status_code, status.HTTP_201_CREATED)
        profile = UserProfile.objects.get(username="cliente-baja")
        self.assertEqual(profile.estado, UserProfile.STATUS_INACTIVE)
        self.assertEqual(profile.fecha_renovacion, paid_until)
        self.assertEqual(profile.subscription_entitlement.status, SubscriptionEntitlement.STATUS_CANCELLED)
        self.assertTrue(profile.can_access_platform())

    def test_token_signup_copies_mobile_hash_when_present(self):
        response = self.post_event(mobile_subscription_event())
        signup = self.client.post(
            reverse("profiles-list"),
            {
                "username": "cliente-token-mobile",
                "email": "cliente-token-mobile@example.com",
                "password": "password123",
                "signup_token": response.data["signup_token"],
            },
            format="json",
        )
        self.assertEqual(signup.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            UserProfile.objects.get(username="cliente-token-mobile").msisdn_hash,
            fingerprint_from_sha256(MOBILE_SHA256),
        )

    def test_cancelled_subscription_expires_then_new_payment_reactivates_user(self):
        created = self.post_event(mobile_subscription_event(
            occurred_at="2026-10-08T10:00:00Z",
        ))
        with patch("users.models.timezone.localdate", return_value=date(2026, 10, 8)):
            signup = self.client.post(reverse("profiles-list"), {
                "username": "monthly-cancel",
                "email": "monthly-cancel@example.com",
                "password": "password123",
                "signup_token": created.data["signup_token"],
            }, format="json")
        self.assertEqual(signup.status_code, status.HTTP_201_CREATED)
        profile = UserProfile.objects.get(username="monthly-cancel")
        self.assertIsNone(profile.fecha_renovacion)
        self.assertTrue(profile.can_access_platform(today=date(2027, 3, 1)))

        cancel = mobile_subscription_event(
            event_id="monthly-cancel-event",
            event_type="cancelled",
            occurred_at="2026-12-20T10:00:00Z",
            subscription={"status": "cancelled"}, customer={},
        )
        self.assertEqual(self.post_event(cancel).status_code, status.HTTP_200_OK)
        profile.refresh_from_db()
        self.assertEqual(profile.fecha_renovacion, date(2027, 1, 8))
        self.assertTrue(profile.can_access_platform(today=date(2027, 1, 7)))
        self.assertFalse(profile.can_access_platform(today=date(2027, 1, 8)))

        # Another cancellation must not extend the already cancelled period.
        cancel.update(event_id="monthly-cancel-repeat", occurred_at="2027-02-01T10:00:00Z")
        self.post_event(cancel)
        profile.refresh_from_db()
        self.assertEqual(profile.fecha_renovacion, date(2027, 1, 8))

        renewed = mobile_subscription_event(
            event_id="monthly-new-payment", event_type="renewed",
            occurred_at="2027-02-03T10:00:00Z",
        )
        self.assertEqual(self.post_event(renewed).status_code, status.HTTP_200_OK)
        profile.refresh_from_db()
        self.assertEqual(profile.estado, UserProfile.STATUS_ACTIVE)
        self.assertIsNone(profile.fecha_renovacion)
        self.assertTrue(profile.can_access_platform(today=date(2028, 2, 3)))

    def test_cancellation_keeps_month_end_billing_anchor(self):
        self.post_event(mobile_subscription_event(occurred_at="2026-01-31T10:00:00Z"))
        response = self.post_event(mobile_subscription_event(
            event_id="month-end-cancel", event_type="cancelled",
            occurred_at="2026-03-20T10:00:00Z",
            subscription={"status": "cancelled"}, customer={},
        ))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entitlement = SubscriptionEntitlement.objects.get(tid="MOBILE-TID-001")
        self.assertEqual(entitlement.access_until, date(2026, 3, 31))

    def test_profiles_cannot_be_deleted_through_api(self):
        profile = UserProfile.objects.create(
            username="keep-account",
            email="keep-account@example.com",
        )
        response = self.client.delete(reverse("profiles-detail", args=[profile.id]))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(UserProfile.objects.filter(pk=profile.id).exists())


@override_settings(
    INTEGRATOR_WEBHOOK_SECRET=INTEGRATION_SECRET,
    MSISDN_HMAC_KEY=MSISDN_SECRET,
)
class ConcurrentMobileSignupTests(TransactionTestCase):
    def test_two_requests_cannot_claim_the_same_subscription(self):
        body, signature = signed_event_body(mobile_subscription_event())
        event = APIClient().post(
            reverse("integration-subscription-events"),
            data=body,
            content_type="application/json",
            HTTP_X_FINANU_SIGNATURE=signature,
        )
        self.assertEqual(event.status_code, status.HTTP_200_OK)
        barrier = Barrier(2)

        def signup(suffix):
            close_old_connections()
            client = APIClient()
            barrier.wait()
            try:
                result = client.post(
                    reverse("profiles-list"),
                    {
                        "username": f"concurrent-{suffix}",
                        "email": f"concurrent-{suffix}@example.com",
                        "password": "password123",
                        "msisdn": MOBILE_NUMBER,
                    },
                    format="json",
                )
                return result.status_code
            except OperationalError:
                # SQLite may report a write lock instead of waiting for row locks.
                return "database_locked"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(signup, (1, 2)))

        self.assertLessEqual(results.count(status.HTTP_201_CREATED), 1)
        fingerprint = fingerprint_from_sha256(MOBILE_SHA256)
        if not UserProfile.objects.filter(msisdn_hash=fingerprint).exists():
            # SQLite can lock out both concurrent writes; one retry must still claim it.
            retry = APIClient().post(
                reverse("profiles-list"),
                {
                    "username": "concurrent-retry",
                    "email": "concurrent-retry@example.com",
                    "password": "password123",
                    "msisdn": MOBILE_NUMBER,
                },
                format="json",
            )
            self.assertEqual(retry.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserProfile.objects.filter(msisdn_hash=fingerprint).count(), 1)
        entitlement = SubscriptionEntitlement.objects.get(tid="MOBILE-TID-001")
        self.assertEqual(bool(entitlement.user_id), bool(UserProfile.objects.filter(username__startswith="concurrent-").exists()))


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
    def test_active_user_can_login_regardless_of_previous_date(self, _localdate):
        profile = self.create_profile(fecha_renovacion=date(2026, 6, 1))

        response = self.login()

        profile.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile.fecha_renovacion, date(2026, 6, 1))

    def test_active_user_has_indefinite_access(self):
        self.create_profile(fecha_renovacion=None)
        response = self.login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["fecha_renovacion"])

    def test_cancelled_user_without_paid_period_is_blocked(self):
        self.create_profile(estado=UserProfile.STATUS_INACTIVE, fecha_renovacion=None)
        self.assertEqual(self.login().status_code, status.HTTP_403_FORBIDDEN)

    def test_subscription_status_reflects_expiry_for_existing_session(self):
        profile = self.create_profile(estado=UserProfile.STATUS_INACTIVE)
        url = reverse("profiles-subscription-status", args=[profile.id])
        self.assertTrue(self.client.get(url).data["can_access"])
        profile.fecha_renovacion = timezone.localdate()
        profile.save(update_fields=["fecha_renovacion"])
        self.assertFalse(self.client.get(url).data["can_access"])


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
