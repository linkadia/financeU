from datetime import timedelta

from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import pagination, viewsets
from .models import NewsArticle
from .serializers import PublicNewsArticleSerializer


class NewsArticlePagination(pagination.PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50


@method_decorator(cache_page(60), name="list")
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

        cutoff_factory = self.DATE_RANGE_CUTOFFS.get(date_range)
        if cutoff_factory:
            queryset = queryset.filter(published_at__gte=cutoff_factory())

        return queryset.order_by("-published_at")
