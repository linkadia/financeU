from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, CourseViewSet, LessonViewSet

router = DefaultRouter()
router.register("articles", ArticleViewSet, basename="articles")
router.register("courses", CourseViewSet, basename="courses")
router.register("lessons", LessonViewSet, basename="lessons")

urlpatterns = [
    path("", include(router.urls)),
]
