import React, { useEffect, useMemo, useRef, useState } from 'react';
import { getLatestMarketSnapshots } from '../../api/market';

const INTEREST_TO_MARKET_CATEGORY = {
  crypto: 'CRYPTO',
  stocks: 'INDEX',
  stock_market: 'INDEX',
  forex: 'FOREX',
  savings: 'GENERAL',
  investing_basics: 'GENERAL',
};

const FEED_FILTER_TO_MARKET_CATEGORY = {
  crypto: 'CRYPTO',
  stock_market: 'INDEX',
  forex: 'FOREX',
  investing_basics: 'GENERAL',
};

const DIRECTION_STYLES = {
  UP: {
    icon: 'trending_up',
    tone: 'border-secondary/30 bg-secondary/10 text-secondary',
    text: 'text-secondary',
  },
  DOWN: {
    icon: 'trending_down',
    tone: 'border-error/35 bg-error/10 text-error',
    text: 'text-error',
  },
  FLAT: {
    icon: 'trending_flat',
    tone: 'border-white/10 bg-white/5 text-on-surface-variant',
    text: 'text-on-surface-variant',
  },
  UNKNOWN: {
    icon: 'remove',
    tone: 'border-white/10 bg-white/5 text-on-surface-variant',
    text: 'text-on-surface-variant',
  },
};

function allowedCategoriesFromInterests(userInterests = []) {
  const categories = userInterests.map((interest) => INTEREST_TO_MARKET_CATEGORY[interest]).filter(Boolean);
  return categories.length > 0 ? categories : Object.values(INTEREST_TO_MARKET_CATEGORY);
}

function categoriesForFilter(selectedFeedFilter, userInterests) {
  const allowed = allowedCategoriesFromInterests(userInterests);
  const selectedCategory = FEED_FILTER_TO_MARKET_CATEGORY[selectedFeedFilter];

  if (selectedCategory) {
    return allowed.includes(selectedCategory) ? [selectedCategory] : [];
  }

  return allowed;
}

function normalizeSearchText(value, lang) {
  return String(value ?? '').trim().toLocaleLowerCase(lang === 'pl' ? 'pl-PL' : 'en-US');
}

function marketItemMatchesSearch(item, searchQuery, lang) {
  const query = normalizeSearchText(searchQuery, lang);
  if (!query) return true;

  const searchableText = [
    item.symbol,
    item.name,
    item.category,
    item.subcategory,
    item.unit,
    item.unit_label,
    item.default_detail,
    item.source_name,
  ]
    .filter(Boolean)
    .join(' ')
    .toLocaleLowerCase(lang === 'pl' ? 'pl-PL' : 'en-US');

  return searchableText.includes(query);
}

function formatNumber(value, item, lang) {
  if (value === null || value === undefined || value === '') return '-';

  const number = Number(value);
  if (!Number.isFinite(number)) return String(value);

  const locale = 'de-DE';
  const fractionDigits = item.category === 'FOREX' ? 4 : 2;

  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: 0,
    maximumFractionDigits: fractionDigits,
  }).format(number);
}

function formatPercent(value, lang) {
  if (value === null || value === undefined || value === '') return '--';

  const number = Number(value);
  if (!Number.isFinite(number)) return '--';

  const locale = 'de-DE';
  const sign = number > 0 ? '+' : '';

  return `${sign}${new Intl.NumberFormat(locale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(number)}%`;
}

function formatSignedNumber(value, item, lang) {
  if (value === null || value === undefined || value === '') return '--';

  const number = Number(value);
  if (!Number.isFinite(number)) return String(value);

  const sign = number > 0 ? '+' : '';
  return `${sign}${formatNumber(value, item, lang)}`;
}

function formatMarketDate(item, lang) {
  const raw = item.effective_at_raw || item.effective_datetime;
  if (!raw) return '';

  if (/^\d{4}-\d{2}$/.test(raw) || /^\d{4}-Q[1-4]$/.test(raw)) {
    return raw;
  }

  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return raw;

  const locale = lang === 'pl' ? 'pl-PL' : 'en-US';
  const hasTime = raw.includes('T');

  return new Intl.DateTimeFormat(locale, {
    day: 'numeric',
    month: 'short',
    ...(hasTime ? { hour: '2-digit', minute: '2-digit' } : {}),
  }).format(date);
}

