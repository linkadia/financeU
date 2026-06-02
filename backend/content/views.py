from rest_framework import viewsets
from .models import NewsArticle
from .serializers import NewsArticleSerializer


class NewsArticleViewSet(viewsets.ModelViewSet):
    serializer_class = NewsArticleSerializer
    throttle_classes = []

    def get_queryset(self):
        queryset = NewsArticle.objects.all().order_by("-published_at")
        news_types = self.request.query_params.get("news_type", "")
        status_filter = self.request.query_params.get("status", NewsArticle.Status.PUBLISHED)

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if news_types:
            queryset = queryset.filter(news_type__in=[
                item.strip()
                for item in news_types.split(",")
                if item.strip()
            ])

        return queryset
