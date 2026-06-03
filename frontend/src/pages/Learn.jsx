import React, { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getLearningCatalog, getLearningProgress, submitLessonExam } from "../api/learning";
import TopBar from "../components/layout/TopBar";
import BottomNav from "../components/layout/BottomNav";
import GlassCard from "../components/ui/GlassCard";
import { getCourses as getLocalCourses } from "../data/localizedCourses";
import { useI18n } from "../i18n/I18nContext";
import { getCurrentUser } from "../utils/session";

const STORAGE_KEY = "finanu_learning_progress";

function loadProgress() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch {
    return {};
  }
}

function getProgressEntry(progress, lessonId) {
  return progress[lessonId] || progress[String(lessonId)] || {};
}

function getCourseProgress(course, progress) {
  const activeLessons = course.lessons.filter((lesson) => lesson.is_active);
  const completed = activeLessons.filter((lesson) => getProgressEntry(progress, lesson.id).status === "completed").length;
  const total = activeLessons.length;

  return {
    completed,
    total,
    percentage: total ? Math.round((completed / total) * 100) : 0
  };
}

function getFirstIncompleteLesson(course, progress) {
  return course.lessons.find((lesson) => lesson.is_active && getProgressEntry(progress, lesson.id).status !== "completed");
}

function getContentIcon(contentType) {
  if (contentType === "audio") return "headphones";
  if (contentType === "article") return "article";
  if (contentType === "course") return "school";
  return "smart_display";
}

function getProviderTone(contentType) {
  if (contentType === "audio") return "bg-primary/15 text-primary";
  if (contentType === "article") return "bg-secondary/10 text-secondary";
  if (contentType === "course") return "bg-tertiary/15 text-tertiary";
  return "bg-red-500/15 text-red-200";
}

