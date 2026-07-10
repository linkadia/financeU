import hashlib
import hmac
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from .models import IntegrationEvent, SubscriptionEntitlement, UserProfile
from .serializers import (
    IntegrationSubscriptionEventSerializer,
    UserProfileSerializer,
    UserSettingsSerializer,
)
from .throttling import LoginUserIpThrottle


def normalize_signature(value):
    value = (value or "").strip()
    if value.startswith("sha256="):
        return value.split("=", 1)[1]
    return value


def build_signup_url(token):
    separator = "&" if "?" in settings.FRONTEND_SIGNUP_URL else "?"
    return f"{settings.FRONTEND_SIGNUP_URL}{separator}{urlencode({'token': token})}"


def verify_integrator_signature(request):
    secret = settings.INTEGRATOR_WEBHOOK_SECRET
    if not secret:
        return Response(
            {
                "detail": "Integrator webhook secret is not configured.",
                "error": "integration_secret_not_configured",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    signature = normalize_signature(request.headers.get("X-Finanu-Signature"))
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        request.body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        return Response(
            {
                "detail": "Invalid integration signature.",
                "error": "invalid_integration_signature",
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    return None


def get_subscription_access_until(payload):
    subscription = payload.get("subscription") or {}
    return subscription.get("access_until")


def apply_customer_metadata(entitlement, payload):
    customer = payload.get("customer") or {}
    entitlement.external_user_id = customer.get("external_user_id", "") or ""
    entitlement.msisdn_hash = customer.get("msisdn_hash", "") or ""
    entitlement.country = customer.get("country", "") or ""


def activate_entitlement(entitlement, payload):
    signup_token = None
    entitlement.access_until = get_subscription_access_until(payload)
    entitlement.cancelled_at = None
    entitlement.last_event_id = payload["event_id"]
    apply_customer_metadata(entitlement, payload)

    if entitlement.user_id:
        entitlement.status = SubscriptionEntitlement.STATUS_ACTIVE
        entitlement.user.estado = UserProfile.STATUS_ACTIVE
        entitlement.user.integrator_tid = entitlement.tid
        entitlement.user.integrator_sid = entitlement.sid
        if entitlement.access_until:
            entitlement.user.fecha_renovacion = entitlement.access_until
        entitlement.user.save(
            update_fields=[
                "estado",
                "integrator_tid",
                "integrator_sid",
                "fecha_renovacion",
            ]
        )
        action = "subscription_activated"
    else:
        entitlement.status = SubscriptionEntitlement.STATUS_PENDING_REGISTRATION
        signup_token = entitlement.generate_signup_token()
        action = "signup_token_created"

    entitlement.save(
        update_fields=[
            "status",
            "signup_token_hash",
            "signup_token_created_at",
            "access_until",
            "cancelled_at",
            "external_user_id",
            "msisdn_hash",
            "country",
            "last_event_id",
            "updated_at",
        ]
    )
    return action, signup_token


def cancel_entitlement(entitlement, payload):
    access_until = get_subscription_access_until(payload) or timezone.localdate()
    entitlement.status = SubscriptionEntitlement.STATUS_CANCELLED
    entitlement.access_until = access_until
    entitlement.cancelled_at = payload["occurred_at"]
    entitlement.last_event_id = payload["event_id"]
    entitlement.signup_token_hash = None
    apply_customer_metadata(entitlement, payload)

    if entitlement.user_id:
        entitlement.user.estado = UserProfile.STATUS_INACTIVE
        entitlement.user.integrator_tid = entitlement.tid
        entitlement.user.integrator_sid = entitlement.sid
        entitlement.user.fecha_renovacion = access_until
        entitlement.user.save(
            update_fields=[
                "estado",
                "integrator_tid",
                "integrator_sid",
                "fecha_renovacion",
            ]
        )

    entitlement.save(
        update_fields=[
            "status",
            "signup_token_hash",
            "access_until",
            "cancelled_at",
            "external_user_id",
            "msisdn_hash",
            "country",
            "last_event_id",
            "updated_at",
        ]
    )
    return "subscription_cancelled"


class IntegrationSubscriptionEventView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "integration_events"

    def post(self, request):
        signature_error = verify_integrator_signature(request)
        if signature_error:
            return signature_error

        serializer = IntegrationSubscriptionEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        existing_event = IntegrationEvent.objects.filter(
            event_id=payload["event_id"]
        ).first()
        if existing_event:
            return Response(
                {
                    "status": "ok",
                    "action": "already_processed",
                    "event_id": existing_event.event_id,
                    "event_type": existing_event.event_type,
                    "tid": existing_event.tid,
                    "sid": existing_event.sid,
                }
            )

        with transaction.atomic():
            entitlement = (
                SubscriptionEntitlement.objects.select_for_update()
                .filter(tid=payload["tid"], sid=payload["sid"])
                .first()
            )
            if not entitlement:
                entitlement = SubscriptionEntitlement.objects.create(
                    tid=payload["tid"],
                    sid=payload["sid"],
                )

            signup_token = None
            if payload["event_type"] == IntegrationEvent.TYPE_CANCELLED:
                action = cancel_entitlement(entitlement, payload)
            else:
                action, signup_token = activate_entitlement(entitlement, payload)

            IntegrationEvent.objects.create(
                event_id=payload["event_id"],
                event_type=payload["event_type"],
                operator=payload.get("operator", ""),
                integrator=payload.get("integrator", ""),
                service=payload.get("service", ""),
                tid=payload["tid"],
                sid=payload["sid"],
                occurred_at=payload["occurred_at"],
                raw_payload=request.data,
                status=IntegrationEvent.STATUS_PROCESSED,
                action=action,
                entitlement=entitlement,
            )

        response_payload = {
            "status": "ok",
            "action": action,
            "event_id": payload["event_id"],
            "event_type": payload["event_type"],
            "tid": payload["tid"],
            "sid": payload["sid"],
        }
        if signup_token:
            response_payload["signup_token"] = signup_token
            response_payload["signup_url"] = build_signup_url(signup_token)
        if entitlement.access_until:
            response_payload["access_until"] = entitlement.access_until

        return Response(response_payload, status=status.HTTP_200_OK)


class SignupTokenValidationView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "signup"

    def get(self, request):
        token = request.query_params.get("token", "")
        entitlement = SubscriptionEntitlement.get_by_signup_token(token)
        if not entitlement or not entitlement.can_be_used_for_signup():
            return Response(
                {
                    "valid": False,
                    "detail": "Invalid or expired signup token.",
                    "error": "invalid_signup_token",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"valid": True})


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle, ScopedRateThrottle]
    throttle_scope_by_action = {
        # The create action is the current registration endpoint.
        "create": "signup",
        # Settings includes profile edits and password changes, so it is tighter.
        "user_settings": "settings",
        "complete_onboarding": "onboarding",
    }

    def get_throttles(self):
        # A scoped throttle lets the SPA burst on normal profile reads while
        # keeping sensitive actions like signup and settings more conservative.
        self.throttle_scope = self.throttle_scope_by_action.get(self.action, "profiles")
        return super().get_throttles()

    @action(detail=True, methods=["get", "patch"], url_path="settings")
    def user_settings(self, request, pk=None):
        profile = self.get_object()

        if request.method == "GET":
            return Response(UserSettingsSerializer(profile).data)

        serializer = UserSettingsSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(UserSettingsSerializer(profile).data)

    @action(detail=True, methods=["post"], url_path="complete-onboarding")
    def complete_onboarding(self, request, pk=None):
        profile = self.get_object()
        interests = request.data.get("interests", [])
        risk_profile = request.data.get("risk_profile", "")
        goal = request.data.get("goal", "")
        selected_agent = request.data.get("selected_agent", "")

        if not isinstance(interests, list):
            return Response(
                {"detail": "Interests must be a list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        missing_fields = [
            field
            for field, value in {
                "interests": interests,
                "risk_profile": risk_profile,
                "goal": goal,
                "selected_agent": selected_agent,
            }.items()
            if not value
        ]
        if missing_fields:
            return Response(
                {"detail": f"Missing onboarding fields: {', '.join(missing_fields)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile.onboarding_interests = interests
        profile.onboarding_risk_profile = risk_profile
        profile.onboarding_goal = goal
        profile.selected_agent = selected_agent
        profile.onboarding_completed = True
        profile.save(
            update_fields=[
                "onboarding_interests",
                "onboarding_risk_profile",
                "onboarding_goal",
                "selected_agent",
                "onboarding_completed",
            ]
        )

        return Response(UserProfileSerializer(profile).data)


class LoginView(APIView):
    throttle_classes = [ScopedRateThrottle, LoginUserIpThrottle]
    throttle_scope = "login"

    def post(self, request):
        identifier = (
            request.data.get("identifier")
            or request.data.get("username")
            or ""
        ).strip()
        password = request.data.get("password", "")

        if not identifier or not password:
            return Response(
                {
                    "detail": "Username or email and password are required.",
                    "error": "missing_login_fields",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = UserProfile.objects.filter(
            Q(username__iexact=identifier)
            | Q(email__iexact=identifier)
        ).first()

        if not profile or not check_password(password, profile.password_hash):
            return Response(
                {
                    "detail": "Invalid username or password.",
                    "error": "invalid_credentials",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not profile.can_access_platform():
            return Response(
                {
                    "detail": "Subscription is inactive.",
                    "error": "subscription_inactive",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if profile.refresh_renewal_date_if_active():
            profile.save(update_fields=["fecha_renovacion"])

        return Response(
            {
                "id": profile.id,
                "username": profile.username,
                "email": profile.email,
                "display_name": profile.display_name,
                "estado": profile.estado,
                "fecha_renovacion": profile.fecha_renovacion,
                "onboarding_completed": profile.onboarding_completed,
                "onboarding_interests": profile.onboarding_interests,
                "onboarding_risk_profile": profile.onboarding_risk_profile,
                "onboarding_goal": profile.onboarding_goal,
                "selected_agent": profile.selected_agent,
            }
        )


class PasswordResetRequestView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request):
        email = (request.data.get("email") or "").strip()

        if not email:
            return Response(
                {
                    "detail": "Email is required.",
                    "error": "missing_email",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = UserProfile.objects.filter(email__iexact=email).first()

        if not profile:
            return Response(
                {
                    "detail": "User does not exist.",
                    "error": "user_not_found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        temporary_password = get_random_string(
            14,
            allowed_chars="abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789",
        )
        if not settings.DEBUG:
            send_mail(
                "Your FinancU temporary password",
                (
                    "We received a password reset request for your FinancU account.\n\n"
                    f"Temporary password: {temporary_password}\n\n"
                    "Sign in with this temporary password and update it from your profile settings."
                ),
                settings.DEFAULT_FROM_EMAIL,
                [profile.email],
                fail_silently=False,
            )

        profile.password_hash = make_password(temporary_password)
        profile.save(update_fields=["password_hash"])

        payload = {
            "message": "Temporary password generated.",
        }
        if settings.DEBUG:
            payload["temporary_password"] = temporary_password

        return Response(payload)
