from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.throttling import BaseThrottle, ScopedRateThrottle
from rest_framework.views import APIView

from .models import CookieConsentRecord, mask_ip_address
from .serializers import CookieConsentRecordSerializer


class CookieConsentRecordView(APIView):
    # The banner is shown before login, so no authentication (and no CSRF
    # check from a leftover admin session) applies to this endpoint.
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "cookie_consent"

    def post(self, request):
        serializer = CookieConsentRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        event_id = values.pop("event_id")
        # The unique database constraint also protects concurrent retries across workers.
        record, created = CookieConsentRecord.objects.get_or_create(
            event_id=event_id,
            defaults={
                **values,
                "ip_address": mask_ip_address(BaseThrottle().get_ident(request)),
                "user_agent": request.headers.get("User-Agent", "")[:512],
            },
        )
        if not created and any(getattr(record, field) != value for field, value in values.items()):
            return Response(
                {"detail": "Event ID is already used for a different consent decision."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            CookieConsentRecordSerializer(record).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
