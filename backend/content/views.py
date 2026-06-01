from rest_framework import viewsets
from .models import Article, Course, Lesson
from .serializers import ArticleSerializer, CourseSerializer, LessonSerializer

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all().order_by("-published_at")
    serializer_class = ArticleSerializer


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all().order_by("order")
    serializer_class = LessonSerializer
