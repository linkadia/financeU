from django.urls import path

from .views import CookieConsentRecordView

urlpatterns = [
    path("cookie-consents/", CookieConsentRecordView.as_view(), name="cookie-consent-records"),
]
