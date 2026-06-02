from rest_framework import serializers

from .models import (
    Course,
    CourseType,
    LearningCategory,
    LearningLevel,
    Lesson,
    LessonQuiz,
    LessonQuizOption,
    LessonQuizQuestion,
)


class LearningCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningCategory
        fields = ["id", "name", "slug", "description", "icon", "order", "is_active"]


class LearningLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningLevel
        fields = ["id", "name", "slug", "order", "is_active"]


class CourseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseType
        fields = ["id", "name", "slug", "description", "order", "is_active"]


class PublicLessonQuizOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonQuizOption
        fields = ["id", "text", "order"]


class LessonQuizQuestionSerializer(serializers.ModelSerializer):
    options = PublicLessonQuizOptionSerializer(many=True, read_only=True)

    class Meta:
        model = LessonQuizQuestion
        fields = ["id", "question", "question_type", "explanation", "order", "is_active", "options"]


class LessonQuizSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()

    class Meta:
        model = LessonQuiz
        fields = [
            "id",
            "title",
            "description",
            "question",
            "explanation",
            "passing_score",
            "is_required",
            "is_active",
            "questions",
        ]

    def get_questions(self, quiz):
        questions = list(quiz.questions.filter(is_active=True).order_by("order"))
        if questions:
            return LessonQuizQuestionSerializer(questions, many=True).data

        legacy_options = quiz.options.filter(question__isnull=True).order_by("order")
        return [
            {
                "id": f"legacy-{quiz.id}",
                "question": quiz.question,
                "explanation": quiz.explanation,
                "order": 1,
                "is_active": quiz.is_active,
                "options": PublicLessonQuizOptionSerializer(legacy_options, many=True).data,
            }
        ]


class LessonSerializer(serializers.ModelSerializer):
    quiz = LessonQuizSerializer(read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "content_type",
            "provider",
            "source_channel",
            "source_url",
            "external_url",
            "embed_url",
            "image_url",
            "content_language",
            "level",
            "category",
            "youtube_url",
            "youtube_video_id",
            "duration_minutes",
            "summary",
            "embed_allowed",
            "requires_disclaimer",
            "disclaimer",
            "order",
            "is_active",
            "quiz",
        ]


class CourseSerializer(serializers.ModelSerializer):
    category = LearningCategorySerializer(read_only=True)
    course_type = CourseTypeSerializer(read_only=True)
    level = LearningLevelSerializer(read_only=True)
    lessons = LessonSerializer(many=True, read_only=True)
    primary_content_type = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "provider",
            "source_type",
            "external_url",
            "language",
            "category",
            "course_type",
            "level",
            "thumbnail_url",
            "cover_image_url",
            "primary_content_type",
            "estimated_duration_minutes",
            "order",
            "is_required",
            "is_active",
            "lessons",
        ]

    def get_primary_content_type(self, course):
        first_lesson = next(iter(course.lessons.all()), None)
        return first_lesson.content_type if first_lesson else "article"
