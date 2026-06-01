from django.contrib import admin
from django.urls import path, include

api_urls = [
    path("users/", include("users.urls")),
    path("content/", include("content.urls")),
    path("markets/", include("markets.urls")),
    path("subscriptions/", include("subscriptions.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_urls)),
]
