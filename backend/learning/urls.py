from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LearningCatalogViewSet, LearningProgressView, LessonSubmitView

router = DefaultRouter()
router.register("catalog", LearningCatalogViewSet, basename="learning-catalog")

urlpatterns = [
    path("progress/", LearningProgressView.as_view(), name="learning-progress"),
    path("lessons/<int:lesson_id>/submit/", LessonSubmitView.as_view(), name="learning-lesson-submit"),
    path("", include(router.urls)),
]
