import React from 'react';
import { useI18n } from '../i18n/I18nContext';

export default function LanguageSwitcher({ compact = false }) {
  const { language, languages, setLanguage, t } = useI18n();

  return (
    <label className={`inline-flex items-center gap-2 ${compact ? 'text-[12px]' : 'text-[13px]'}`}>
      <span className="sr-only">{t('common.language')}</span>
      <span className="material-symbols-outlined text-[18px] text-on-surface-variant">language</span>
      <select
        aria-label={t('common.language')}
        className="rounded-lg border border-white/10 bg-surface-container px-2 py-1 font-semibold text-on-surface outline-none focus:border-secondary focus:ring-1 focus:ring-secondary"
        value={language}
        onChange={(event) => setLanguage(event.target.value)}
      >
        {languages.map((item) => (
          <option key={item.code} value={item.code}>
            {compact ? item.shortLabel : item.label}
          </option>
        ))}
      </select>
    </label>
  );
}