function LessonStatusIcon({ completed, active, locked }) {
  if (locked) {
    return <span className="material-symbols-outlined text-on-surface-variant">lock</span>;
  }

  if (completed) {
    return (
      <span className="material-symbols-outlined text-metric" style={{ fontVariationSettings: "'FILL' 1" }}>
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

function LessonMedia({ lesson, language, t }) {
  if (lesson.content_type === "video" && lesson.youtube_video_id) {
    return (
      <div className="aspect-video bg-black">
        <iframe
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowFullScreen
          className="h-full w-full"
          referrerPolicy="strict-origin-when-cross-origin"
          src={`https://www.youtube.com/embed/${lesson.youtube_video_id}?rel=0&modestbranding=0`}
          title={`${lesson.title} on YouTube`}
        />
      </div>
    );
  }

  if (lesson.embed_url) {
    return (
      <div className="aspect-video bg-black">
        <iframe
          allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
          className="h-full w-full"
          loading="lazy"
          src={lesson.embed_url}
          title={lesson.title}
        />
      </div>
    );
  }

  if (lesson.image_url) {
    return (
      <div className="aspect-video bg-surface-container-high">
        <img alt="" className="h-full w-full object-cover" src={lesson.image_url} />
      </div>
    );
  }

  return (
    <div className="flex aspect-video items-center justify-center bg-surface-container-high">
      <span className="material-symbols-outlined text-[56px] text-primary">
        {getContentIcon(lesson.content_type)}
      </span>
      <span className="sr-only">{t("learn.contentLanguage")}: {(lesson.content_language || language).toUpperCase()}</span>
    </div>
  );
}

export default function Learn() {
  const { language, t } = useI18n();
  const [searchParams] = useSearchParams();
  const requestedCourseParam = searchParams.get("course");
  const requestedLessonParam = searchParams.get("lesson");
  const currentUser = useMemo(() => getCurrentUser(), []);
  const localCourses = useMemo(() => getLocalCourses(language), [language]);
  const [courses, setCourses] = useState([]);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [progress, setProgress] = useState(loadProgress);
  const [activeCourseId, setActiveCourseId] = useState(Number(requestedCourseParam) || null);
  const [activeLessonId, setActiveLessonId] = useState(Number(requestedLessonParam) || null);
  const [selectedOptionIds, setSelectedOptionIds] = useState({});
  const [examFeedback, setExamFeedback] = useState({});
  const [quizResult, setQuizResult] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setCourses([]);
    setCatalogLoading(true);

    getLearningCatalog(language)
      .then((catalog) => {
        if (!cancelled && Array.isArray(catalog) && catalog.length > 0) {
          setCourses(catalog);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCourses(localCourses);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setCatalogLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [language, localCourses]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
  }, [progress]);

  useEffect(() => {
    if (!currentUser?.id) return;

    let cancelled = false;
    getLearningProgress(currentUser.id)
      .then((data) => {
        if (!cancelled && data?.lessons) {
          setProgress(data.lessons);
        }
      })
      .catch(() => {});

    return () => {
      cancelled = true;
    };
  }, [currentUser?.id, courses]);

  useEffect(() => {
    const courseId = Number(requestedCourseParam);
    const lessonId = Number(requestedLessonParam);

    if (!courseId && !lessonId) return;

    const requestedCourse = courses.find((course) => course.id === courseId);
    const requestedLesson = requestedCourse?.lessons.find((lesson) => lesson.id === lessonId);

    if (requestedCourse) {
      setActiveCourseId(requestedCourse.id);
    }

    if (requestedLesson) {
      setActiveLessonId(requestedLesson.id);
    }

    setSelectedOptionIds({});
    setExamFeedback({});
    setQuizResult(null);
  }, [courses, requestedCourseParam, requestedLessonParam]);

  const activeCourses = useMemo(() => courses.filter((course) => course.is_active), [courses]);

  const courseStates = useMemo(() => {
    let previousCompleted = true;

    return activeCourses.map((course, index) => {
      const courseProgress = getCourseProgress(course, progress);
      const completed = courseProgress.total > 0 && courseProgress.completed === courseProgress.total;
      const unlocked = previousCompleted;
      const current = unlocked && !completed;
      const firstIncompleteLesson = getFirstIncompleteLesson(course, progress);
      previousCompleted = previousCompleted && completed;

      return {
        course,
        courseProgress,
        completed,
        current,
        firstIncompleteLesson,
        index,
        unlocked,
      };
    });
  }, [activeCourses, progress]);

  const pathCompleted = courseStates.length > 0 && courseStates.every((state) => state.completed);
  const currentCourseState = courseStates.find((state) => state.current) || courseStates[courseStates.length - 1];
  const activeCourseState =
    courseStates.find((state) => state.course.id === activeCourseId) || currentCourseState;
  const activeCourse = activeCourseState?.course || activeCourses[0];
  const activeLesson =
    activeLessonId ? activeCourse?.lessons.find((lesson) => lesson.id === activeLessonId) : null;

  useEffect(() => {
    if (activeCourses.length === 0) return;

    const requestedCourseId = Number(requestedCourseParam);
    const requestedLessonId = Number(requestedLessonParam);
    const requestedCourse = activeCourses.find((course) => course.id === requestedCourseId);
    const currentCourse = activeCourses.find((course) => course.id === activeCourseId);
    const nextCourse = requestedCourse || currentCourse || activeCourses[0];
    const requestedLesson = nextCourse.lessons.find((lesson) => lesson.id === requestedLessonId);
    const currentLesson = nextCourse.lessons.find((lesson) => lesson.id === activeLessonId);
    const nextLesson = requestedLesson || currentLesson || nextCourse.lessons[0];

    if (nextCourse.id !== activeCourseId) {
      setActiveCourseId(nextCourse.id);
    }

    if (nextLesson?.id !== activeLessonId) {
      setActiveLessonId(nextLesson?.id || null);
    }
  }, [activeCourseId, activeCourses, activeLessonId, requestedCourseParam, requestedLessonParam]);

  const globalProgress = useMemo(() => {
    const allLessons = courses.flatMap((course) =>
      course.is_active ? course.lessons.filter((lesson) => lesson.is_active) : []
    );
    const completed = allLessons.filter((lesson) => getProgressEntry(progress, lesson.id).status === "completed").length;

    return {
      completed,
      total: allLessons.length,
      percentage: allLessons.length ? Math.round((completed / allLessons.length) * 100) : 0
    };
  }, [courses, progress]);

  const activeCourseProgress = activeCourseState?.courseProgress || (activeCourse ? getCourseProgress(activeCourse, progress) : null);
  const activeLessonProgress = activeLesson ? getProgressEntry(progress, activeLesson.id) : null;
  const isCompleted = activeLessonProgress?.status === "completed";
  const activeExamQuestions = activeLesson?.quiz?.questions || (activeLesson?.quiz ? [activeLesson.quiz] : []);
  const answeredQuestions = activeExamQuestions.filter((question) => selectedOptionIds[question.id]).length;
  const hasAnsweredExam = activeExamQuestions.length > 0 && answeredQuestions === activeExamQuestions.length;

  const isLessonSequentiallyUnlocked = (course, lesson) => {
    const lessonIndex = course.lessons.findIndex((courseLesson) => courseLesson.id === lesson.id);
    if (lessonIndex <= 0) return true;

    return course.lessons
      .slice(0, lessonIndex)
      .every((previousLesson) => getProgressEntry(progress, previousLesson.id).status === "completed");
  };

  const canAccessLessonContent = (courseState, lesson) =>
    Boolean(courseState?.unlocked && activeCourse && isLessonSequentiallyUnlocked(activeCourse, lesson));

  const canAccessActiveLessonContent = activeLesson ? canAccessLessonContent(activeCourseState, activeLesson) : false;

  const selectCourse = (course) => {
    const selectedCourseState = courseStates.find((state) => state.course.id === course.id);
    const nextLesson = selectedCourseState?.unlocked
      ? selectedCourseState.firstIncompleteLesson || course.lessons[0]
      : course.lessons[0];

    setActiveCourseId(course.id);
    setActiveLessonId(nextLesson?.id);
    setSelectedOptionIds({});
    setExamFeedback({});
    setQuizResult(null);
  };

  const selectLesson = (lesson) => {
    if (!activeCourse) return;

    if (activeLessonId === lesson.id) {
      setActiveLessonId(null);
      setSelectedOptionIds({});
      setExamFeedback({});
      setQuizResult(null);
      return;
    }

    const lessonIsAccessible = canAccessLessonContent(activeCourseState, lesson);
    setActiveLessonId(lesson.id);
    setSelectedOptionIds({});
    setExamFeedback({});
    setQuizResult(null);

    if (!lessonIsAccessible) return;

    setProgress((current) => ({
      ...current,
      [lesson.id]: {
        status: getProgressEntry(current, lesson.id).status === "completed" ? "completed" : "in_progress",
        attempts: getProgressEntry(current, lesson.id).attempts || 0,
        selected_options: getProgressEntry(current, lesson.id).selected_options || {},
        quiz_answered_correctly: getProgressEntry(current, lesson.id).quiz_answered_correctly || false
      }
    }));
  };

  const goToNextStep = () => {
    if (!activeCourse || !activeLesson) return;

    const lessonIndex = activeCourse.lessons.findIndex((lesson) => lesson.id === activeLesson.id);
    const nextLesson = activeCourse.lessons[lessonIndex + 1];

    if (nextLesson) {
      selectLesson(nextLesson);
      return;
    }

    const courseIndex = courseStates.findIndex((state) => state.course.id === activeCourse.id);
    const nextCourseState = courseStates[courseIndex + 1];

    if (nextCourseState) {
      setActiveCourseId(nextCourseState.course.id);
      setActiveLessonId(nextCourseState.firstIncompleteLesson?.id || nextCourseState.course.lessons[0]?.id);
      setSelectedOptionIds({});
      setExamFeedback({});
      setQuizResult(null);
    }
  };

  const submitAnswer = async () => {
    if (!canAccessActiveLessonContent) return;

    const selectedOptions = activeExamQuestions.map((question) =>
      question.options.find((option) => option.id === selectedOptionIds[question.id])
    );
    if (selectedOptions.some((option) => !option)) return;

    if (currentUser?.id) {
      try {
        const result = await submitLessonExam({
          lessonId: activeLesson.id,
          userId: currentUser.id,
          answers: selectedOptionIds,
        });

        setExamFeedback(result.feedback || {});
        setQuizResult(result.quiz_answered_correctly ? "correct" : "wrong");
        setProgress((current) => ({
          ...current,
          [activeLesson.id]: {
            status: result.status,
            attempts: result.attempts,
            selected_options: result.selected_options,
            quiz_answered_correctly: result.quiz_answered_correctly,
            completed_at: result.completed_at,
          }
        }));
        return;
      } catch {
        // Fall through to the local validator only when the bundled fallback data includes answers.
      }
    }

    const currentProgress = getProgressEntry(progress, activeLesson.id);
    const attempts = (currentProgress.attempts || 0) + 1;
    const allCorrect = selectedOptions.every((option) => option.is_correct);
    const nextFeedback = activeExamQuestions.reduce((feedback, question, index) => {
      const selectedOption = selectedOptions[index];
      return {
        ...feedback,
        [question.id]: {
          correct: selectedOption?.is_correct || false,
          selectedText: selectedOption?.text || "",
        }
      };
    }, {});

    setExamFeedback(nextFeedback);

    if (!allCorrect) {
      setQuizResult("wrong");
      setProgress((current) => ({
        ...current,
        [activeLesson.id]: {
          ...getProgressEntry(current, activeLesson.id),
          status: "in_progress",
          attempts,
          selected_options: selectedOptionIds,
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
        selected_options: selectedOptionIds,
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
              <p className="mb-1 text-label-sm uppercase text-primary">{t("learn.learning")}</p>
              <h1 className="font-headline-lg-mobile text-headline-lg-mobile tracking-normal">
                {t("learn.financeLessons")}
              </h1>
            </div>
            <div className="text-right">
              <p className="font-mono-data text-[22px] text-metric">{courseStates.length}</p>
              <p className="text-label-sm text-on-surface-variant">
                {t("learn.courses")}
              </p>
            </div>
          </div>

          <GlassCard className="p-stack-md">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-label-sm text-on-surface-variant">{t("learn.globalProgress")}</span>
              <span className="font-mono-data text-label-sm">
                {globalProgress.completed}/{globalProgress.total} {t("learn.lessonsCompleted")}
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-white/5">
              <div className="h-full rounded-full bg-metric" style={{ width: `${globalProgress.percentage}%` }} />
            </div>
          </GlassCard>
        </section>

        <section className="px-container-padding pb-stack-lg">
          <div className="mb-stack-md flex items-center justify-between">
            <h2 className="font-title-md text-title-md">{t("learn.courseMap")}</h2>
          </div>

          <GlassCard className="overflow-hidden p-stack-md">
            {catalogLoading ? (
              <div className="flex gap-2 overflow-hidden pb-2">
                {[0, 1, 2].map((item) => (
                  <div className="flex min-w-[92px] flex-col items-center gap-2" key={item}>
                    <span className="h-14 w-14 animate-pulse rounded-full bg-surface-container-high" />
                    <span className="h-8 w-20 animate-pulse rounded-lg bg-surface-container-high" />
                    <span className="h-3 w-14 animate-pulse rounded-full bg-surface-container-high" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex gap-2 overflow-x-auto pb-2 hide-scrollbar">
                {courseStates.map((state, index) => {
                const isActive = state.course.id === activeCourse?.id;
                const statusLabel = state.completed
                  ? t("learn.completed")
                  : state.current
                    ? t("learn.inProgress")
                    : t("learn.locked");

                return (
                  <div className="flex min-w-[92px] items-start" key={state.course.id}>
                    <button
                      className="group flex w-full flex-col items-center gap-2 text-center"
                      onClick={() => selectCourse(state.course)}
                      type="button"
                    >
                      <span
                        className={`flex h-14 w-14 items-center justify-center rounded-full border text-[13px] font-label-md transition-all active:scale-[0.96] ${isActive
                          ? "border-primary bg-primary text-on-primary shadow-lg shadow-primary/20"
                          : state.completed
                            ? "border-metric/60 bg-metric/15 text-metric"
                            : state.unlocked
                              ? "border-primary/50 bg-primary/10 text-primary"
                              : "border-white/10 bg-surface-container-high text-on-surface-variant"
                        }`}
                      >
                        <span className="material-symbols-outlined text-[22px]">
                          {state.completed ? "check" : state.unlocked ? "play_arrow" : "lock"}
                        </span>
                      </span>
                      <span className="line-clamp-3 min-h-[42px] text-label-sm leading-tight text-on-surface">
                        {index + 1}. {state.course.title}
                      </span>
                      <span className="text-[10px] uppercase text-on-surface-variant">{statusLabel}</span>
                    </button>
                    {index < courseStates.length - 1 && (
                      <div className={`mt-7 h-px w-8 shrink-0 ${state.completed ? "bg-metric" : "bg-white/10"}`} />
                    )}
                  </div>
                );
                })}
              </div>
            )}
          </GlassCard>
        </section>

        {activeCourseState && (
          <section className="px-container-padding pb-stack-lg">
            <GlassCard className="overflow-hidden">
              <div className="relative aspect-[16/9] bg-surface-container-high">
                <img alt="" className="h-full w-full object-cover" src={activeCourseState.course.thumbnail_url} />
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-stack-md">
                  <p className="mb-1 text-label-sm uppercase text-secondary">
                    {activeCourseState.unlocked ? t("learn.learningPath") : t("learn.previewOnly")}
                  </p>
                  <h2 className="font-title-md text-title-md text-white">{activeCourseState.course.title}</h2>
                </div>
              </div>
              <div className="p-stack-md">
                <div className="mb-stack-sm flex items-center justify-between gap-stack-md">
                  <span className="rounded-lg bg-primary/15 px-2 py-1 text-[10px] font-label-sm uppercase text-primary">
                    {activeCourseState.course.category.name}
                  </span>
                  <span className="text-label-sm text-on-surface-variant">
                    {activeCourseState.courseProgress.completed}/{activeCourseState.courseProgress.total} {t("learn.lessonsCompleted")}
                  </span>
                </div>
                <p className="text-body-md text-on-surface-variant">{activeCourseState.course.description}</p>
                <div className="mt-stack-md h-2 overflow-hidden rounded-full bg-white/5">
                  <div
                    className="h-full rounded-full bg-metric"
                    style={{ width: `${activeCourseState.courseProgress.percentage}%` }}
                  />
                </div>
                {!activeCourseState.unlocked && (
                  <p className="mt-stack-md rounded-lg bg-surface-container-high p-3 text-label-sm text-on-surface-variant">
                    {t("learn.lockedCourseNote")}
                  </p>
                )}
                {pathCompleted && activeCourseState.completed && (
                  <p className="mt-stack-md rounded-lg bg-metric/10 p-3 text-label-sm text-metric">
                    {t("learn.pathCompleted")}
                  </p>
                )}
              </div>
            </GlassCard>
          </section>
        )}

        {activeCourse && (
          <>
            <section className="px-container-padding pb-stack-lg">
              <div className="mb-stack-md flex items-center justify-between">
                <h2 className="font-title-md text-title-md">{t("learn.lessons")}</h2>
                <span className="font-mono-data text-label-sm text-metric">{activeCourseProgress?.percentage || 0}%</span>
              </div>

              <div className="grid gap-gutter">
                {activeCourse.lessons.map((lesson) => {
                  const lessonProgress = getProgressEntry(progress, lesson.id);
                  const completed = lessonProgress.status === "completed";
                  const active = lesson.id === activeLessonId;
                  const locked = !canAccessLessonContent(activeCourseState, lesson);
                  const examQuestions = lesson.quiz?.questions || (lesson.quiz ? [lesson.quiz] : []);
                  const showQuiz = active && !locked;

                  return (
                    <article
                      className={`overflow-hidden rounded-xl border transition-all ${active
                        ? "border-primary bg-primary/10"
                        : locked
                          ? "border-white/5 bg-surface-container/50"
                          : "border-white/10 bg-surface-container"
                      }`}
                      key={lesson.id}
                    >
                      <button
                        className="flex w-full items-center gap-stack-md p-stack-md text-left transition-all active:scale-[0.99]"
                        onClick={() => selectLesson(lesson)}
                        type="button"
                      >
                        <LessonStatusIcon active={active} completed={completed} locked={locked} />
                        <div className="min-w-0 flex-1">
                          <p className="font-label-md text-label-md">{lesson.title}</p>
                          <p className="text-label-sm text-on-surface-variant">
                            {lesson.duration_minutes} min / {lesson.content_type || "video"} / {completed ? t("learn.completed") : t("learn.quizRequired")}
                          </p>
                        </div>
                        <span className="material-symbols-outlined text-on-surface-variant">
                          {active ? "expand_less" : "expand_more"}
                        </span>
                      </button>

                      {active && (
                        <div className="border-t border-white/10">
                          {locked ? (
                            <div className="p-stack-md">
                              <p className="text-body-md text-on-surface-variant">{lesson.description}</p>
                              <p className="mt-3 rounded-lg bg-surface-container-high p-3 text-label-sm text-on-surface-variant">
                                {activeCourseState?.unlocked ? t("learn.lockedLessonNote") : t("learn.lockedCourseNote")}
                              </p>
                            </div>
                          ) : (
                            <>
                              <LessonMedia lesson={lesson} language={language} t={t} />
                              <div className="p-stack-md">
                                <div className="mb-stack-sm flex items-center justify-between gap-stack-md">
                                  <span className={`flex items-center gap-1 rounded-lg px-2 py-1 text-[10px] font-label-sm ${getProviderTone(lesson.content_type)}`}>
                                    <span className="material-symbols-outlined text-[16px]">{getContentIcon(lesson.content_type)}</span>
                                    {lesson.provider || t("learn.learningResource")}
                                  </span>
                                  {(lesson.source_url || lesson.youtube_url) && (
                                    <a
                                      className="text-label-sm text-primary"
                                      href={lesson.source_url || lesson.youtube_url}
                                      rel="noreferrer"
                                      target="_blank"
                                    >
                                      {t("learn.open")}
                                    </a>
                                  )}
                                </div>
                                <h3 className="font-title-md text-title-md">{lesson.title}</h3>
                                <p className="mt-1 text-body-md text-on-surface-variant">{lesson.description}</p>
                                <p className="mt-2 text-label-sm text-on-surface-variant">
                                  {t("learn.contentLanguage")}: {(lesson.content_language || language).toUpperCase()}
                                  {lesson.source_channel ? ` / ${lesson.source_channel}` : ""}
                                </p>
                                <p className="mt-3 rounded-lg bg-surface-container-high p-3 text-label-md text-on-surface">
                                  {lesson.summary}
                                </p>
                              </div>
                            </>
                          )}

                          {showQuiz && (
                            <div className="border-t border-white/10 p-stack-md">
                              <div className="mb-stack-md flex items-start justify-between gap-stack-md">
                                <div>
                                  <p className="mb-1 text-label-sm uppercase text-secondary">{t("learn.lessonQuiz")}</p>
                                  <h3 className="font-title-md text-title-md">{t("learn.examForVideo")}</h3>
                                </div>
                                {completed && (
                                  <span className="material-symbols-outlined text-metric" style={{ fontVariationSettings: "'FILL' 1" }}>
                                    verified
                                  </span>
                                )}
                              </div>

                              <div className="grid gap-gutter">
                                {examQuestions.map((question, questionIndex) => (
                                  <div className="rounded-lg border border-white/10 bg-surface-container p-3" key={question.id}>
                                    <p className="mb-3 font-label-md text-label-md">
                                      {questionIndex + 1}. {question.question}
                                    </p>
                                    <div className="grid gap-2">
                                      {question.options.map((option) => {
                                        const selected = selectedOptionIds[question.id] === option.id;

                                        return (
                                          <button
                                            className={`rounded-lg border p-3 text-left text-label-md transition-all ${selected
                                              ? "border-primary bg-primary/15 text-on-surface"
                                              : "border-white/10 bg-surface-container-high text-on-surface-variant"
                                            }`}
                                            disabled={completed}
                                            key={option.id}
                                            onClick={() =>
                                              setSelectedOptionIds((current) => ({
                                                ...current,
                                                [question.id]: option.id
                                              }))
                                            }
                                            type="button"
                                          >
                                            {option.text}
                                          </button>
                                        );
                                      })}
                                    </div>
                                    {examFeedback[question.id] && (
                                      <div
                                        className={`mt-3 rounded-lg p-3 text-label-sm ${examFeedback[question.id].correct
                                          ? "bg-metric/10 text-metric"
                                          : "bg-error-container/30 text-on-error-container"
                                        }`}
                                      >
                                        <div className="flex items-start gap-2">
                                          <span className="material-symbols-outlined text-[18px]">
                                            {examFeedback[question.id].correct ? "check_circle" : "cancel"}
                                          </span>
                                          <p className="font-label-md">
                                            {examFeedback[question.id].correct ? t("learn.answerCorrect") : t("learn.answerWrong")}
                                          </p>
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>

                              {quizResult && (
                                <div
                                  className={`mt-stack-md rounded-lg p-3 text-label-md ${quizResult === "correct"
                                    ? "bg-metric/10 text-metric"
                                    : "bg-error-container/30 text-on-error-container"
                                  }`}
                                >
                                  {quizResult === "correct"
                                    ? `${t("learn.correct")} ${examQuestions[0]?.explanation || ""}`
                                    : t("learn.notQuite")}
                                </div>
                              )}

                              <button
                                className="mt-stack-md flex w-full items-center justify-center gap-2 rounded-lg bg-[#f2ae2e] px-stack-md py-3 font-label-md text-on-primary-container shadow-lg shadow-[rgba(242,174,46,0.16)] transition-all hover:brightness-105 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
                                disabled={completed || !hasAnsweredExam}
                                onClick={submitAnswer}
                                type="button"
                              >
                                <span className="material-symbols-outlined text-[18px]">
                                  {completed ? "check_circle" : "quiz"}
                                </span>
                                {completed ? t("learn.lessonCompleted") : t("learn.submitAnswer")}
                              </button>

                              {completed && (
                                <button
                                  className="mt-gutter flex w-full items-center justify-center gap-2 rounded-lg border border-primary/40 bg-primary/10 px-stack-md py-3 font-label-md text-primary transition-all active:scale-[0.98]"
                                  onClick={goToNextStep}
                                  type="button"
                                >
                                  <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                                  {t("learn.nextStep")}
                                </button>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </article>
                  );
                })}
              </div>
            </section>

            <section className="px-container-padding">
              <GlassCard className="p-stack-md">
                <div className="mb-2 flex items-center justify-between">
                  <span className="font-label-md">{activeCourse.title}</span>
                  <span className="font-mono-data text-label-sm">{activeCourseProgress?.percentage || 0}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-white/5">
                  <div
                    className="h-full rounded-full bg-primary"
                    style={{ width: `${activeCourseProgress?.percentage || 0}%` }}
                  />
                </div>
                <p className="mt-2 text-label-sm text-on-surface-variant">
                  {t("learn.courseProgressNote")}
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
