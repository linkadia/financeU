from django.contrib import admin
from django.urls import path, include

api_urls = [
    path("users/", include("users.urls")),
    path("content/", include("content.urls")),
    path("learning/", include("learning.urls")),
    path("market/", include("marketdata.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_urls)),
]
