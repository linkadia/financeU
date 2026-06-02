from django.urls import path

from .views import LatestSnapshotsView, ProductHistoryView, ProductListView

urlpatterns = [
    path("products/", ProductListView.as_view(), name="market-products"),
    path("snapshots/latest/", LatestSnapshotsView.as_view(), name="market-snapshots-latest"),
    path("products/<slug:slug>/history/", ProductHistoryView.as_view(), name="market-product-history"),
]
