import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import GlassCard from '../components/ui/GlassCard';
import CategoryChips from '../components/ui/CategoryChips';
import MarketCarousel from '../components/market/MarketCarousel';
import { getNewsArticles } from '../api/content';
import { getCourses } from '../data/localizedCourses';
import { useI18n } from '../i18n/I18nContext';
import { translateApiError } from '../utils/apiErrors';
import { getCurrentUser } from '../utils/session';

const INTEREST_TO_NEWS_TYPE = {
  crypto: 'crypto',
  stocks: 'stock_market',
  forex: 'forex',
  savings: 'investing_basics',
};

const NEWS_TYPE_LABEL_KEYS = {
  crypto: 'dashboard.crypto',
  stock_market: 'dashboard.stocks',
  forex: 'dashboard.forex',
  investing_basics: 'dashboard.investingBasics',
};

const NEWS_TYPE_ICON = {
  crypto: 'currency_bitcoin',
  stock_market: 'show_chart',
  forex: 'payments',
  investing_basics: 'school',
};

const FALLBACK_IMAGES = [
  'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=1200&q=80',
  'https://images.unsplash.com/photo-1642790106117-e829e14a795f?auto=format&fit=crop&w=1200&q=80',
  'https://images.unsplash.com/photo-1520607162513-77705c0f0d4a?auto=format&fit=crop&w=1200&q=80',
  'https://images.unsplash.com/photo-1559526324-593bc073d938?auto=format&fit=crop&w=1200&q=80',
  'https://images.unsplash.com/photo-1563986768609-322da13575f3?auto=format&fit=crop&w=1200&q=80',
];

const NEWS_PAGE_SIZE = 20;
const LEARNING_PROGRESS_STORAGE_KEY = 'finanu_learning_progress';
const NEWS_DATE_RANGE_OPTIONS = [
  { id: '24h', labelKey: 'dashboard.newsRange24h' },
  { id: 'week', labelKey: 'dashboard.newsRangeWeek' },
  { id: 'month', labelKey: 'dashboard.newsRangeMonth' },
  { id: 'year', labelKey: 'dashboard.newsRangeYear' },
  { id: 'all', labelKey: 'dashboard.newsRangeAll' },
];

function mapUserInterestsToNewsTypes(interests = []) {
  return interests.map((interest) => INTEREST_TO_NEWS_TYPE[interest]).filter(Boolean);
}

function getLocalizedNews(article, language) {
  return article.translations?.[language] ?? null;
}

function getUserNewsLevel(user) {
  return user?.selected_agent === 'nova' ? 'advanced' : 'beginner';
}

function getNewsSummaryForLevel(copy, level) {
  if (level === 'advanced') {
    return copy.advanced_summary || copy.short_summary || copy.beginner_summary;
  }

  return copy.beginner_summary || copy.short_summary || copy.advanced_summary;
}

function getImportanceTone(score) {
  if (score >= 75) {
    return {
      dot: 'bg-error',
      ring: 'border-error/50 bg-error/15 text-error',
      labelKey: 'dashboard.highImportance',
      noteKey: 'dashboard.highImportanceNote',
    };
  }

  if (score >= 45) {
    return {
      dot: 'bg-secondary',
      ring: 'border-secondary/50 bg-secondary/15 text-secondary',
      labelKey: 'dashboard.mediumImportance',
      noteKey: 'dashboard.mediumImportanceNote',
    };
  }

  return {
    dot: 'bg-on-surface-variant',
    ring: 'border-white/10 bg-white/5 text-on-surface-variant',
    labelKey: 'dashboard.lowImportance',
    noteKey: 'dashboard.lowImportanceNote',
  };
}

function getFallbackImage(article) {
  const key = `${article.id ?? article.source_url ?? article.headline ?? ''}`;
  const hash = Array.from(key).reduce((total, char) => total + char.charCodeAt(0), 0);

  return FALLBACK_IMAGES[hash % FALLBACK_IMAGES.length];
}

