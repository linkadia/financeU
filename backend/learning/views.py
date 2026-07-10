from django.core.cache import cache
from django.db.models import Prefetch
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import UserProfile

from .models import (
    Course,
    Lesson,
    LessonQuizOption,
    LessonQuizQuestion,
    UserCourseProgress,
    UserLessonProgress,
)
from .serializers import CourseSerializer


class LearningCatalogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CourseSerializer
    throttle_classes = []
    PUBLIC_CATALOG_CACHE_SECONDS = 300

    def get_queryset(self):
        language = self.request.query_params.get("language", "en")
        if language not in {"en", "pl"}:
            language = "en"

        question_options = Prefetch(
            "options",
            queryset=LessonQuizOption.objects.order_by("order"),
        )
        questions = Prefetch(
            "quiz__questions",
            queryset=LessonQuizQuestion.objects.filter(is_active=True)
            .prefetch_related(question_options)
            .order_by("order"),
        )
        lessons = Prefetch(
            "lessons",
            queryset=Lesson.objects.filter(is_active=True)
            .select_related("quiz", "category", "level")
            .prefetch_related(
                questions,
                Prefetch(
                    "quiz__options",
                    queryset=LessonQuizOption.objects.filter(question__isnull=True).order_by("order"),
                ),
            )
            .order_by("order"),
        )

        queryset = (
            Course.objects.filter(language=language, is_active=True)
            .select_related("category", "course_type", "level")
            .prefetch_related(lessons)
            .order_by("order", "title")
        )

        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__slug=category)

        level = self.request.query_params.get("level")
        if level:
            queryset = queryset.filter(level__slug=level)

        return queryset

    @action(detail=False, methods=["get"], url_path="catalog")
    def catalog(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            language = request.query_params.get("language", "en")
            if language not in {"en", "pl"}:
                language = "en"
            category = request.query_params.get("category", "")
            level = request.query_params.get("level", "")
            cache_key = f"learning:catalog:v1:{language}:{category}:{level}"
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return Response(cached_data)

        courses = list(self.get_queryset())
        data = self.get_serializer(courses, many=True).data

        if user_id:
            user = UserProfile.objects.filter(id=user_id).first()
            if user:
                progress = {
                    item.lesson_id: item
                    for item in UserLessonProgress.objects.filter(user=user, lesson__course__in=courses)
                }
                course_progress = {
                    item.course_id: item
                    for item in UserCourseProgress.objects.filter(user=user, course__in=courses)
                }

                for course_data, course in zip(data, courses):
                    active_lessons = list(course.lessons.all())
                    total_lessons = len(active_lessons)
                    course_progress_item = course_progress.get(course.id)
                    course_data["progress"] = {
                        "progress_percentage": course_progress_item.progress_percentage if course_progress_item else 0,
                        "completed_lessons_count": course_progress_item.completed_lessons_count if course_progress_item else 0,
                        "total_lessons_count": course_progress_item.total_lessons_count if course_progress_item else total_lessons,
                        "completed_at": course_progress_item.completed_at if course_progress_item else None,
                    }

                    previous_completed = True
                    for lesson_data, lesson in zip(course_data["lessons"], active_lessons):
                        lesson_progress = progress.get(lesson.id)
                        completed = (
                            lesson_progress
                            and lesson_progress.status == UserLessonProgress.Status.COMPLETED
                            and lesson_progress.quiz_answered_correctly
                        )
                        lesson_data["progress"] = {
                            "status": lesson_progress.status if lesson_progress else UserLessonProgress.Status.NOT_STARTED,
                            "attempts": lesson_progress.attempts if lesson_progress else 0,
                            "quiz_answered_correctly": bool(lesson_progress and lesson_progress.quiz_answered_correctly),
                            "completed_at": lesson_progress.completed_at if lesson_progress else None,
                        }
                        lesson_data["availability_status"] = (
                            "completed" if completed else "available" if previous_completed else "locked"
                        )
                        previous_completed = previous_completed and bool(completed)
        else:
            cache.set(cache_key, data, self.PUBLIC_CATALOG_CACHE_SECONDS)

        return Response(data)


def get_user_from_request(request):
    user_id = request.query_params.get("user_id") or request.data.get("user_id")
    if not user_id:
        return None, Response(
            {"detail": "user_id is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = UserProfile.objects.filter(id=user_id).first()
    if not user:
        return None, Response(
            {"detail": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    return user, None


def serialize_global_progress(user):
    return UserLessonProgress.get_global_progress_for_user(user)


class LearningProgressView(APIView):
    throttle_classes = []

    def get(self, request):
        user, error = get_user_from_request(request)
        if error:
            return error

        lesson_progress = UserLessonProgress.objects.filter(user=user).select_related("lesson")
        course_progress = UserCourseProgress.objects.filter(user=user).select_related("course")

        return Response(
            {
                "lessons": {
                    str(item.lesson_id): {
                        "status": item.status,
                        "attempts": item.attempts,
                        "selected_options": item.selected_options,
                        "quiz_answered_correctly": item.quiz_answered_correctly,
                        "completed_at": item.completed_at,
                    }
                    for item in lesson_progress
                },
                "courses": {
                    str(item.course_id): {
                        "progress_percentage": item.progress_percentage,
                        "completed_lessons_count": item.completed_lessons_count,
                        "total_lessons_count": item.total_lessons_count,
                        "completed_at": item.completed_at,
                    }
                    for item in course_progress
                },
                "global": serialize_global_progress(user),
            }
        )


class LessonSubmitView(APIView):
    throttle_classes = []

    def post(self, request, lesson_id):
        user, error = get_user_from_request(request)
        if error:
            return error

        answers = request.data.get("answers", {})
        if not isinstance(answers, dict) or not answers:
            return Response(
                {"detail": "answers must be a non-empty object."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lesson = (
            Lesson.objects.filter(id=lesson_id, is_active=True, course__is_active=True)
            .select_related("course", "quiz")
            .first()
        )
        if not lesson:
            return Response(
                {"detail": "Lesson not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        questions = list(
            LessonQuizQuestion.objects.filter(quiz=lesson.quiz, is_active=True)
            .prefetch_related("options")
            .order_by("order")
        )
        if not questions:
            return Response(
                {"detail": "Lesson does not have an active exam."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        feedback = {}
        selected_options = {}
        all_correct = True

        for question in questions:
            selected_option_id = answers.get(str(question.id)) or answers.get(question.id)
            selected_options[str(question.id)] = selected_option_id
            option = next(
                (
                    candidate
                    for candidate in question.options.all()
                    if str(candidate.id) == str(selected_option_id)
                ),
                None,
            )
            is_correct = bool(option and option.is_correct)
            feedback[str(question.id)] = {"correct": is_correct}
            all_correct = all_correct and is_correct

        progress, _ = UserLessonProgress.objects.get_or_create(user=user, lesson=lesson)
        progress.started_at = progress.started_at or timezone.now()
        progress.last_watched_at = timezone.now()
        progress.attempts += 1
        progress.selected_options = selected_options
        progress.quiz_answered_correctly = all_correct

        first_selected_option_id = next(
            (value for value in selected_options.values() if value),
            None,
        )
        progress.selected_option = (
            LessonQuizOption.objects.filter(id=first_selected_option_id).first()
            if first_selected_option_id
            else None
        )

        if all_correct:
            progress.status = UserLessonProgress.Status.COMPLETED
            progress.completed_at = progress.completed_at or timezone.now()
        else:
            progress.status = UserLessonProgress.Status.IN_PROGRESS
            progress.completed_at = None

        progress.full_clean()
        progress.save()

        course_progress, _ = UserCourseProgress.objects.get_or_create(
            user=user,
            course=lesson.course,
        )
        course_progress.recalculate(save=True)

        return Response(
            {
                "lesson_id": lesson.id,
                "status": progress.status,
                "attempts": progress.attempts,
                "quiz_answered_correctly": progress.quiz_answered_correctly,
                "completed_at": progress.completed_at,
                "feedback": feedback,
                "selected_options": progress.selected_options,
                "course_progress": {
                    "course_id": lesson.course_id,
                    "progress_percentage": course_progress.progress_percentage,
                    "completed_lessons_count": course_progress.completed_lessons_count,
                    "total_lessons_count": course_progress.total_lessons_count,
                    "completed_at": course_progress.completed_at,
                },
                "global": serialize_global_progress(user),
            }
        )
