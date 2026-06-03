from datetime import timedelta

from django.utils import timezone
from rest_framework import viewsets
from .models import NewsArticle
from .serializers import NewsArticleSerializer


class NewsArticleViewSet(viewsets.ModelViewSet):
    serializer_class = NewsArticleSerializer
    throttle_classes = []
    DATE_RANGE_CUTOFFS = {
        "24h": lambda: timezone.now() - timedelta(days=1),
        "week": lambda: timezone.now() - timedelta(days=7),
        "month": lambda: timezone.now() - timedelta(days=30),
        "year": lambda: timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
    }

    def get_queryset(self):
        queryset = NewsArticle.objects.all().order_by("-published_at")
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

        return queryset
