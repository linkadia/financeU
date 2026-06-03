import hashlib

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
    options = serializers.SerializerMethodField()

    class Meta:
        model = LessonQuizQuestion
        fields = ["id", "question", "question_type", "explanation", "order", "is_active", "options"]

    def get_options(self, question):
        options = list(question.options.all())
        options.sort(key=lambda option: stable_option_sort_key(question.id, option.id))
        return PublicLessonQuizOptionSerializer(options, many=True).data


def stable_option_sort_key(question_id, option_id):
    key = f"{question_id}:{option_id}".encode("utf-8")
    return hashlib.sha256(key).hexdigest()


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
        questions = [question for question in quiz.questions.all() if question.is_active]
        if questions:
            return LessonQuizQuestionSerializer(questions, many=True).data

        legacy_options = [option for option in quiz.options.all() if option.question_id is None]
        legacy_options.sort(key=lambda option: stable_option_sort_key(f"legacy-{quiz.id}", option.id))
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
