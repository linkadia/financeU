from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FinancialProduct, FinancialProductSnapshot
from .serializers import (
    LatestMarketSnapshotSerializer,
    ProductMarketSerializer,
    SnapshotHistorySerializer,
)


def normalized_lang(request):
    return "pl" if request.query_params.get("lang") == "pl" else "en"


def filtered_active_products(request):
    queryset = FinancialProduct.objects.filter(is_active=True).order_by("display_order", "symbol")
    category = request.query_params.get("category")
    featured = request.query_params.get("featured")

    if category:
        queryset = queryset.filter(category=category.upper())

    if featured is not None:
        queryset = queryset.filter(is_featured=featured.lower() in {"1", "true", "yes"})

    return queryset


class ProductListView(APIView):
    throttle_classes = []

    def get(self, request):
        serializer = ProductMarketSerializer(
            filtered_active_products(request),
            many=True,
            context={"lang": normalized_lang(request)},
        )
        return Response(serializer.data)


class LatestSnapshotsView(APIView):
    throttle_classes = []

    def get(self, request):
        usable_statuses = [
            FinancialProductSnapshot.ValidationStatus.VALID,
            FinancialProductSnapshot.ValidationStatus.PARTIAL,
        ]
        snapshots = []

        for product in filtered_active_products(request):
            snapshot = (
                product.snapshots.filter(
                    validation_status__in=usable_statuses,
                    current_value__isnull=False,
                    effective_at_raw__isnull=False,
                )
                .order_by("-effective_datetime", "-effective_date", "-created_at")
                .first()
            )
            if snapshot is not None:
                snapshots.append(snapshot)

        serializer = LatestMarketSnapshotSerializer(
            snapshots,
            many=True,
            context={"lang": normalized_lang(request)},
        )
        return Response(serializer.data)


class ProductHistoryView(APIView):
    throttle_classes = []

    def get(self, request, slug):
        try:
            limit = int(request.query_params.get("limit", 100))
        except (TypeError, ValueError):
            limit = 100
        limit = max(1, min(limit, 500))

        queryset = FinancialProductSnapshot.objects.filter(
            product__slug=slug,
            product__is_active=True,
        ).select_related("product")

        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        if date_from:
            queryset = queryset.filter(effective_date__gte=date_from)

        if date_to:
            queryset = queryset.filter(effective_date__lte=date_to)

        queryset = queryset.order_by("-effective_date", "-created_at")[:limit]
        serializer = SnapshotHistorySerializer(
            queryset,
            many=True,
            context={"lang": normalized_lang(request)},
        )
        return Response(serializer.data)
