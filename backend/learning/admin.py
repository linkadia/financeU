from django.contrib import admin

from .models import (
    Course,
    CourseType,
    LearningCategory,
    LearningLevel,
    Lesson,
    LessonQuiz,
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
        "youtube_video_id",
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
        "category",
        "course_type",
        "level",
        "estimated_duration_minutes",
        "order",
        "is_active",
    )
    list_filter = ("category", "course_type", "level", "is_active")
    list_editable = ("order", "is_active")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "description")
    inlines = [LessonInline]


class LessonQuizOptionInline(admin.TabularInline):
    model = LessonQuizOption
    extra = 4
    fields = ("text", "is_correct", "order")


@admin.register(LessonQuiz)
class LessonQuizAdmin(admin.ModelAdmin):
    list_display = ("lesson", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "lesson__course")
    search_fields = ("lesson__title", "question", "explanation")
    autocomplete_fields = ("lesson",)
    inlines = [LessonQuizOptionInline]


class LessonQuizInline(admin.StackedInline):
    model = LessonQuiz
    extra = 0
    show_change_link = True


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "course",
        "youtube_video_id",
        "duration_minutes",
        "order",
        "is_active",
    )
    list_filter = ("course", "is_active")
    list_editable = ("order", "is_active")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "description", "summary", "youtube_video_id")
    autocomplete_fields = ("course",)
    inlines = [LessonQuizInline]


@admin.register(LessonQuizOption)
class LessonQuizOptionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz", "is_correct", "order")
    list_filter = ("is_correct", "quiz__lesson__course")
    list_editable = ("is_correct", "order")
    search_fields = ("text", "quiz__question", "quiz__lesson__title")
    autocomplete_fields = ("quiz",)


@admin.register(UserLessonProgress)
class UserLessonProgressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "lesson",
        "status",
        "quiz_answered_correctly",
        "attempts",
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