function formatNewsDate(value, language) {
  if (!value) return '';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';

  return new Intl.DateTimeFormat(language, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function loadLearningProgress() {
  try {
    return JSON.parse(localStorage.getItem(LEARNING_PROGRESS_STORAGE_KEY)) || {};
  } catch {
    return {};
  }
}

function getCourseProgress(course, progress) {
  const activeLessons = course.lessons.filter((lesson) => lesson.is_active);
  const completed = activeLessons.filter((lesson) => progress[lesson.id]?.status === 'completed').length;
  const total = activeLessons.length;

  return {
    completed,
    total,
    percentage: total ? Math.round((completed / total) * 100) : 0,
  };
}

function getLearningPreview(courses, progress) {
  const activeCourses = courses.filter((course) => course.is_active);
  const activeLessons = activeCourses.flatMap((course) =>
    course.lessons
      .filter((lesson) => lesson.is_active)
      .map((lesson) => ({ course, lesson }))
  );

  const currentLearning =
    activeLessons.find(({ lesson }) => progress[lesson.id]?.status === 'in_progress') ||
    activeLessons.find(({ lesson }) => progress[lesson.id]?.status !== 'completed') ||
    activeLessons[0];

  if (!currentLearning) return null;

  return {
    ...currentLearning,
    courseProgress: getCourseProgress(currentLearning.course, progress),
  };
}

function NewsCard({ article, language, onOpen, t }) {
  const copy = getLocalizedNews(article, language);
  if (!copy) return null;

  const importance = getImportanceTone(article.importance_score);
  const publishedDate = formatNewsDate(article.published_at, language);
  const tags = [...(article.tags ?? []), ...(article.mentioned_assets ?? [])]
    .filter(Boolean)
    .slice(0, 4);

  return (
    <article className="overflow-hidden rounded-xl border border-white/10 bg-surface-container-high/80 shadow-sm">
      <button
        type="button"
        className="block w-full text-left"
        onClick={() => onOpen(article)}
      >
        <div className="relative aspect-[16/10] w-full overflow-hidden bg-surface-container-lowest">
          <img
            className="h-full w-full object-cover transition-transform duration-500 hover:scale-105"
            src={article.image_url || getFallbackImage(article)}
            alt={article.image_alt || copy.headline}
            loading="lazy"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent"></div>
          <div className="absolute left-4 top-4 flex flex-wrap gap-2">
            <span className="inline-flex items-center gap-1 rounded-full bg-surface/90 px-3 py-1 font-label-sm text-label-sm text-on-surface backdrop-blur">
              <span className="material-symbols-outlined text-[16px]">{NEWS_TYPE_ICON[article.news_type]}</span>
              {t(NEWS_TYPE_LABEL_KEYS[article.news_type] ?? 'dashboard.market')}
              <span
                className={`ml-1 h-2 w-2 shrink-0 rounded-full ${importance.dot}`}
                aria-label={`${t('dashboard.importance')}: ${t(importance.labelKey)}`}
                title={`${t('dashboard.importance')}: ${t(importance.labelKey)}`}
              ></span>
            </span>
          </div>
        </div>

        <div className="space-y-3 p-4">
          <div className="flex items-start justify-between gap-3">
            <span className="min-w-0 break-words font-label-sm text-label-sm leading-snug text-on-surface-variant">
              {article.source_name}{publishedDate ? ` · ${publishedDate}` : ''}
            </span>
            <span className="material-symbols-outlined mt-0.5 shrink-0 text-[18px] text-secondary">chevron_right</span>
          </div>

          <div className="space-y-2">
            <h4 className="font-title-md text-title-md leading-tight text-on-surface">
              {copy.headline}
            </h4>
            <p className="font-body-md text-body-md text-on-surface-variant line-clamp-3">
              {copy.subtitle || copy.short_summary}
            </p>
          </div>

          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => (
                <span
                  key={`${article.id}-${tag}`}
                  className="rounded-full bg-surface-container-lowest px-2.5 py-1 font-label-sm text-label-sm text-on-surface-variant"
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </button>
    </article>
  );
}

function NewsDetailModal({ article, language, onClose, t, userLevel }) {
  const copy = article ? getLocalizedNews(article, language) : null;
  const importance = article ? getImportanceTone(article.importance_score) : null;
  const tags = article
    ? [...(article.tags ?? []), ...(article.mentioned_assets ?? [])].filter(Boolean).slice(0, 8)
    : [];

  useEffect(() => {
    if (!article) return undefined;

    const scrollY = window.scrollY;
    const previousBodyStyle = {
      overflow: document.body.style.overflow,
      position: document.body.style.position,
      top: document.body.style.top,
      width: document.body.style.width,
    };

    document.body.style.overflow = 'hidden';
    document.body.style.position = 'fixed';
    document.body.style.top = `-${scrollY}px`;
    document.body.style.width = '100%';

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = previousBodyStyle.overflow;
      document.body.style.position = previousBodyStyle.position;
      document.body.style.top = previousBodyStyle.top;
      document.body.style.width = previousBodyStyle.width;
      window.scrollTo(0, scrollY);
    };
  }, [article, onClose]);

  if (!article || !copy) return null;

  const summary = getNewsSummaryForLevel(copy, userLevel);
  const publishedDate = formatNewsDate(article.published_at, language);

  return (
    <div className="fixed inset-0 z-[80] flex items-end justify-center overflow-hidden bg-black/70 px-3 py-4 backdrop-blur-sm sm:items-center">
      <button
        type="button"
        className="absolute inset-0 cursor-default"
        onClick={onClose}
        aria-label={t('common.close')}
      ></button>

      <section
        className="relative flex h-[88dvh] max-h-[720px] w-full max-w-md flex-col overflow-hidden rounded-2xl border border-white/10 bg-surface-container-high shadow-2xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="news-detail-title"
      >
        <div className="relative aspect-[16/9] w-full shrink-0 overflow-hidden bg-surface-container-lowest">
          <img
            className="h-full w-full object-cover"
            src={article.image_url || getFallbackImage(article)}
            alt={article.image_alt || copy.headline}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent"></div>
          <button
            type="button"
            className="absolute right-3 top-3 flex h-10 w-10 items-center justify-center rounded-full bg-black/65 text-on-surface backdrop-blur transition-colors hover:bg-black/80"
            onClick={onClose}
            aria-label={t('common.close')}
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
          <div className="absolute bottom-4 left-4 right-4 flex flex-wrap gap-2">
            <span className="inline-flex items-center gap-1 rounded-full bg-surface/90 px-3 py-1 font-label-sm text-label-sm text-on-surface backdrop-blur">
              <span className="material-symbols-outlined text-[16px]">{NEWS_TYPE_ICON[article.news_type]}</span>
              {t(NEWS_TYPE_LABEL_KEYS[article.news_type] ?? 'dashboard.market')}
            </span>
          </div>
        </div>

        <div className="min-h-0 flex-1 space-y-5 overflow-y-auto overscroll-contain p-5">
          <div className="space-y-3">
            <div className="font-label-sm text-label-sm text-on-surface-variant">
              <span className="block break-words leading-snug">
                {article.source_name}{publishedDate ? ` · ${publishedDate}` : ''}
              </span>
            </div>

            <h2 id="news-detail-title" className="font-title-lg text-title-lg leading-tight text-on-surface">
              {copy.headline}
            </h2>

            {copy.subtitle && (
              <p className="font-body-md text-body-md text-on-surface-variant">
                {copy.subtitle}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <p className="font-label-md text-label-md uppercase text-secondary">
              {t('dashboard.summary')}
            </p>
            <p className="whitespace-pre-line font-body-md text-body-md leading-relaxed text-on-surface">
              {summary}
            </p>
          </div>

          <div className="rounded-xl border border-white/10 bg-surface-container/70 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="font-label-md text-label-md uppercase text-on-surface-variant">
                {t('dashboard.importance')}
              </p>
              <span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 font-label-sm text-label-sm ${importance.ring}`}>
                <span className={`h-2 w-2 rounded-full ${importance.dot}`}></span>
                {t(importance.labelKey)}
              </span>
            </div>
            <p className="mt-2 font-label-sm text-label-sm text-on-surface-variant">
              {t(importance.noteKey)}
            </p>
          </div>

          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => (
                <span
                  key={`modal-${article.id}-${tag}`}
                  className="rounded-full bg-surface-container-lowest px-2.5 py-1 font-label-sm text-label-sm text-on-surface-variant"
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </div>

        {article.source_url && (
          <div className="shrink-0 border-t border-white/10 bg-surface-container-high px-4 pb-[calc(1rem+env(safe-area-inset-bottom))] pt-4">
            <a
              className="flex w-full items-center justify-center gap-2 rounded-full bg-[#f2ae2e] px-5 py-3 font-label-md text-label-md text-black transition-transform active:scale-[0.98]"
              href={article.source_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              <span className="material-symbols-outlined text-[18px]">open_in_new</span>
              {t('dashboard.readOriginal')}
            </a>
          </div>
        )}
      </section>
    </div>
  );
}

export default function Dashboard() {
  const { language, t } = useI18n();
  const navigate = useNavigate();
  const [activeCategory, setActiveCategory] = useState('all');
  const [news, setNews] = useState([]);
  const [isLoadingNews, setIsLoadingNews] = useState(true);
  const [isLoadingMoreNews, setIsLoadingMoreNews] = useState(false);
  const [newsError, setNewsError] = useState('');
  const [newsSearchQuery, setNewsSearchQuery] = useState('');
  const [newsDateRange, setNewsDateRange] = useState('24h');
  const [newsPage, setNewsPage] = useState(1);
  const [hasNextNewsPage, setHasNextNewsPage] = useState(false);
  const [learningProgress, setLearningProgress] = useState(loadLearningProgress);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [currentUser] = useState(() => getCurrentUser());
  const courses = useMemo(() => getCourses(language), [language]);
  const allowedNewsTypes = useMemo(
    () => mapUserInterestsToNewsTypes(currentUser?.onboarding_interests),
    [currentUser?.onboarding_interests]
  );
  const categories = useMemo(() => {
    const available = allowedNewsTypes.length > 0
      ? allowedNewsTypes
      : Object.values(INTEREST_TO_NEWS_TYPE);

    return [
      { id: 'all', label: t('dashboard.all') },
      ...available.map((newsType) => ({
        id: newsType,
        label: t(NEWS_TYPE_LABEL_KEYS[newsType] ?? 'dashboard.market'),
      })),
    ];
  }, [allowedNewsTypes, t]);

  const learningPreview = useMemo(
    () => getLearningPreview(courses, learningProgress),
    [courses, learningProgress]
  );
  const filteredNews = activeCategory === 'all'
    ? news
    : news.filter((article) => article.news_type === activeCategory);
  const normalizedNewsSearchQuery = newsSearchQuery.trim().toLocaleLowerCase(language);
  const localizedNews = filteredNews.filter((article) => {
    const copy = getLocalizedNews(article, language);
    if (!copy) return false;
    if (!normalizedNewsSearchQuery) return true;

    const searchableText = [
      copy.headline,
      copy.subtitle,
      copy.short_summary,
      copy.beginner_summary,
      copy.advanced_summary,
      article.source_name,
      ...(article.tags ?? []),
      ...(article.mentioned_assets ?? []),
    ]
      .filter(Boolean)
      .join(' ')
      .toLocaleLowerCase(language);

    return searchableText.includes(normalizedNewsSearchQuery);
  });
  const visibleNews = localizedNews;
  const hasMoreNews = hasNextNewsPage;
  const userNewsLevel = getUserNewsLevel(currentUser);

  useEffect(() => {
    let isMounted = true;

    async function loadNews() {
      setIsLoadingNews(true);
      setNewsError('');

      try {
        const data = await getNewsArticles({
          newsTypes: allowedNewsTypes,
          dateRange: newsDateRange,
          page: 1,
          pageSize: NEWS_PAGE_SIZE,
        });
        if (isMounted) {
          setNews(Array.isArray(data) ? data : data.results ?? []);
          setNewsPage(1);
          setHasNextNewsPage(Boolean(data?.next));
        }
      } catch (error) {
        if (isMounted) {
          setNewsError(translateApiError(error, t));
        }
      } finally {
        if (isMounted) {
          setIsLoadingNews(false);
        }
      }
    }

    loadNews();

    return () => {
      isMounted = false;
    };
  }, [allowedNewsTypes, newsDateRange, t]);

  useEffect(() => {
    setSelectedArticle(null);
  }, [activeCategory, language, newsSearchQuery, newsDateRange]);

  useEffect(() => {
    const refreshLearningProgress = () => setLearningProgress(loadLearningProgress());

    window.addEventListener('focus', refreshLearningProgress);
    window.addEventListener('storage', refreshLearningProgress);

    return () => {
      window.removeEventListener('focus', refreshLearningProgress);
      window.removeEventListener('storage', refreshLearningProgress);
    };
  }, []);

  const openLearningPreview = () => {
    if (!learningPreview) {
      navigate('/learn');
      return;
    }

    navigate(`/learn?course=${learningPreview.course.id}&lesson=${learningPreview.lesson.id}`);
  };

  const showMoreNews = async () => {
    if (isLoadingMoreNews || !hasNextNewsPage) return;

    setIsLoadingMoreNews(true);
    setNewsError('');

    try {
      const nextPage = newsPage + 1;
      const data = await getNewsArticles({
        newsTypes: allowedNewsTypes,
        dateRange: newsDateRange,
        page: nextPage,
        pageSize: NEWS_PAGE_SIZE,
      });
      const rows = Array.isArray(data) ? data : data.results ?? [];
      setNews((current) => [...current, ...rows]);
      setNewsPage(nextPage);
      setHasNextNewsPage(Boolean(data?.next));
    } catch (error) {
      setNewsError(translateApiError(error, t));
    } finally {
      setIsLoadingMoreNews(false);
    }
  };

  return (
    <div className="bg-background text-on-surface min-h-screen pb-24">
      <TopBar />

      <main className="pt-20 px-container-padding space-y-stack-lg max-w-md mx-auto">
        {learningPreview && (
          <section className="relative overflow-hidden rounded-xl glass-card pulse-border-green group">
            <button
              type="button"
              className="flex w-full gap-3 p-3 text-left active:scale-[0.99] transition-transform"
              onClick={openLearningPreview}
            >
              <div className="relative h-24 w-28 shrink-0 overflow-hidden rounded-lg bg-surface-container-high">
                <img
                  alt=""
                  className="h-full w-full object-cover opacity-75 transition-transform duration-500 group-hover:scale-105"
                  src={learningPreview.course.thumbnail_url}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
                <div className="absolute bottom-2 left-2 flex h-8 w-8 items-center justify-center rounded-full bg-black/75">
                  <span className="material-symbols-outlined text-[20px] text-secondary">play_arrow</span>
                </div>
              </div>

              <div className="min-w-0 flex-1 space-y-2">
                <div>
                  <p className="mb-1 font-label-sm text-label-sm uppercase text-secondary">
                    {t('dashboard.continueLearning')}
                  </p>
                  <h2 className="truncate font-title-md text-title-md leading-tight text-on-surface">
                    {learningPreview.lesson.title}
                  </h2>
                  <p className="mt-1 truncate font-label-sm text-label-sm text-on-surface-variant">
                    {learningPreview.course.title}
                  </p>
                </div>

                <div>
                  <div className="mb-1 flex items-center justify-between">
                    <span className="font-label-sm text-label-sm text-on-surface-variant">
                      {learningPreview.courseProgress.completed}/{learningPreview.courseProgress.total} {t('learn.lessonsCompleted')}
                    </span>
                    <span className="font-mono-data text-label-sm text-metric">
                      {learningPreview.courseProgress.percentage}%
                    </span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-white/5">
                    <div
                      className="h-full rounded-full bg-metric"
                      style={{ width: `${learningPreview.courseProgress.percentage}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </button>
          </section>
        )}

        <div className="space-y-stack-md">
          <div className="flex items-center justify-between">
            <h3 className="font-title-md text-title-md text-on-surface">{t('dashboard.dailyFeed')}</h3>
          </div>

          <div className="sticky top-16 z-20 -mx-container-padding space-y-2 bg-background/90 px-container-padding py-2 backdrop-blur-xl">
            <label className="relative block">
              <span className="sr-only">{t('dashboard.searchNews')}</span>
              <span className="material-symbols-outlined pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[19px] text-on-surface-variant">
                search
              </span>
              <input
                className="w-full rounded-full border border-white/10 bg-surface-container-lowest py-2.5 pl-10 pr-10 font-body-md text-body-md text-on-surface outline-none placeholder:text-on-surface-variant focus:border-[#f2ae2e]/70 focus:ring-2 focus:ring-[#f2ae2e]/20"
                type="search"
                value={newsSearchQuery}
                onChange={(event) => setNewsSearchQuery(event.target.value)}
                placeholder={t('dashboard.searchNewsPlaceholder')}
              />
              {newsSearchQuery && (
                <button
                  type="button"
                  className="absolute right-2 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container"
                  onClick={() => setNewsSearchQuery('')}
                  aria-label={t('common.close')}
                >
                  <span className="material-symbols-outlined text-[18px]">close</span>
                </button>
              )}
            </label>

            <CategoryChips
              categories={categories}
              activeCategory={activeCategory}
              onCategoryChange={setActiveCategory}
              className="py-0"
            />
          </div>

          <MarketCarousel
            lang={language}
            selectedFeedFilter={activeCategory}
            userInterests={currentUser?.onboarding_interests ?? []}
            searchQuery={newsSearchQuery}
          />

          <div className="flex items-center justify-between gap-3">
            <p className="font-label-sm text-label-sm uppercase text-on-surface-variant">
              {t('dashboard.newsDateRange')}
            </p>
            <label className="relative shrink-0">
              <span className="sr-only">{t('dashboard.newsDateRange')}</span>
              <span className="material-symbols-outlined pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[17px] text-secondary">
                calendar_today
              </span>
              <select
                className="appearance-none rounded-full border border-white/10 bg-surface-container-high py-2 pl-9 pr-9 font-label-md text-label-md text-on-surface outline-none transition-colors hover:border-white/20 focus:border-[#f2ae2e]/70 focus:ring-2 focus:ring-[#f2ae2e]/20"
                value={newsDateRange}
                onChange={(event) => setNewsDateRange(event.target.value)}
              >
                {NEWS_DATE_RANGE_OPTIONS.map((option) => (
                  <option key={option.id} value={option.id}>
                    {t(option.labelKey)}
                  </option>
                ))}
              </select>
              <span className="material-symbols-outlined pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-[18px] text-on-surface-variant">
                expand_more
              </span>
            </label>
          </div>

          {isLoadingNews && (
            <GlassCard className="p-6 text-center font-body-md text-body-md text-on-surface-variant">
              {t('dashboard.loadingNews')}
            </GlassCard>
          )}

          {!isLoadingNews && newsError && (
            <GlassCard className="p-6 text-center font-body-md text-body-md text-error">
              {newsError}
            </GlassCard>
          )}

          {!isLoadingNews && !newsError && localizedNews.length === 0 && (
            <GlassCard className="p-6 text-center font-body-md text-body-md text-on-surface-variant">
              {newsSearchQuery.trim() ? t('dashboard.noNewsSearch') : t('dashboard.noNews')}
            </GlassCard>
          )}

          {!isLoadingNews && !newsError && visibleNews.map((article) => (
            <NewsCard
              key={article.id}
              article={article}
              language={language}
              onOpen={setSelectedArticle}
              t={t}
            />
          ))}

          {!isLoadingNews && !newsError && hasMoreNews && (
            <button
              type="button"
              className="mx-auto flex items-center justify-center gap-2 rounded-full border border-[#f2ae2e]/50 bg-[#f2ae2e]/10 px-5 py-3 font-label-md text-label-md text-[#f2ae2e] shadow-[0_0_14px_rgba(242,174,46,0.12)] transition-all hover:border-[#f2ae2e] hover:bg-[#f2ae2e]/15 active:scale-[0.98]"
              onClick={showMoreNews}
              disabled={isLoadingMoreNews}
            >
              <span className="material-symbols-outlined text-[18px]">expand_more</span>
              {isLoadingMoreNews ? t('dashboard.loadingNews') : t('dashboard.viewMore')}
            </button>
          )}
        </div>
      </main>
      <NewsDetailModal
        article={selectedArticle}
        language={language}
        onClose={() => setSelectedArticle(null)}
        t={t}
        userLevel={userNewsLevel}
      />
      <BottomNav />
    </div>
  );
}
