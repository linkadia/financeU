import React, { useEffect, useMemo, useState } from "react";
import TopBar from "../components/layout/TopBar";
import BottomNav from "../components/layout/BottomNav";
import GlassCard from "../components/ui/GlassCard";
import { getCourseTypes, getCourses, getLearningCategories, getLearningLevels } from "../data/localizedCourses";
import { useI18n } from "../i18n/I18nContext";

const STORAGE_KEY = "finan3_learning_progress";

function loadProgress() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch {
    return {};
  }
}

function getCourseProgress(course, progress) {
  const activeLessons = course.lessons.filter((lesson) => lesson.is_active);
  const completed = activeLessons.filter((lesson) => progress[lesson.id]?.status === "completed").length;
  const total = activeLessons.length;

  return {
    completed,
    total,
    percentage: total ? Math.round((completed / total) * 100) : 0
  };
}

function FilterChip({ active, children, onClick }) {
  return (
    <button
      className={`shrink-0 rounded-lg border px-3 py-2 text-label-sm transition-all active:scale-95 ${
        active
          ? "border-primary bg-primary text-on-primary"
          : "border-white/10 bg-surface-container text-on-surface-variant"
      }`}
      onClick={onClick}
      type="button"
    >
      {children}
    </button>
  );
}

function LessonStatusIcon({ completed, active }) {
  if (completed) {
    return (
      <span className="material-symbols-outlined text-secondary" style={{ fontVariationSettings: "'FILL' 1" }}>
        check_circle
      </span>
    );
  }

  return (
    <span className={`material-symbols-outlined ${active ? "text-primary" : "text-on-surface-variant"}`}>
      play_circle
    </span>
  );
}

