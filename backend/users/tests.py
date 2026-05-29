from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from django.test import TestCase
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