function formatFullMarketDate(item, lang) {
  const raw = item.effective_at_raw || item.effective_datetime;
  if (!raw) return '';

  if (/^\d{4}-\d{2}$/.test(raw) || /^\d{4}-Q[1-4]$/.test(raw)) {
    return raw;
  }

  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return raw;

  const locale = lang === 'pl' ? 'pl-PL' : 'en-US';
  const hasTime = raw.includes('T');

  return new Intl.DateTimeFormat(locale, {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    ...(hasTime ? { hour: '2-digit', minute: '2-digit' } : {}),
  }).format(date);
}

function MarketSkeleton() {
  return (
    <section className="-mx-container-padding overflow-hidden px-container-padding">
      <div className="flex gap-3">
        {[0, 1, 2].map((item) => (
          <div
            key={item}
            className="h-[112px] min-w-[168px] animate-pulse rounded-xl border border-white/10 bg-surface-container-high/70 p-3"
          >
            <div className="mb-4 h-4 w-14 rounded-full bg-white/10"></div>
            <div className="mb-2 h-5 w-24 rounded bg-white/10"></div>
            <div className="h-4 w-20 rounded bg-white/10"></div>
          </div>
        ))}
      </div>
    </section>
  );
}

function localizedLabels(lang) {
  return lang === 'pl'
    ? {
        close: 'Zamknij',
        current: 'Wartość',
        change: 'Zmiana',
        comparison: 'Porównanie',
        previous: 'Poprzednia wartość',
        source: 'Źródło',
        date: 'Data',
        category: 'Kategoria',
        details: 'Szczegóły KPI',
        unavailable: 'Brak danych',
      }
    : {
        close: 'Close',
        current: 'Value',
        change: 'Change',
        comparison: 'Comparison',
        previous: 'Previous value',
        source: 'Source',
        date: 'Date',
        category: 'Category',
        details: 'KPI details',
        unavailable: 'Unavailable',
      };
}

function MarketCard({ item, lang, onOpen }) {
  const direction = DIRECTION_STYLES[item.direction] ?? DIRECTION_STYLES.UNKNOWN;
  const updateLabel = lang === 'pl' ? 'Aktualizacja' : 'Updated';

  return (
    <button
      type="button"
      className="block min-w-[172px] max-w-[172px] rounded-xl border border-white/10 bg-surface-container-high/80 p-3 text-left shadow-sm backdrop-blur transition-colors active:bg-surface-container-highest/80"
      onClick={() => onOpen(item)}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-label-md text-label-md text-on-surface">{item.symbol}</p>
          <p className="truncate font-label-sm text-label-sm text-on-surface-variant">{item.name}</p>
        </div>
        <span className={`inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full border ${direction.tone}`}>
          <span className="material-symbols-outlined text-[17px]">{direction.icon}</span>
        </span>
      </div>

      <div className="space-y-1">
        <p className="truncate font-title-md text-title-md leading-tight text-on-surface">
          {formatNumber(item.current_value, item, lang)}
          <span className="ml-1 font-label-sm text-label-sm text-on-surface-variant">{item.unit_label || item.unit}</span>
        </p>
        <div className="flex items-center justify-between gap-2">
          <span className={`font-label-sm text-label-sm ${direction.text}`}>
            {formatPercent(item.change_percent, lang)}
          </span>
        </div>
      </div>

      <p className="mt-3 truncate font-label-sm text-label-sm text-on-surface-variant">
        {updateLabel}: {formatMarketDate(item, lang)}
      </p>
    </button>
  );
}

function DetailRow({ label, value, valueClassName = 'text-on-surface' }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-white/5 py-2 last:border-b-0">
      <span className="font-label-sm text-label-sm text-on-surface-variant">{label}</span>
      <span className={`max-w-[60%] text-right font-label-md text-label-md ${valueClassName}`}>
        {value}
      </span>
    </div>
  );
}