export default function Learn() {
  const { language, t } = useI18n();
  const courses = useMemo(() => getCourses(language), [language]);
  const learningCategories = useMemo(() => getLearningCategories(language), [language]);
  const learningLevels = useMemo(() => getLearningLevels(language), [language]);
  const courseTypes = useMemo(() => getCourseTypes(language), [language]);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedLevel, setSelectedLevel] = useState("all");
  const [selectedType, setSelectedType] = useState("all");
  const [progress, setProgress] = useState(loadProgress);
  const [activeCourseId, setActiveCourseId] = useState(courses[0]?.id);
  const [activeLessonId, setActiveLessonId] = useState(courses[0]?.lessons[0]?.id);
  const [selectedOptionId, setSelectedOptionId] = useState(null);
  const [quizResult, setQuizResult] = useState(null);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
  }, [progress]);

  const filteredCourses = useMemo(() => {
    return courses.filter((course) => {
      return (
        course.is_active &&
        (selectedCategory === "all" || course.category.slug === selectedCategory) &&
        (selectedLevel === "all" || course.level.slug === selectedLevel) &&
        (selectedType === "all" || course.course_type.slug === selectedType)
      );
    });
  }, [selectedCategory, selectedLevel, selectedType]);

  const activeCourse = courses.find((course) => course.id === activeCourseId) || filteredCourses[0] || courses[0];
  const activeLesson =
    activeCourse?.lessons.find((lesson) => lesson.id === activeLessonId) || activeCourse?.lessons[0];

  const globalProgress = useMemo(() => {
    const allLessons = courses.flatMap((course) =>
      course.is_active ? course.lessons.filter((lesson) => lesson.is_active) : []
    );
    const completed = allLessons.filter((lesson) => progress[lesson.id]?.status === "completed").length;

    return {
      completed,
      total: allLessons.length,
      percentage: allLessons.length ? Math.round((completed / allLessons.length) * 100) : 0
    };
  }, [progress]);

  const activeCourseProgress = activeCourse ? getCourseProgress(activeCourse, progress) : null;
  const activeLessonProgress = activeLesson ? progress[activeLesson.id] : null;
  const isCompleted = activeLessonProgress?.status === "completed";

  const selectCourse = (course) => {
    setActiveCourseId(course.id);
    setActiveLessonId(course.lessons[0]?.id);
    setSelectedOptionId(null);
    setQuizResult(null);
  };

  const selectLesson = (lesson) => {
    setActiveLessonId(lesson.id);
    setSelectedOptionId(null);
    setQuizResult(null);
    setProgress((current) => ({
      ...current,
      [lesson.id]: {
        status: current[lesson.id]?.status === "completed" ? "completed" : "in_progress",
        attempts: current[lesson.id]?.attempts || 0,
        selected_option: current[lesson.id]?.selected_option || null
      }
    }));
  };

  const submitAnswer = () => {
    const selectedOption = activeLesson.quiz.options.find((option) => option.id === selectedOptionId);
    if (!selectedOption) return;

    const currentProgress = progress[activeLesson.id] || { attempts: 0 };
    const attempts = currentProgress.attempts + 1;

    if (!selectedOption.is_correct) {
      setQuizResult("wrong");
      setProgress((current) => ({
        ...current,
        [activeLesson.id]: {
          ...current[activeLesson.id],
          status: "in_progress",
          attempts,
          selected_option: selectedOption.id,
          quiz_answered_correctly: false
        }
      }));
      return;
    }

    setQuizResult("correct");
    setProgress((current) => ({
      ...current,
      [activeLesson.id]: {
        status: "completed",
        attempts,
        selected_option: selectedOption.id,
        quiz_answered_correctly: true,
        completed_at: new Date().toISOString()
      }
    }));
  };

  return (
    <div className="min-h-screen bg-background pb-24 text-on-surface selection:bg-primary-container/30">
      <TopBar />

      <main className="mx-auto max-w-md pb-32 pt-20">
        <section className="px-container-padding pb-stack-md pt-stack-lg">
          <div className="mb-stack-md flex items-end justify-between gap-stack-md">
            <div>
              <p className="mb-1 text-label-sm uppercase text-primary">{t('learn.learning')}</p>
              <h1 className="font-headline-lg-mobile text-headline-lg-mobile tracking-normal">
                {t('learn.financeLessons')}
              </h1>
            </div>
            <div className="text-right">
              <p className="font-mono-data text-[22px] text-secondary">{globalProgress.percentage}%</p>
              <p className="text-label-sm text-on-surface-variant">
                {globalProgress.completed}/{globalProgress.total} {t('learn.done')}
              </p>
            </div>
          </div>

          <GlassCard className="p-stack-md">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-label-sm text-on-surface-variant">{t('learn.globalProgress')}</span>
              <span className="font-mono-data text-label-sm">{globalProgress.percentage}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-white/5">
              <div className="h-full rounded-full bg-secondary" style={{ width: `${globalProgress.percentage}%` }} />
            </div>
          </GlassCard>
        </section>

        <section className="space-y-stack-sm px-container-padding pb-stack-md">
          <div className="flex gap-gutter overflow-x-auto pb-1 hide-scrollbar">
            <FilterChip active={selectedCategory === "all"} onClick={() => setSelectedCategory("all")}>
              {t('learn.allTopics')}
            </FilterChip>
            {learningCategories.map((category) => (
              <FilterChip
                active={selectedCategory === category.slug}
                key={category.id}
                onClick={() => setSelectedCategory(category.slug)}
              >
                {category.name}
              </FilterChip>
            ))}
          </div>
          <div className="flex gap-gutter overflow-x-auto pb-1 hide-scrollbar">
            <FilterChip active={selectedLevel === "all"} onClick={() => setSelectedLevel("all")}>
              {t('learn.allLevels')}
            </FilterChip>
            {learningLevels.map((level) => (
              <FilterChip
                active={selectedLevel === level.slug}
                key={level.id}
                onClick={() => setSelectedLevel(level.slug)}
              >
                {level.name}
              </FilterChip>
            ))}
          </div>
          <div className="flex gap-gutter overflow-x-auto pb-1 hide-scrollbar">
            <FilterChip active={selectedType === "all"} onClick={() => setSelectedType("all")}>
              {t('learn.allFormats')}
            </FilterChip>
            {courseTypes.map((type) => (
              <FilterChip
                active={selectedType === type.slug}
                key={type.id}
                onClick={() => setSelectedType(type.slug)}
              >
                {type.name}
              </FilterChip>
            ))}
          </div>
        </section>

        <section className="mb-stack-lg">
          <div className="mb-stack-md flex items-center justify-between px-container-padding">
            <h2 className="font-title-md text-title-md">{t('learn.courses')}</h2>
            <span className="text-label-sm text-on-surface-variant">{filteredCourses.length} {t('learn.available')}</span>
          </div>
          <div className="flex gap-gutter overflow-x-auto px-container-padding pb-1 hide-scrollbar">
            {filteredCourses.map((course) => {
              const courseProgress = getCourseProgress(course, progress);
              const isActive = course.id === activeCourse?.id;

              return (
                <button
                  className={`min-w-[236px] overflow-hidden rounded-xl border bg-surface-container text-left transition-all active:scale-[0.98] ${
                    isActive ? "border-primary" : "border-white/10"
                  }`}
                  key={course.id}
                  onClick={() => selectCourse(course)}
                  type="button"
                >
                  <div className="relative aspect-video bg-surface-container-high">
                    <img alt="" className="h-full w-full object-cover" src={course.thumbnail_url} />
                    <div className="absolute left-2 top-2 flex items-center gap-1 rounded-lg bg-black/70 px-2 py-1">
                      <span className="material-symbols-outlined text-[16px] text-red-500">smart_display</span>
                      <span className="text-[10px] font-label-sm text-white">YouTube</span>
                    </div>
                    <div className="absolute bottom-2 right-2 rounded-lg bg-black/70 px-2 py-1 text-[10px] text-white">
                      {course.estimated_duration_minutes} min
                    </div>
                  </div>
                  <div className="p-stack-md">
                    <p className="mb-1 text-[10px] font-label-sm uppercase text-primary">
                      {course.category.name} / {course.level.name}
                    </p>
                    <h3 className="mb-1 font-title-md text-[17px] leading-6">{course.title}</h3>
                    <p className="mb-3 text-label-sm text-on-surface-variant">{course.description}</p>
                    <div className="h-1.5 overflow-hidden rounded-full bg-white/5">
                      <div className="h-full rounded-full bg-secondary" style={{ width: `${courseProgress.percentage}%` }} />
                    </div>
                    <p className="mt-2 text-[10px] text-on-surface-variant">
                      {courseProgress.completed}/{courseProgress.total} {t('learn.lessonsCompleted')}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        {activeCourse && activeLesson && (
          <>
            <section className="px-container-padding pb-stack-lg">
              <GlassCard className="overflow-hidden">
                <div className="aspect-video bg-black">
                  <iframe
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                    allowFullScreen
                    className="h-full w-full"
                    referrerPolicy="strict-origin-when-cross-origin"
                    src={`https://www.youtube.com/embed/${activeLesson.youtube_video_id}?rel=0&modestbranding=0`}
                    title={`${activeLesson.title} on YouTube`}
                  />
                </div>

                <div className="p-stack-md">
                  <div className="mb-stack-sm flex items-center justify-between gap-stack-md">
                    <span className="flex items-center gap-1 rounded-lg bg-red-500/15 px-2 py-1 text-[10px] font-label-sm text-red-200">
                      <span className="material-symbols-outlined text-[16px]">smart_display</span>
                      {t('learn.embeddedFromYoutube')}
                    </span>
                    <a
                      className="text-label-sm text-primary"
                      href={activeLesson.youtube_url}
                      rel="noreferrer"
                      target="_blank"
                    >
                      {t('learn.open')}
                    </a>
                  </div>
                  <h2 className="font-title-md text-title-md">{activeLesson.title}</h2>
                  <p className="mt-1 text-body-md text-on-surface-variant">{activeLesson.description}</p>
                  <p className="mt-3 rounded-lg bg-surface-container-high p-3 text-label-md text-on-surface">
                    {activeLesson.summary}
                  </p>
                </div>
              </GlassCard>
            </section>

            <section className="px-container-padding pb-stack-lg">
              <h2 className="mb-stack-md font-title-md text-title-md">{t('learn.lessons')}</h2>
              <div className="grid gap-gutter">
                {activeCourse.lessons.map((lesson) => {
                  const completed = progress[lesson.id]?.status === "completed";
                  const active = lesson.id === activeLesson.id;

                  return (
                    <button
                      className={`flex items-center gap-stack-md rounded-xl border p-stack-md text-left transition-all active:scale-[0.99] ${
                        active
                          ? "border-primary bg-primary/10"
                          : "border-white/10 bg-surface-container"
                      }`}
                      key={lesson.id}
                      onClick={() => selectLesson(lesson)}
                      type="button"
                    >
                      <LessonStatusIcon active={active} completed={completed} />
                      <div className="min-w-0 flex-1">
                        <p className="font-label-md text-label-md">{lesson.title}</p>
                        <p className="text-label-sm text-on-surface-variant">
                          {lesson.duration_minutes} min / {t('learn.quizRequired')}
                        </p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </section>

            <section className="px-container-padding">
              <GlassCard className="p-stack-md">
                <div className="mb-stack-md flex items-start justify-between gap-stack-md">
                  <div>
                    <p className="mb-1 text-label-sm uppercase text-secondary">{t('learn.lessonQuiz')}</p>
                    <h2 className="font-title-md text-title-md">{activeLesson.quiz.question}</h2>
                  </div>
                  {isCompleted && (
                    <span className="material-symbols-outlined text-secondary" style={{ fontVariationSettings: "'FILL' 1" }}>
                      verified
                    </span>
                  )}
                </div>

                <div className="grid gap-gutter">
                  {activeLesson.quiz.options.map((option) => {
                    const selected = selectedOptionId === option.id;

                    return (
                      <button
                        className={`rounded-lg border p-3 text-left text-label-md transition-all ${
                          selected
                            ? "border-primary bg-primary/15 text-on-surface"
                            : "border-white/10 bg-surface-container text-on-surface-variant"
                        }`}
                        disabled={isCompleted}
                        key={option.id}
                        onClick={() => setSelectedOptionId(option.id)}
                        type="button"
                      >
                        {option.text}
                      </button>
                    );
                  })}
                </div>

                {quizResult && (
                  <div
                    className={`mt-stack-md rounded-lg p-3 text-label-md ${
                      quizResult === "correct"
                        ? "bg-secondary/10 text-secondary"
                        : "bg-error-container/30 text-on-error-container"
                    }`}
                  >
                    {quizResult === "correct"
                      ? `${t('learn.correct')} ${activeLesson.quiz.explanation}`
                      : t('learn.notQuite')}
                  </div>
                )}

                <button
                  className="mt-stack-md flex w-full items-center justify-center gap-2 rounded-lg bg-secondary px-stack-md py-3 font-label-md text-on-secondary transition-all active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={isCompleted || !selectedOptionId}
                  onClick={submitAnswer}
                  type="button"
                >
                  <span className="material-symbols-outlined text-[18px]">
                    {isCompleted ? "check_circle" : "quiz"}
                  </span>
                  {isCompleted ? t('learn.lessonCompleted') : t('learn.submitAnswer')}
                </button>
              </GlassCard>
            </section>

            <section className="px-container-padding pt-stack-lg">
              <GlassCard className="p-stack-md">
                <div className="mb-2 flex items-center justify-between">
                  <span className="font-label-md">{activeCourse.title}</span>
                  <span className="font-mono-data text-label-sm">{activeCourseProgress.percentage}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-white/5">
                  <div
                    className="h-full rounded-full bg-primary"
                    style={{ width: `${activeCourseProgress.percentage}%` }}
                  />
                </div>
                <p className="mt-2 text-label-sm text-on-surface-variant">
                  {t('learn.courseProgressNote')}
                </p>
              </GlassCard>
            </section>
          </>
        )}
      </main>

      <BottomNav />
    </div>
  );
}
