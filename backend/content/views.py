from datetime import timedelta

from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import pagination, viewsets
from rest_framework.response import Response
from .models import NewsArticle
from .serializers import PublicNewsArticleSerializer


class NewsArticlePagination(pagination.PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50


@method_decorator(cache_page(300), name="list")
class NewsArticleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PublicNewsArticleSerializer
    pagination_class = NewsArticlePagination
    throttle_classes = []
    DATE_RANGE_CUTOFFS = {
        "24h": lambda: timezone.now() - timedelta(days=1),
        "week": lambda: timezone.now() - timedelta(days=7),
        "month": lambda: timezone.now() - timedelta(days=30),
        "year": lambda: timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
    }
    DATE_RANGE_FALLBACK_ORDER = ("24h", "week", "month", "year", "all")

    def apply_date_range(self, queryset, date_range):
        cutoff_factory = self.DATE_RANGE_CUTOFFS.get(date_range)
        if cutoff_factory:
            return queryset.filter(published_at__gte=cutoff_factory())
        return queryset

    def should_use_date_range_fallback(self):
        return self.request.query_params.get("date_range_fallback", "").lower() in {"1", "true", "yes"}

    def resolve_date_range(self, queryset, requested_range):
        if not self.should_use_date_range_fallback():
            return requested_range, self.apply_date_range(queryset, requested_range)

        try:
            start_index = self.DATE_RANGE_FALLBACK_ORDER.index(requested_range)
        except ValueError:
            start_index = 0

        fallback_ranges = self.DATE_RANGE_FALLBACK_ORDER[start_index:]
        for date_range in fallback_ranges:
            ranged_queryset = self.apply_date_range(queryset, date_range)
            if ranged_queryset.exists() or date_range == fallback_ranges[-1]:
                return date_range, ranged_queryset

        return requested_range, self.apply_date_range(queryset, requested_range)

    def get_queryset(self):
        queryset = NewsArticle.objects.all()
        news_types = self.request.query_params.get("news_type", "")
        status_filter = self.request.query_params.get("status", NewsArticle.Status.PUBLISHED)
        date_range = self.request.query_params.get("date_range", "24h")

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if news_types:
            queryset = queryset.filter(news_type__in=[
                item.strip()
                for item in news_types.split(",")
                if item.strip()
            ])

        self.effective_date_range, queryset = self.resolve_date_range(queryset, date_range)

        return queryset.order_by("-published_at")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data["effective_date_range"] = getattr(self, "effective_date_range", request.query_params.get("date_range", "24h"))
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "results": serializer.data,
            "effective_date_range": getattr(self, "effective_date_range", request.query_params.get("date_range", "24h")),
        })
