from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone


class LearningCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=80, blank=True)
    order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "learning category"
        verbose_name_plural = "learning categories"
        indexes = [
            models.Index(fields=["is_active", "order"]),
        ]

    def __str__(self):
        return self.name


class CourseType(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["order", "name"]
        indexes = [
            models.Index(fields=["is_active", "order"]),
        ]

    def __str__(self):
        return self.name


class LearningLevel(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["order", "name"]
        indexes = [
            models.Index(fields=["is_active", "order"]),
        ]

    def __str__(self):
        return self.name


class Course(models.Model):
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        LearningCategory,
        related_name="courses",
        on_delete=models.PROTECT,
    )
    course_type = models.ForeignKey(
        CourseType,
        related_name="courses",
        on_delete=models.PROTECT,
    )
    level = models.ForeignKey(
        LearningLevel,
        related_name="courses",
        on_delete=models.PROTECT,
    )
    thumbnail_url = models.URLField(max_length=500, blank=True)
    estimated_duration_minutes = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "title"]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "course_type", "level", "title"],
                name="unique_learning_course_taxonomy_title",
            ),
        ]
        indexes = [
            models.Index(fields=["is_active", "category", "level", "course_type"]),
            models.Index(fields=["category", "order"]),
        ]

    def __str__(self):
        return self.title

    @property
    def total_lessons(self):
        return self.lessons.filter(is_active=True).count()

    def get_progress_for_user(self, user):
        progress, _ = UserCourseProgress.objects.get_or_create(
            user=user,
            course=self,
        )
        return progress.recalculate(save=True)


class Lesson(models.Model):
    course = models.ForeignKey(Course, related_name="lessons", on_delete=models.CASCADE)
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200)
    description = models.TextField(blank=True)
    youtube_url = models.URLField(max_length=500)
    youtube_video_id = models.CharField(max_length=32, db_index=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    summary = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["course", "order", "title"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "slug"],
                name="unique_learning_lesson_slug_per_course",
            ),
            models.UniqueConstraint(
                fields=["course", "order"],
                name="unique_learning_lesson_order_per_course",
            ),
        ]
        indexes = [
            models.Index(fields=["course", "is_active", "order"]),
        ]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class LessonQuiz(models.Model):
    lesson = models.OneToOneField(
        Lesson,
        related_name="quiz",
        on_delete=models.CASCADE,
    )
    question = models.TextField()
    explanation = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["lesson__course", "lesson__order"]
        verbose_name = "lesson quiz"
        verbose_name_plural = "lesson quizzes"

    def __str__(self):
        return f"Quiz: {self.lesson.title}"


class LessonQuizOption(models.Model):
    quiz = models.ForeignKey(
        LessonQuiz,
        related_name="options",
        on_delete=models.CASCADE,
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False, db_index=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["quiz", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["quiz", "order"],
                name="unique_learning_quiz_option_order",
            ),
            models.UniqueConstraint(
                fields=["quiz"],
                condition=Q(is_correct=True),
                name="unique_learning_correct_option_per_quiz",
            ),
        ]

    def __str__(self):
        return self.text


class UserLessonProgress(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="learning_lesson_progress",
        on_delete=models.CASCADE,
    )
    lesson = models.ForeignKey(
        Lesson,
        related_name="user_progress",
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED,
        db_index=True,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_watched_at = models.DateTimeField(null=True, blank=True)
    quiz_answered_correctly = models.BooleanField(default=False)
    selected_option = models.ForeignKey(
        LessonQuizOption,
        related_name="selected_by_progress",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    attempts = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["user", "lesson__course", "lesson__order"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "lesson"],
                name="unique_learning_user_lesson_progress",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status="completed", quiz_answered_correctly=True)
                    | ~Q(status="completed")
                ),
                name="completed_lesson_requires_correct_quiz",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "lesson"]),
            models.Index(fields=["lesson", "status"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.lesson} - {self.status}"

    def clean(self):
        if self.selected_option and self.selected_option.quiz.lesson_id != self.lesson_id:
            raise ValidationError(
                {"selected_option": "Selected option must belong to this lesson quiz."}
            )
        if self.status == self.Status.COMPLETED and not self.quiz_answered_correctly:
            raise ValidationError("A lesson can only be completed after a correct quiz.")

    def mark_completed(self, selected_option=None, save=True):
        if selected_option is not None:
            self.selected_option = selected_option

        if not self.selected_option:
            raise ValidationError("A selected quiz option is required to complete a lesson.")
        if self.selected_option.quiz.lesson_id != self.lesson_id:
            raise ValidationError("Selected option must belong to this lesson quiz.")
        if not self.selected_option.is_correct:
            self.attempts += 1
            self.quiz_answered_correctly = False
            if save:
                self.save(update_fields=["selected_option", "attempts", "quiz_answered_correctly"])
            raise ValidationError("The selected quiz option is not correct.")

        now = timezone.now()
        self.quiz_answered_correctly = True
        self.status = self.Status.COMPLETED
        self.started_at = self.started_at or now
        self.completed_at = self.completed_at or now
        self.last_watched_at = now
        self.attempts += 1

        if save:
            with transaction.atomic():
                self.full_clean()
                self.save()
                course_progress, _ = UserCourseProgress.objects.get_or_create(
                    user=self.user,
                    course=self.lesson.course,
                )
                course_progress.recalculate(save=True)
        return self

    @classmethod
    def get_global_progress_for_user(cls, user):
        active_lessons = Lesson.objects.filter(is_active=True, course__is_active=True)
        total = active_lessons.count()
        completed = cls.objects.filter(
            user=user,
            lesson__in=active_lessons,
            status=cls.Status.COMPLETED,
            quiz_answered_correctly=True,
        ).count()

        return {
            "completed_lessons_count": completed,
            "total_lessons_count": total,
            "progress_percentage": round((completed / total) * 100, 2) if total else 0,
        }


class UserCourseProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="learning_course_progress",
        on_delete=models.CASCADE,
    )
    course = models.ForeignKey(
        Course,
        related_name="user_progress",
        on_delete=models.CASCADE,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )
    completed_lessons_count = models.PositiveIntegerField(default=0)
    total_lessons_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["user", "course__order", "course__title"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "course"],
                name="unique_learning_user_course_progress",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "course"]),
            models.Index(fields=["user", "progress_percentage"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.course} - {self.progress_percentage}%"

    def recalculate(self, save=True):
        active_lessons = self.course.lessons.filter(is_active=True)
        total = active_lessons.count()
        completed = UserLessonProgress.objects.filter(
            user=self.user,
            lesson__in=active_lessons,
            status=UserLessonProgress.Status.COMPLETED,
            quiz_answered_correctly=True,
        ).count()

        self.total_lessons_count = total
        self.completed_lessons_count = completed
        self.progress_percentage = (
            (Decimal(completed) / Decimal(total) * Decimal("100")).quantize(Decimal("0.01"))
            if total
            else Decimal("0.00")
        )

        if completed > 0:
            self.started_at = self.started_at or timezone.now()
        if total > 0 and completed == total:
            self.completed_at = self.completed_at or timezone.now()
        else:
            self.completed_at = None

        if save:
            self.save()
        return self
