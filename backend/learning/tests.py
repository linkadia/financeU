from django.core.management import call_command
from django.test import TestCase

from users.models import UserProfile

from .models import (
    Course,
    Lesson,
    LessonQuiz,
    LessonQuizQuestion,
    UserCourseProgress,
    UserLessonProgress,
)


class LearningSeedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_learning_content", verbosity=0)

    def test_seed_creates_external_courses_without_duplicates(self):
        first_counts = (Course.objects.count(), Lesson.objects.count(), LessonQuiz.objects.count())

        call_command("seed_learning_content", verbosity=0)

        self.assertEqual(first_counts, (Course.objects.count(), Lesson.objects.count(), LessonQuiz.objects.count()))
        self.assertTrue(Course.objects.filter(language="en", external_url__icontains="khanacademy.org").exists())
        self.assertTrue(Course.objects.filter(language="pl", external_url__icontains="nbp.pl").exists())

    def test_each_seeded_lesson_has_required_three_question_quiz(self):
        for lesson in Lesson.objects.select_related("quiz").filter(external_url__gt=""):
            self.assertTrue(lesson.quiz.is_required)
            self.assertEqual(lesson.quiz.passing_score, 100)
            self.assertEqual(lesson.quiz.questions.filter(is_active=True).count(), 3)
            for question in lesson.quiz.questions.all():
                self.assertEqual(question.options.count(), 3)
                self.assertEqual(question.options.filter(is_correct=True).count(), 1)

    def test_catalog_can_filter_by_language_category_and_level(self):
        queryset = Course.objects.filter(language="pl", category__slug="crypto", level__slug="beginner")

        self.assertTrue(queryset.exists())
        self.assertTrue(all(course.language == "pl" for course in queryset))
        self.assertTrue(all(course.category.slug == "crypto" for course in queryset))
        self.assertTrue(all(course.level.slug == "beginner" for course in queryset))


class LearningProgressTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_learning_content", verbosity=0)
        cls.user = UserProfile.objects.create(
            username="learning-user",
            email="learning-user@example.com",
        )

    def test_course_progress_counts_completed_lessons(self):
        course = Course.objects.prefetch_related("lessons").filter(language="en").first()
        lesson = course.lessons.first()
        question = LessonQuizQuestion.objects.filter(quiz=lesson.quiz).first()
        selected_option = question.options.get(is_correct=True)

        progress = UserLessonProgress.objects.create(
            user=self.user,
            lesson=lesson,
            status=UserLessonProgress.Status.COMPLETED,
            quiz_answered_correctly=True,
            selected_option=selected_option,
            selected_options={str(question.id): selected_option.id},
            attempts=1,
        )
        self.assertEqual(progress.status, UserLessonProgress.Status.COMPLETED)

        course_progress, _ = UserCourseProgress.objects.get_or_create(user=self.user, course=course)
        course_progress.recalculate(save=True)

        self.assertEqual(course_progress.completed_lessons_count, 1)
        self.assertEqual(course_progress.total_lessons_count, course.lessons.filter(is_active=True).count())
        self.assertGreater(course_progress.progress_percentage, 0)