function MarketDetailModal({ item, lang, onClose }) {
  const labels = localizedLabels(lang);
  const direction = DIRECTION_STYLES[item.direction] ?? DIRECTION_STYLES.UNKNOWN;
  const formattedDate = formatFullMarketDate(item, lang) || item.effective_at_raw || labels.unavailable;
  const currentValue = `${formatNumber(item.current_value, item, lang)} ${item.unit_label || item.unit}`;
  const previousValue = item.previous_value === null || item.previous_value === undefined
    ? labels.unavailable
    : `${formatNumber(item.previous_value, item, lang)} ${item.unit_label || item.unit}`;

  return (
    <div className="fixed inset-0 z-[90] flex items-end justify-center bg-black/55 px-3 pb-[calc(1rem+env(safe-area-inset-bottom))] pt-4 backdrop-blur-sm sm:items-center">
      <button
        type="button"
        className="absolute inset-0 cursor-default"
        onClick={onClose}
        aria-label={labels.close}
      ></button>

      <section
        className="relative w-full max-w-sm rounded-2xl border border-white/10 bg-surface-container-high p-4 shadow-2xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="market-detail-title"
      >
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="font-label-sm text-label-sm uppercase text-secondary">{labels.details}</p>
            <h3 id="market-detail-title" className="mt-1 font-title-md text-title-md leading-tight text-on-surface">
              {item.symbol}
            </h3>
            <p className="truncate font-body-md text-body-md text-on-surface-variant">{item.name}</p>
          </div>

          <button
            type="button"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface-container-lowest text-on-surface-variant transition-colors active:bg-surface-container"
            onClick={onClose}
            aria-label={labels.close}
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>

        <div className="mb-4 rounded-xl border border-white/10 bg-surface-container-lowest/70 p-3">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="font-label-sm text-label-sm text-on-surface-variant">{labels.current}</p>
              <p className="mt-1 break-words font-title-md text-title-md text-on-surface">{currentValue}</p>
            </div>
            <div className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 ${direction.tone}`}>
              <span className="material-symbols-outlined text-[16px]">{direction.icon}</span>
              <span className="font-label-sm text-label-sm">{formatPercent(item.change_percent, lang)}</span>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-white/10 bg-surface-container/70 px-3">
          <DetailRow
            label={labels.change}
            value={`${formatSignedNumber(item.change_absolute, item, lang)} / ${formatPercent(item.change_percent, lang)}`}
            valueClassName={direction.text}
          />
          <DetailRow label={labels.comparison} value={item.default_detail || labels.unavailable} />
          <DetailRow label={labels.previous} value={previousValue} />
          <DetailRow label={labels.date} value={formattedDate} />
          <DetailRow label={labels.source} value={item.source_name || labels.unavailable} />
          <DetailRow label={labels.category} value={`${item.category} · ${item.subcategory}`} />
        </div>
      </section>
    </div>
  );
}

export default function MarketCarousel({ lang, selectedFeedFilter, userInterests, searchQuery = '' }) {
  const [items, setItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedItem, setSelectedItem] = useState(null);
  const scrollerRef = useRef(null);
  const pauseUntilRef = useRef(0);
  const isNormalizingRef = useRef(false);
  const marqueePositionRef = useRef(0);
  const categories = useMemo(
    () => categoriesForFilter(selectedFeedFilter, userInterests),
    [selectedFeedFilter, userInterests]
  );
  const marqueeItems = useMemo(
    () => (items.length > 1 ? [...items, ...items, ...items] : items),
    [items]
  );

  useEffect(() => {
    let isMounted = true;

    async function loadMarkets() {
      if (categories.length === 0) {
        setItems([]);
        setIsLoading(false);
        setError('');
        return;
      }

      setIsLoading(true);
      setError('');

      try {
        const selectedCategory = categories.length === 1 ? categories[0] : undefined;
        const data = await getLatestMarketSnapshots({
          featured: true,
          category: selectedCategory,
          lang,
        });
        const rows = Array.isArray(data) ? data : data.results ?? [];
        const filteredRows = selectedCategory
          ? rows
          : rows.filter((row) => categories.includes(row.category));
        const searchedRows = filteredRows.filter((row) => marketItemMatchesSearch(row, searchQuery, lang));
        const sortedRows = [...searchedRows].sort((a, b) => a.display_order - b.display_order);

        if (isMounted) {
          setItems(sortedRows);
        }
      } catch (marketError) {
        if (isMounted) {
          setError(marketError.message || 'Unable to load market data.');
          setItems([]);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadMarkets();

    return () => {
      isMounted = false;
    };
  }, [categories, lang, searchQuery]);

  useEffect(() => {
    const scroller = scrollerRef.current;
    if (!scroller || items.length < 2 || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return undefined;
    }

    let animationFrame;
    let lastTimestamp = 0;
    const segmentWidth = () => scroller.scrollWidth / 3;

    marqueePositionRef.current = segmentWidth();
    scroller.scrollLeft = marqueePositionRef.current;

    function normalizeLoopPosition() {
      const segment = segmentWidth();
      if (!segment) return;

      if (marqueePositionRef.current >= segment * 2) {
        isNormalizingRef.current = true;
        marqueePositionRef.current -= segment;
        scroller.scrollLeft = marqueePositionRef.current;
        isNormalizingRef.current = false;
      } else if (marqueePositionRef.current <= 0) {
        isNormalizingRef.current = true;
        marqueePositionRef.current += segment;
        scroller.scrollLeft = marqueePositionRef.current;
        isNormalizingRef.current = false;
      }
    }

    function tick(timestamp) {
      if (!lastTimestamp) {
        lastTimestamp = timestamp;
      }

      const delta = timestamp - lastTimestamp;
      lastTimestamp = timestamp;

      if (Date.now() > pauseUntilRef.current) {
        marqueePositionRef.current += delta * 0.028;
        scroller.scrollLeft = marqueePositionRef.current;
        normalizeLoopPosition();
      }

      animationFrame = requestAnimationFrame(tick);
    }

    animationFrame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animationFrame);
  }, [items]);

  const pauseAutoScroll = () => {
    pauseUntilRef.current = Date.now() + 2500;
  };

  const openDetail = (item) => {
    pauseUntilRef.current = Date.now() + 5000;
    setSelectedItem(item);
  };

  const handleManualScroll = () => {
    if (isNormalizingRef.current || items.length < 2) return;

    const scroller = scrollerRef.current;
    if (!scroller) return;

    const segment = scroller.scrollWidth / 3;
    if (!segment) return;

    marqueePositionRef.current = scroller.scrollLeft;

    if (marqueePositionRef.current >= segment * 2) {
      isNormalizingRef.current = true;
      marqueePositionRef.current -= segment;
      scroller.scrollLeft = marqueePositionRef.current;
      isNormalizingRef.current = false;
    } else if (marqueePositionRef.current <= 0) {
      isNormalizingRef.current = true;
      marqueePositionRef.current += segment;
      scroller.scrollLeft = marqueePositionRef.current;
      isNormalizingRef.current = false;
    }
  };

  if (isLoading) {
    return <MarketSkeleton />;
  }

  if (error) {
    return (
      <div className="-mx-container-padding px-container-padding">
        <div className="rounded-xl border border-white/10 bg-surface-container-high/70 px-4 py-3 font-label-sm text-label-sm text-on-surface-variant">
          {lang === 'pl' ? 'Dane rynkowe sa chwilowo niedostepne.' : 'Market data is temporarily unavailable.'}
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return null;
  }

  return (
    <section className="-mx-container-padding overflow-hidden px-container-padding">
      <div
        ref={scrollerRef}
        className="hide-scrollbar flex gap-3 overflow-x-auto pb-1"
        onScroll={handleManualScroll}
        onPointerDown={pauseAutoScroll}
        onPointerEnter={pauseAutoScroll}
        onTouchStart={pauseAutoScroll}
        onWheel={pauseAutoScroll}
        aria-label={lang === 'pl' ? 'Najnowsze dane rynkowe' : 'Latest market data'}
      >
        {marqueeItems.map((item, index) => (
          <div key={`${item.symbol}-${item.effective_at_raw}-${index}`}>
            <MarketCard item={item} lang={lang} onOpen={openDetail} />
          </div>
        ))}
      </div>
      {selectedItem && (
        <MarketDetailModal
          item={selectedItem}
          lang={lang}
          onClose={() => setSelectedItem(null)}
        />
      )}
    </section>
  );
}
