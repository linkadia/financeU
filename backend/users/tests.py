from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth.hashers import check_password, make_password
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .models import UserProfile


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
