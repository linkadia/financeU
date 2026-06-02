from django.contrib import admin

from .models import (
    Course,
    CourseType,
    LearningCategory,
    LearningLevel,
    Lesson,
    LessonQuiz,
    LessonQuizQuestion,
    LessonQuizOption,
    UserCourseProgress,
    UserLessonProgress,
)


@admin.register(LearningCategory)
class LearningCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "is_active")
    list_editable = ("order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")


@admin.register(CourseType)
class CourseTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "is_active")
    list_editable = ("order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")


@admin.register(LearningLevel)
class LearningLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "is_active")
    list_editable = ("order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = (
        "title",
        "slug",
        "content_type",
        "provider",
        "embed_allowed",
        "requires_disclaimer",
        "duration_minutes",
        "order",
        "is_active",
    )
    prepopulated_fields = {"slug": ("title",)}
    show_change_link = True


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "provider",
        "source_type",
        "category",
        "course_type",
        "level",
        "language",
        "estimated_duration_minutes",
        "order",
        "is_active",
    )
    list_filter = ("language", "source_type", "category", "course_type", "level", "is_active")
    list_editable = ("order", "is_active")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "description")
    inlines = [LessonInline]


class LessonQuizOptionInline(admin.TabularInline):
    model = LessonQuizOption
    extra = 4
    fields = ("question", "text", "is_correct", "order")


class LessonQuizQuestionInline(admin.TabularInline):
    model = LessonQuizQuestion
    extra = 0
    fields = ("question", "explanation", "order", "is_active")
    show_change_link = True


@admin.register(LessonQuiz)
class LessonQuizAdmin(admin.ModelAdmin):
    list_display = ("lesson", "passing_score", "is_required", "is_active", "created_at", "updated_at")
    list_filter = ("is_required", "is_active", "lesson__course")
    search_fields = ("lesson__title", "question", "explanation")
    autocomplete_fields = ("lesson",)
    inlines = [LessonQuizQuestionInline, LessonQuizOptionInline]


class LessonQuizInline(admin.StackedInline):
    model = LessonQuiz
    extra = 0
    show_change_link = True


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "course",
        "content_type",
        "provider",
        "embed_allowed",
        "requires_disclaimer",
        "duration_minutes",
        "order",
        "is_active",
    )
    list_filter = ("course", "content_type", "embed_allowed", "requires_disclaimer", "is_active")
    list_editable = ("order", "is_active")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "description", "summary", "youtube_video_id", "provider")
    autocomplete_fields = ("course",)
    inlines = [LessonQuizInline]


@admin.register(LessonQuizQuestion)
class LessonQuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("question", "quiz", "question_type", "order", "is_active")
    list_filter = ("question_type", "is_active", "quiz__lesson__course")
    list_editable = ("order", "is_active")
    search_fields = ("question", "explanation", "quiz__lesson__title")
    autocomplete_fields = ("quiz",)
    inlines = [LessonQuizOptionInline]


@admin.register(LessonQuizOption)
class LessonQuizOptionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz", "question", "is_correct", "order")
    list_filter = ("is_correct", "quiz__lesson__course")
    list_editable = ("is_correct", "order")
    search_fields = ("text", "question__question", "quiz__question", "quiz__lesson__title")
    autocomplete_fields = ("quiz", "question")


@admin.register(UserLessonProgress)
class UserLessonProgressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "lesson",
        "status",
        "quiz_answered_correctly",
        "attempts",
        "selected_options",
        "started_at",
        "completed_at",
    )
    list_filter = (
        "status",
        "quiz_answered_correctly",
        "lesson__course",
        "completed_at",
    )
    search_fields = ("user__username", "user__email", "lesson__title")
    autocomplete_fields = ("user", "lesson", "selected_option")
    readonly_fields = ("started_at", "completed_at", "last_watched_at")


@admin.register(UserCourseProgress)
class UserCourseProgressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "course",
        "progress_percentage",
        "completed_lessons_count",
        "total_lessons_count",
        "started_at",
        "completed_at",
    )
    list_filter = ("course", "completed_at")
    search_fields = ("user__username", "user__email", "course__title")
    autocomplete_fields = ("user", "course")
    readonly_fields = (
        "progress_percentage",
        "completed_lessons_count",
        "total_lessons_count",
        "started_at",
        "completed_at",
    )

    actions = ["recalculate_selected"]

    @admin.action(description="Recalculate selected progress records")
    def recalculate_selected(self, request, queryset):
        for progress in queryset.select_related("user", "course"):
            progress.recalculate(save=True)
