import React, { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import TopBar from "../components/layout/TopBar";
import BottomNav from "../components/layout/BottomNav";
import GlassCard from "../components/ui/GlassCard";
import { getCourses } from "../data/localizedCourses";
import { useI18n } from "../i18n/I18nContext";

const STORAGE_KEY = "finanu_learning_progress";

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

function getFirstIncompleteLesson(course, progress) {
  return course.lessons.find((lesson) => lesson.is_active && progress[lesson.id]?.status !== "completed");
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

export default function Learn() {
  const { language, t } = useI18n();
  const [searchParams] = useSearchParams();
  const requestedCourseParam = searchParams.get("course");
  const requestedLessonParam = searchParams.get("lesson");
  const courses = useMemo(() => getCourses(language), [language]);
  const [progress, setProgress] = useState(loadProgress);
  const initialCourseId = Number(requestedCourseParam) || courses[0]?.id;
  const initialCourse = courses.find((course) => course.id === initialCourseId) || courses[0];
  const [activeCourseId, setActiveCourseId] = useState(initialCourse?.id);
  const [activeLessonId, setActiveLessonId] = useState(
    Number(requestedLessonParam) || initialCourse?.lessons[0]?.id
  );
  const [selectedOptionIds, setSelectedOptionIds] = useState({});
  const [examFeedback, setExamFeedback] = useState({});
  const [quizResult, setQuizResult] = useState(null);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
  }, [progress]);

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
      setProgress((current) => ({
        ...current,
        [requestedLesson.id]: {
          status: current[requestedLesson.id]?.status === "completed" ? "completed" : "in_progress",
          attempts: current[requestedLesson.id]?.attempts || 0,
          selected_option: current[requestedLesson.id]?.selected_option || null
        }
      }));
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
    courseStates.find((state) => state.course.id === activeCourseId && state.unlocked) || currentCourseState;
  const activeCourse = activeCourseState?.course || activeCourses[0];
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
  }, [courses, progress]);

  const activeCourseProgress = activeCourseState?.courseProgress || (activeCourse ? getCourseProgress(activeCourse, progress) : null);
  const activeLessonProgress = activeLesson ? progress[activeLesson.id] : null;
  const isCompleted = activeLessonProgress?.status === "completed";
  const activeExamQuestions = activeLesson?.quiz?.questions || (activeLesson?.quiz ? [activeLesson.quiz] : []);
  const answeredQuestions = activeExamQuestions.filter((question) => selectedOptionIds[question.id]).length;
  const hasAnsweredExam = activeExamQuestions.length > 0 && answeredQuestions === activeExamQuestions.length;

  const isLessonUnlocked = (course, lesson) => {
    const lessonIndex = course.lessons.findIndex((courseLesson) => courseLesson.id === lesson.id);
    if (lessonIndex <= 0) return true;

    return course.lessons
      .slice(0, lessonIndex)
      .every((previousLesson) => progress[previousLesson.id]?.status === "completed");
  };

  const selectCourse = (course) => {
    const selectedCourseState = courseStates.find((state) => state.course.id === course.id);
    if (!selectedCourseState?.unlocked) return;

    setActiveCourseId(course.id);
    setActiveLessonId(selectedCourseState.firstIncompleteLesson?.id || course.lessons[0]?.id);
    setSelectedOptionIds({});
    setExamFeedback({});
    setQuizResult(null);
  };

  const selectLesson = (lesson) => {
    if (!activeCourse || !isLessonUnlocked(activeCourse, lesson)) return;

    setActiveLessonId(lesson.id);
    setSelectedOptionIds({});
    setExamFeedback({});
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

    if (nextCourseState?.unlocked || nextCourseState?.current) {
      setActiveCourseId(nextCourseState.course.id);
      setActiveLessonId(nextCourseState.firstIncompleteLesson?.id || nextCourseState.course.lessons[0]?.id);
      setSelectedOptionIds({});
      setExamFeedback({});
      setQuizResult(null);
    }
  };

  const submitAnswer = () => {
    const selectedOptions = activeExamQuestions.map((question) =>
      question.options.find((option) => option.id === selectedOptionIds[question.id])
    );
    if (selectedOptions.some((option) => !option)) return;

    const currentProgress = progress[activeLesson.id] || { attempts: 0 };
    const attempts = currentProgress.attempts + 1;
    const allCorrect = selectedOptions.every((option) => option.is_correct);
    const nextFeedback = activeExamQuestions.reduce((feedback, question, index) => {
      const selectedOption = selectedOptions[index];
      return {
        ...feedback,
        [question.id]: {
          correct: selectedOption?.is_correct || false,
          selectedText: selectedOption?.text || '',
        }
      };
    }, {});

    setExamFeedback(nextFeedback);

    if (!allCorrect) {
      setQuizResult("wrong");
      setProgress((current) => ({
        ...current,
        [activeLesson.id]: {
          ...current[activeLesson.id],
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

        {currentCourseState && (
          <section className="px-container-padding pb-stack-lg">
            <GlassCard className="overflow-hidden">
              <div className="relative aspect-[16/9] bg-surface-container-high">
                <img alt="" className="h-full w-full object-cover" src={currentCourseState.course.thumbnail_url} />
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-stack-md">
                  <p className="mb-1 text-label-sm uppercase text-secondary">
                    {pathCompleted ? t('learn.pathCompleted') : t('learn.nextCourse')}
                  </p>
                  <h2 className="font-title-md text-title-md text-white">{currentCourseState.course.title}</h2>
                </div>
              </div>
              <div className="p-stack-md">
                <div className="mb-stack-sm flex items-center justify-between gap-stack-md">
                  <span className="rounded-lg bg-primary/15 px-2 py-1 text-[10px] font-label-sm uppercase text-primary">
                    {currentCourseState.course.category.name}
                  </span>
                  <span className="text-label-sm text-on-surface-variant">
                    {currentCourseState.courseProgress.completed}/{currentCourseState.courseProgress.total} {t('learn.lessonsCompleted')}
                  </span>
                </div>
                <p className="text-body-md text-on-surface-variant">{currentCourseState.course.description}</p>
                <div className="mt-stack-md h-2 overflow-hidden rounded-full bg-white/5">
                  <div
                    className="h-full rounded-full bg-secondary"
                    style={{ width: `${currentCourseState.courseProgress.percentage}%` }}
                  />
                </div>
                <button
                  className="mt-stack-md flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-stack-md py-3 font-label-md text-on-primary transition-all active:scale-[0.98]"
                  onClick={() => selectCourse(currentCourseState.course)}
                  type="button"
                >
                  <span className="material-symbols-outlined text-[18px]">play_arrow</span>
                  {pathCompleted ? t('learn.reviewCourse') : t('learn.continueCourse')}
                </button>
              </div>
            </GlassCard>
          </section>
        )}

        <section className="px-container-padding pb-stack-lg">
          <div className="mb-stack-md flex items-center justify-between">
            <h2 className="font-title-md text-title-md">{t('learn.learningPath')}</h2>
            <span className="text-label-sm text-on-surface-variant">{courseStates.length} {t('learn.courses')}</span>
          </div>
          <div className="grid gap-gutter">
            {courseStates.map((state) => {
              const isActive = state.course.id === activeCourse?.id;
              const statusLabel = state.completed
                ? t('learn.completed')
                : state.current
                  ? t('learn.inProgress')
                  : t('learn.locked');

              return (
                <button
                  className={`flex items-center gap-stack-md rounded-xl border p-stack-md text-left transition-all active:scale-[0.99] ${isActive
                    ? "border-primary bg-primary/10"
                    : state.unlocked
                      ? "border-white/10 bg-surface-container"
                      : "border-white/5 bg-surface-container/50 opacity-60"
                    }`}
                  disabled={!state.unlocked}
                  key={state.course.id}
                  onClick={() => selectCourse(state.course)}
                  type="button"
                >
                  <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${state.completed ? "bg-secondary/15 text-secondary" : state.unlocked ? "bg-primary/15 text-primary" : "bg-white/5 text-on-surface-variant"}`}>
                    <span className="material-symbols-outlined text-[20px]">
                      {state.completed ? "check_circle" : state.unlocked ? "play_circle" : "lock"}
                    </span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="font-label-md text-label-md">{state.index + 1}. {state.course.title}</p>
                    <p className="text-label-sm text-on-surface-variant">
                      {state.course.level.name} / {state.course.category.name} / {statusLabel}
                    </p>
                    <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/5">
                      <div className="h-full rounded-full bg-secondary" style={{ width: `${state.courseProgress.percentage}%` }} />
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        {courseStates.some((state) => state.completed) && (
          <section className="px-container-padding pb-stack-lg">
            <div className="mb-stack-md flex items-center justify-between">
              <h2 className="font-title-md text-title-md">{t('learn.reviewCompleted')}</h2>
              <span className="text-label-sm text-on-surface-variant">
                {courseStates.filter((state) => state.completed).length}
              </span>
            </div>
            <div className="flex gap-gutter overflow-x-auto pb-1 hide-scrollbar">
              {courseStates.filter((state) => state.completed).map((state) => (
                <button
                  className={`min-w-[220px] rounded-xl border bg-surface-container p-stack-md text-left transition-all active:scale-[0.98] ${state.course.id === activeCourse?.id ? "border-primary" : "border-white/10"
                    }`}
                  key={state.course.id}
                  onClick={() => selectCourse(state.course)}
                  type="button"
                >
                  <div className="mb-stack-sm flex items-center justify-between">
                    <span className="material-symbols-outlined text-secondary" style={{ fontVariationSettings: "'FILL' 1" }}>
                      check_circle
                    </span>
                    <span className="text-label-sm text-on-surface-variant">100%</span>
                  </div>
                  <p className="font-label-md text-label-md">{state.course.title}</p>
                  <p className="mt-1 text-label-sm text-on-surface-variant">{state.course.category.name}</p>
                </button>
              ))}
            </div>
          </section>
        )}

        {activeCourse && activeLesson && (
          <>
            <section className="px-container-padding pb-stack-lg">
              <GlassCard className="overflow-hidden">
                {activeLesson.content_type === "video" && activeLesson.youtube_video_id ? (
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
                ) : activeLesson.embed_url ? (
                  <div className="aspect-video bg-black">
                    <iframe
                      allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                      className="h-full w-full"
                      loading="lazy"
                      src={activeLesson.embed_url}
                      title={activeLesson.title}
                    />
                  </div>
                ) : (
                  <div className="flex aspect-video items-center justify-center bg-surface-container-high">
                    <span className="material-symbols-outlined text-[56px] text-primary">
                      {getContentIcon(activeLesson.content_type)}
                    </span>
                  </div>
                )}

                <div className="p-stack-md">
                  <div className="mb-stack-sm flex items-center justify-between gap-stack-md">
                    <span className={`flex items-center gap-1 rounded-lg px-2 py-1 text-[10px] font-label-sm ${getProviderTone(activeLesson.content_type)}`}>
                      <span className="material-symbols-outlined text-[16px]">{getContentIcon(activeLesson.content_type)}</span>
                      {activeLesson.provider || t('learn.learningResource')}
                    </span>
                    <a
                      className="text-label-sm text-primary"
                      href={activeLesson.source_url || activeLesson.youtube_url}
                      rel="noreferrer"
                      target="_blank"
                    >
                      {t('learn.open')}
                    </a>
                  </div>
                  <h2 className="font-title-md text-title-md">{activeLesson.title}</h2>
                  <p className="mt-1 text-body-md text-on-surface-variant">{activeLesson.description}</p>
                  <p className="mt-2 text-label-sm text-on-surface-variant">
                    {t('learn.contentLanguage')}: {(activeLesson.content_language || language).toUpperCase()}
                    {activeLesson.source_channel ? ` / ${activeLesson.source_channel}` : ''}
                  </p>
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
                  const locked = !isLessonUnlocked(activeCourse, lesson);

                  return (
                    <button
                      className={`flex items-center gap-stack-md rounded-xl border p-stack-md text-left transition-all active:scale-[0.99] ${active
                        ? "border-primary bg-primary/10"
                        : locked
                          ? "border-white/5 bg-surface-container/50 opacity-60"
                          : "border-white/10 bg-surface-container"
                        }`}
                      disabled={locked}
                      key={lesson.id}
                      onClick={() => selectLesson(lesson)}
                      type="button"
                    >
                      {locked ? (
                        <span className="material-symbols-outlined text-on-surface-variant">lock</span>
                      ) : (
                        <LessonStatusIcon active={active} completed={completed} />
                      )}
                      <div className="min-w-0 flex-1">
                        <p className="font-label-md text-label-md">{lesson.title}</p>
                        <p className="text-label-sm text-on-surface-variant">
                          {lesson.duration_minutes} min / {lesson.content_type || "video"} / {t('learn.quizRequired')}
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
                    <h2 className="font-title-md text-title-md">{t('learn.examForVideo')}</h2>
                  </div>
                  {isCompleted && (
                    <span className="material-symbols-outlined text-secondary" style={{ fontVariationSettings: "'FILL' 1" }}>
                      verified
                    </span>
                  )}
                </div>

                <div className="grid gap-gutter">
                  {activeExamQuestions.map((question, questionIndex) => (
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
                              disabled={isCompleted}
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
                            ? "bg-secondary/10 text-secondary"
                            : "bg-error-container/30 text-on-error-container"
                            }`}
                        >
                          <div className="flex items-start gap-2">
                            <span className="material-symbols-outlined text-[18px]">
                              {examFeedback[question.id].correct ? "check_circle" : "cancel"}
                            </span>
                            <div>
                              <p className="font-label-md">
                                {examFeedback[question.id].correct ? t('learn.answerCorrect') : t('learn.answerWrong')}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {quizResult && (
                  <div
                    className={`mt-stack-md rounded-lg p-3 text-label-md ${quizResult === "correct"
                      ? "bg-secondary/10 text-secondary"
                      : "bg-error-container/30 text-on-error-container"
                      }`}
                  >
                    {quizResult === "correct"
                      ? `${t('learn.correct')} ${activeExamQuestions[0]?.explanation || ''}`
                      : t('learn.notQuite')}
                  </div>
                )}

                <button
                  className="mt-stack-md flex w-full items-center justify-center gap-2 rounded-lg bg-[#f2ae2e] px-stack-md py-3 font-label-md text-on-primary-container shadow-lg shadow-[rgba(242,174,46,0.16)] transition-all hover:brightness-105 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={isCompleted || !hasAnsweredExam}
                  onClick={submitAnswer}
                  type="button"
                >
                  <span className="material-symbols-outlined text-[18px]">
                    {isCompleted ? "check_circle" : "quiz"}
                  </span>
                  {isCompleted ? t('learn.lessonCompleted') : t('learn.submitAnswer')}
                </button>

                {isCompleted && (
                  <button
                    className="mt-gutter flex w-full items-center justify-center gap-2 rounded-lg border border-primary/40 bg-primary/10 px-stack-md py-3 font-label-md text-primary transition-all active:scale-[0.98]"
                    onClick={goToNextStep}
                    type="button"
                  >
                    <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                    {t('learn.nextStep')}
                  </button>
                )}
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
