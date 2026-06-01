import React, { useEffect, useRef, useState } from 'react';
import { useI18n } from '../i18n/I18nContext';

export default function LanguageSwitcher({ compact = false }) {
  const { language, languages, setLanguage, t } = useI18n();
  const [isOpen, setIsOpen] = useState(false);
  const switcherRef = useRef(null);
  const currentLanguage = languages.find((item) => item.code === language) ?? languages[0];

  useEffect(() => {
    if (!isOpen) return undefined;

    const handlePointerDown = (event) => {
      if (!switcherRef.current?.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('pointerdown', handlePointerDown);
    return () => document.removeEventListener('pointerdown', handlePointerDown);
  }, [isOpen]);

  const selectLanguage = (code) => {
    setLanguage(code);
    setIsOpen(false);
  };

  return (
    <div
      ref={switcherRef}
      className={`relative inline-flex items-center ${compact ? 'text-[12px]' : 'text-[13px]'}`}
    >
      <button
        className="inline-flex min-w-16 items-center justify-between gap-1.5 rounded-full border border-white/10 bg-surface-container px-3 py-1.5 font-semibold leading-none text-on-surface shadow-sm transition-colors hover:bg-surface-container-high focus:outline-none focus-visible:ring-2 focus-visible:ring-secondary"
        type="button"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={t('common.language')}
        onClick={() => setIsOpen((current) => !current)}
      >
        <span>{compact ? currentLanguage.shortLabel : currentLanguage.label}</span>
        <span className="material-symbols-outlined text-[16px] leading-none text-on-surface-variant" aria-hidden="true">
          expand_more
        </span>
      </button>

      {isOpen && (
        <div
          className="absolute right-0 top-[calc(100%+8px)] z-[90] min-w-28 overflow-hidden rounded-xl border border-white/10 bg-surface-container p-1 shadow-2xl"
          role="listbox"
          aria-label={t('common.language')}
        >
          {languages.map((item) => (
            <button
              key={item.code}
              className={`flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2 text-left font-semibold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-secondary ${
                language === item.code
                  ? 'bg-secondary text-on-secondary'
                  : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
              }`}
              type="button"
              role="option"
              aria-selected={language === item.code}
              onClick={() => selectLanguage(item.code)}
            >
              <span>{item.shortLabel}</span>
              <span className="text-[11px] font-medium opacity-80">{item.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
