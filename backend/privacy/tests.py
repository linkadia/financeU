import uuid
from datetime import datetime, timezone as datetime_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle

from .models import CookieConsentRecord, mask_ip_address


def consent_payload(**overrides):
    payload = {
        "event_id": str(uuid.uuid4()),
        "consent_id": str(uuid.uuid4()),
        "action": CookieConsentRecord.ACTION_ACCEPT_ALL,
        "analytics": True,
        "ads_measurement": True,
        "marketing": False,
        "policy_version": "1.1",
        "language": "pl",
        "page_path": "/dashboard",
        "client_recorded_at": "2026-10-20T09:30:00Z",
    }
    payload.update(overrides)
    return payload


class MaskIpAddressTests(TestCase):
    def test_masks_ipv4_to_slash_24(self):
        self.assertEqual(mask_ip_address("83.45.120.77"), "83.45.120.0")

    def test_masks_ipv6_to_slash_48(self):
        self.assertEqual(mask_ip_address("2a02:9130:84f1:5c00::1"), "2a02:9130:84f1::")

    def test_returns_none_for_invalid_values(self):
        self.assertIsNone(mask_ip_address(""))
        self.assertIsNone(mask_ip_address("not-an-ip"))


class CookieConsentRecordViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.url = reverse("cookie-consent-records")

    def test_records_choice_with_masked_ip_and_user_agent(self):
        payload = consent_payload()

        response = self.client.post(
            self.url,
            payload,
            format="json",
            REMOTE_ADDR="83.45.120.77",
            HTTP_USER_AGENT="Mozilla/5.0 Test",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["consent_id"], payload["consent_id"])
        self.assertIn("created_at", response.data)
        self.assertNotIn("ip_address", response.data)

        record = CookieConsentRecord.objects.get()
        self.assertEqual(str(record.consent_id), payload["consent_id"])
        self.assertEqual(record.action, CookieConsentRecord.ACTION_ACCEPT_ALL)
        self.assertTrue(record.analytics)
        self.assertTrue(record.ads_measurement)
        self.assertFalse(record.marketing)
        self.assertEqual(record.policy_version, "1.1")
        self.assertEqual(record.language, "pl")
        self.assertEqual(record.ip_address, "83.45.120.0")
        self.assertEqual(record.user_agent, "Mozilla/5.0 Test")
        self.assertIsNotNone(record.client_recorded_at)

    def test_uses_forwarded_client_ip_behind_one_proxy(self):
        response = self.client.post(
            self.url,
            consent_payload(),
            format="json",
            REMOTE_ADDR="10.0.0.5",
            HTTP_X_FORWARDED_FOR="91.200.10.33",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CookieConsentRecord.objects.get().ip_address, "91.200.10.0")

    def test_each_change_adds_a_new_record_for_the_same_consent_id(self):
        consent_id = str(uuid.uuid4())

        self.client.post(self.url, consent_payload(consent_id=consent_id), format="json")
        self.client.post(
            self.url,
            consent_payload(
                consent_id=consent_id,
                action=CookieConsentRecord.ACTION_CUSTOM,
                analytics=False,
                marketing=False,
            ),
            format="json",
        )

        history = CookieConsentRecord.objects.filter(consent_id=consent_id).order_by("id")
        self.assertEqual([record.analytics for record in history], [True, False])

    def test_strips_query_string_from_page_path(self):
        response = self.client.post(
            self.url,
            consent_payload(page_path="/signup?token=secret-signup-token#form"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CookieConsentRecord.objects.get().page_path, "/signup")

    def test_rejects_absolute_page_urls(self):
        response = self.client.post(
            self.url,
            consent_payload(page_path="https://example.com/dashboard"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(CookieConsentRecord.objects.exists())

    def test_rejects_action_that_does_not_match_categories(self):
        response = self.client.post(
            self.url,
            consent_payload(action=CookieConsentRecord.ACTION_REJECT_ALL, analytics=True),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("action", response.data)
        self.assertFalse(CookieConsentRecord.objects.exists())

    def test_requires_explicit_category_choices(self):
        payload = consent_payload(action=CookieConsentRecord.ACTION_CUSTOM)
        payload.pop("analytics")

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("analytics", response.data)

    def test_rejects_invalid_consent_id(self):
        response = self.client.post(
            self.url,
            consent_payload(consent_id="not-a-uuid"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("consent_id", response.data)


class CookieConsentRecordModelTests(TestCase):
    def test_record_label_uses_the_configured_local_timezone(self):
        record = CookieConsentRecord(consent_id=uuid.uuid4(), action="custom")
        record.created_at = datetime(2026, 10, 21, 8, tzinfo=datetime_timezone.utc)
        with timezone.override("Europe/Madrid"):
            self.assertIn("2026-10-21 10:00", str(record))

    def test_records_cannot_be_modified(self):
        record = CookieConsentRecord.objects.create(
            event_id=uuid.uuid4(),
            consent_id=uuid.uuid4(),
            action=CookieConsentRecord.ACTION_ACCEPT_ALL,
            analytics=True,
            marketing=False,
            policy_version="1.0",
        )

        record.analytics = False
        with self.assertRaises(ValueError):
            record.save()

        record.refresh_from_db()
        self.assertTrue(record.analytics)


class CookieConsentReliabilityTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.url = reverse("cookie-consent-records")

    def test_retries_return_the_original_record_without_duplicating_it(self):
        payload = consent_payload()
        first = self.client.post(self.url, payload, format="json", HTTP_USER_AGENT="Original browser")
        retry = self.client.post(self.url, payload, format="json", HTTP_USER_AGENT="Changed on retry")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(retry.status_code, 200)
        self.assertEqual(first.data, retry.data)
        self.assertEqual(CookieConsentRecord.objects.count(), 1)
        self.assertEqual(CookieConsentRecord.objects.get().user_agent, "Original browser")

    def test_reusing_an_event_with_different_data_is_a_conflict(self):
        payload = consent_payload(action=CookieConsentRecord.ACTION_CUSTOM)
        self.client.post(self.url, payload, format="json")
        response = self.client.post(self.url, {**payload, "analytics": False}, format="json")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(CookieConsentRecord.objects.count(), 1)
        self.assertTrue(CookieConsentRecord.objects.get().analytics)

    def test_two_decisions_at_the_same_client_timestamp_are_distinct_events(self):
        payload = consent_payload()
        self.client.post(self.url, payload, format="json")
        response = self.client.post(self.url, {**payload, "event_id": str(uuid.uuid4())}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(CookieConsentRecord.objects.count(), 2)

    def test_event_identifier_is_required_and_must_be_a_uuid(self):
        for event_id in (None, "not-a-uuid"):
            with self.subTest(event_id=event_id):
                payload = consent_payload(event_id=event_id)
                if event_id is None:
                    payload.pop("event_id")
                response = self.client.post(self.url, payload, format="json")
                self.assertEqual(response.status_code, 400)
        self.assertFalse(CookieConsentRecord.objects.exists())

    def test_marketing_cannot_be_granted_for_any_action(self):
        for action in ("accept_all", "reject_all", "custom"):
            with self.subTest(action=action):
                response = self.client.post(self.url, consent_payload(action=action, marketing=True), format="json")
                self.assertEqual(response.status_code, 400)
                self.assertIn("marketing", response.data)
        self.assertFalse(CookieConsentRecord.objects.exists())

    def test_reject_requires_analytics_off_and_accept_requires_it_on(self):
        for action, analytics in (("accept_all", False), ("reject_all", True)):
            with self.subTest(action=action):
                response = self.client.post(self.url, consent_payload(action=action, analytics=analytics), format="json")
                self.assertEqual(response.status_code, 400)

    def test_reject_and_custom_choices_are_recorded(self):
        for action, analytics in (("reject_all", False), ("custom", False), ("custom", True)):
            response = self.client.post(self.url, consent_payload(action=action, analytics=analytics, ads_measurement=False), format="json")
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.data["analytics"], analytics)
            self.assertFalse(response.data["marketing"])

    def test_custom_accepts_all_four_independent_category_combinations(self):
        for analytics in (False, True):
            for ads_measurement in (False, True):
                with self.subTest(analytics=analytics, ads_measurement=ads_measurement):
                    response = self.client.post(self.url, consent_payload(
                        action="custom", analytics=analytics, ads_measurement=ads_measurement,
                    ), format="json")
                    self.assertEqual(response.status_code, 201)
                    self.assertEqual(response.data["analytics"], analytics)
                    self.assertEqual(response.data["ads_measurement"], ads_measurement)
                    self.assertFalse(response.data["marketing"])

    def test_accept_and_reject_require_both_categories_to_match(self):
        for action, expected in (("accept_all", True), ("reject_all", False)):
            for analytics in (False, True):
                for ads_measurement in (False, True):
                    with self.subTest(action=action, analytics=analytics, ads_measurement=ads_measurement):
                        response = self.client.post(self.url, consent_payload(
                            action=action, analytics=analytics, ads_measurement=ads_measurement,
                        ), format="json")
                        self.assertEqual(response.status_code, 201 if analytics == ads_measurement == expected else 400)

    def test_policy_1_1_requires_explicit_advertising_measurement_choice(self):
        for action in ("accept_all", "reject_all", "custom"):
            payload = consent_payload(action=action, analytics=action == "accept_all")
            payload.pop("ads_measurement")
            response = self.client.post(self.url, payload, format="json")
            self.assertEqual(response.status_code, 400)
            self.assertIn("ads_measurement", response.data)
        response = self.client.post(self.url, consent_payload(ads_measurement=None), format="json")
        self.assertEqual(response.status_code, 400)

    def test_legacy_queued_events_retry_without_advertising_consent(self):
        for action, analytics in (("accept_all", True), ("reject_all", False), ("custom", True), ("custom", False)):
            payload = consent_payload(policy_version="1.0", action=action, analytics=analytics)
            payload.pop("ads_measurement")
            first = self.client.post(self.url, payload, format="json")
            retry = self.client.post(self.url, payload, format="json")
            explicit_retry = self.client.post(self.url, {**payload, "ads_measurement": False}, format="json")
            self.assertEqual(first.status_code, 201)
            self.assertEqual(retry.status_code, 200)
            self.assertEqual(explicit_retry.status_code, 200)
            self.assertEqual(first.data, retry.data)
            self.assertFalse(first.data["ads_measurement"])
        self.assertEqual(CookieConsentRecord.objects.count(), 4)

    def test_retry_of_an_existing_legacy_record_remains_idempotent(self):
        payload = consent_payload(policy_version="1.0")
        payload.pop("ads_measurement")
        CookieConsentRecord.objects.create(**payload)
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["ads_measurement"])
        self.assertEqual(CookieConsentRecord.objects.count(), 1)

    def test_legacy_policy_cannot_grant_advertising_measurement_or_change_action_rules(self):
        for overrides in ({"ads_measurement": True}, {"analytics": False, "ads_measurement": False}):
            response = self.client.post(self.url, consent_payload(policy_version="1.0", **overrides), format="json")
            self.assertEqual(response.status_code, 400)
        self.assertFalse(CookieConsentRecord.objects.exists())

    def test_unknown_policy_versions_are_rejected(self):
        for version in ("", "0.9", "1.3", "future"):
            response = self.client.post(self.url, consent_payload(policy_version=version), format="json")
            self.assertEqual(response.status_code, 400)
            self.assertIn("policy_version", response.data)

    def test_changing_advertising_measurement_on_the_same_event_is_a_conflict(self):
        payload = consent_payload(action="custom", analytics=False)
        self.assertEqual(self.client.post(self.url, payload, format="json").status_code, 201)
        response = self.client.post(self.url, {**payload, "ads_measurement": False}, format="json")
        self.assertEqual(response.status_code, 409)
        self.assertTrue(CookieConsentRecord.objects.get().ads_measurement)
        self.assertEqual(CookieConsentRecord.objects.count(), 1)

    def test_external_or_protocol_relative_paths_are_rejected(self):
        for path in ("https://example.com/", "//example.com/path", "relative-path", "/\\example.com"):
            with self.subTest(path=path):
                response = self.client.post(self.url, consent_payload(page_path=path), format="json")
                self.assertEqual(response.status_code, 400)

    def test_server_metadata_cannot_be_overridden_and_user_agent_is_bounded(self):
        response = self.client.post(
            self.url,
            {**consent_payload(), "created_at": "2000-01-01T00:00:00Z", "ip_address": "1.2.3.4", "user_agent": "forged"},
            format="json", REMOTE_ADDR="83.45.120.77", HTTP_USER_AGENT="x" * 600,
        )
        self.assertEqual(response.status_code, 201)
        record = CookieConsentRecord.objects.get()
        self.assertEqual(record.ip_address, "83.45.120.0")
        self.assertEqual(record.user_agent, "x" * 512)
        self.assertNotEqual(record.created_at.year, 2000)
        self.assertNotIn("ip_address", response.data)
        self.assertNotIn("user_agent", response.data)

    def test_optional_fields_have_consistent_defaults_for_retries(self):
        payload = consent_payload()
        for field in ("language", "page_path", "client_recorded_at"):
            payload.pop(field)
        self.assertEqual(self.client.post(self.url, payload, format="json").status_code, 201)
        response = self.client.post(self.url, {**payload, "language": "", "page_path": "", "client_recorded_at": None}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_public_endpoint_does_not_expose_the_history(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_public_endpoint_accepts_requests_even_with_an_admin_session_and_no_csrf_token(self):
        user = get_user_model().objects.create_user(username="cookie-test-admin", is_staff=True)
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(user)
        self.assertEqual(client.post(self.url, consent_payload(), format="json").status_code, 201)

    def test_scope_rate_limit_is_enforced(self):
        with patch.object(ScopedRateThrottle, "THROTTLE_RATES", {"cookie_consent": "1/hour"}):
            first = self.client.post(self.url, consent_payload(), format="json")
            limited = self.client.post(self.url, consent_payload(), format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(limited.status_code, 429)
        self.assertGreater(limited.data["seconds_remaining"], 0)
        self.assertEqual(CookieConsentRecord.objects.count(), 1)

    def test_database_rejects_duplicate_event_identifiers(self):
        payload = consent_payload()
        self.client.post(self.url, payload, format="json")
        record = CookieConsentRecord.objects.get()
        with self.assertRaises(IntegrityError), transaction.atomic():
            CookieConsentRecord.objects.create(
                event_id=record.event_id, consent_id=record.consent_id, action=record.action,
                analytics=True, marketing=False, policy_version="1.0",
            )


class CookieConsentAnalyticsOnlyTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.url = reverse("cookie-consent-records")

    def test_current_policy_records_accept_reject_and_both_custom_analytics_choices(self):
        for action, analytics in (("accept_all", True), ("reject_all", False), ("custom", True), ("custom", False)):
            response = self.client.post(self.url, consent_payload(
                policy_version="1.2", action=action, analytics=analytics, ads_measurement=False,
            ), format="json")
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.data["analytics"], analytics)
            self.assertFalse(response.data["ads_measurement"])
            self.assertFalse(response.data["marketing"])

    def test_current_policy_cannot_grant_advertising_for_any_action(self):
        for action in ("accept_all", "reject_all", "custom"):
            response = self.client.post(self.url, consent_payload(
                policy_version="1.2", action=action, analytics=action == "accept_all", ads_measurement=True,
            ), format="json")
            self.assertEqual(response.status_code, 400)
            self.assertIn("ads_measurement", response.data)
        self.assertFalse(CookieConsentRecord.objects.exists())

    def test_current_policy_requires_explicit_false_and_consistent_action(self):
        for value in (None, "missing"):
            payload = consent_payload(policy_version="1.2", ads_measurement=value)
            if value == "missing":
                payload.pop("ads_measurement")
            response = self.client.post(self.url, payload, format="json")
            self.assertEqual(response.status_code, 400)
            self.assertIn("ads_measurement", response.data)
        for action, analytics in (("accept_all", False), ("reject_all", True)):
            response = self.client.post(self.url, consent_payload(
                policy_version="1.2", action=action, analytics=analytics, ads_measurement=False,
            ), format="json")
            self.assertEqual(response.status_code, 400)
            self.assertIn("action", response.data)

    def test_current_choice_preserves_prior_policy_history_and_idempotent_retries(self):
        previous = consent_payload()
        self.assertEqual(self.client.post(self.url, previous, format="json").status_code, 201)
        current = consent_payload(consent_id=previous["consent_id"], policy_version="1.2", ads_measurement=False)
        self.assertEqual(self.client.post(self.url, current, format="json").status_code, 201)
        self.assertEqual(self.client.post(self.url, current, format="json").status_code, 200)
        self.assertEqual(self.client.post(self.url, previous, format="json").status_code, 200)
        self.assertEqual(CookieConsentRecord.objects.count(), 2)
        history = CookieConsentRecord.objects.order_by("id")
        self.assertEqual([(row.policy_version, row.ads_measurement) for row in history], [("1.1", True), ("1.2", False)])


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class CookieConsentAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.viewer = get_user_model().objects.create_user(username="consent-viewer", is_staff=True)
        cls.viewer.user_permissions.add(Permission.objects.get(codename="view_cookieconsentrecord"))
        cls.record = CookieConsentRecord.objects.create(
            event_id=uuid.uuid4(), consent_id=uuid.uuid4(), action="custom", analytics=True,
            ads_measurement=True, marketing=False, policy_version="1.1", language="pl", page_path="/privacy",
        )

    def setUp(self):
        self.client.force_login(self.viewer)

    def test_staff_with_view_permission_can_search_and_read_the_record(self):
        listing = self.client.get(reverse("admin:privacy_cookieconsentrecord_changelist"), {"q": str(self.record.consent_id)})
        self.assertEqual(listing.status_code, 200)
        self.assertContains(listing, str(self.record.consent_id))
        detail = self.client.get(reverse("admin:privacy_cookieconsentrecord_change", args=[self.record.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, str(self.record.event_id))
        self.assertNotContains(detail, 'name="analytics"')
        self.assertContains(detail, "Medición publicitaria")
        self.assertNotContains(detail, 'name="ads_measurement"')

    def test_advertising_measurement_is_visible_and_filterable(self):
        other = CookieConsentRecord.objects.create(
            event_id=uuid.uuid4(), consent_id=uuid.uuid4(), action="reject_all",
            analytics=False, ads_measurement=False, marketing=False, policy_version="1.1",
        )
        listing = self.client.get(reverse("admin:privacy_cookieconsentrecord_changelist"), {"ads_measurement__exact": "1"})
        self.assertEqual(listing.status_code, 200)
        self.assertContains(listing, 'column-ads_measurement')
        self.assertContains(listing, str(self.record.consent_id))
        self.assertNotContains(listing, str(other.consent_id))

    def test_manual_additions_and_edits_are_forbidden(self):
        self.assertEqual(self.client.get(reverse("admin:privacy_cookieconsentrecord_add")).status_code, 403)
        response = self.client.post(reverse("admin:privacy_cookieconsentrecord_change", args=[self.record.pk]), {"analytics": False})
        self.assertEqual(response.status_code, 403)
        self.record.refresh_from_db()
        self.assertTrue(self.record.analytics)

    def test_admin_history_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("admin:privacy_cookieconsentrecord_changelist")).status_code, 302)

    def test_deletion_requires_an_explicit_permission(self):
        response = self.client.post(reverse("admin:privacy_cookieconsentrecord_delete", args=[self.record.pk]), {"post": "yes"})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(CookieConsentRecord.objects.filter(pk=self.record.pk).exists())

    def test_even_a_superuser_cannot_create_or_edit_records_manually(self):
        owner = get_user_model().objects.create_superuser(username="consent-owner", email="owner@example.test")
        self.client.force_login(owner)
        self.assertEqual(self.client.get(reverse("admin:privacy_cookieconsentrecord_add")).status_code, 403)
        response = self.client.post(reverse("admin:privacy_cookieconsentrecord_change", args=[self.record.pk]), {"analytics": False})
        self.assertEqual(response.status_code, 403)
        self.record.refresh_from_db()
        self.assertTrue(self.record.analytics)

    def test_authorized_admin_can_purge_a_record(self):
        owner = get_user_model().objects.create_superuser(username="consent-purge-owner", email="owner@example.test")
        self.client.force_login(owner)
        response = self.client.post(reverse("admin:privacy_cookieconsentrecord_delete", args=[self.record.pk]), {"post": "yes"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(CookieConsentRecord.objects.filter(pk=self.record.pk).exists())


class CookieConsentMigrationTests(TransactionTestCase):
    def test_existing_history_keeps_its_data_and_defaults_measurement_to_false(self):
        old_target = [("privacy", "0001_initial")]
        new_target = [("privacy", "0002_cookieconsentrecord_ads_measurement")]
        executor = MigrationExecutor(connection)
        executor.migrate(old_target)
        try:
            old_model = executor.loader.project_state(old_target).apps.get_model("privacy", "CookieConsentRecord")
            event_id, consent_id = uuid.uuid4(), uuid.uuid4()
            original = old_model.objects.create(
                event_id=event_id, consent_id=consent_id, action="accept_all",
                analytics=True, marketing=False, policy_version="1.0",
            )
            executor = MigrationExecutor(connection)
            executor.migrate(new_target)
            record = CookieConsentRecord.objects.get(event_id=event_id)
            self.assertFalse(record.ads_measurement)
            self.assertTrue(record.analytics)
            self.assertEqual(record.consent_id, consent_id)
            self.assertEqual(record.created_at, original.created_at)
            self.assertEqual(record.policy_version, "1.0")
        finally:
            MigrationExecutor(connection).migrate(new_target)
