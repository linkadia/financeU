import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { defaultLanguage, supportedLanguages, translations } from './translations';

const LANGUAGE_KEY = 'finanu.language';
const I18nContext = createContext(null);

function getInitialLanguage() {
  try {
    const stored = localStorage.getItem(LANGUAGE_KEY);
    return supportedLanguages[stored] ? stored : defaultLanguage;
  } catch {
    return defaultLanguage;
  }
}

function interpolate(value, params = {}) {
  return Object.entries(params).reduce(
    (text, [key, replacement]) => text.replaceAll(`{{${key}}}`, replacement),
    value
  );
}

function getTranslation(language, key) {
  return key.split('.').reduce((current, part) => current?.[part], translations[language]);
}

export function I18nProvider({ children }) {
  const [language, setLanguage] = useState(getInitialLanguage);

  useEffect(() => {
    localStorage.setItem(LANGUAGE_KEY, language);
    document.documentElement.lang = language;
  }, [language]);

  const value = useMemo(() => {
    const t = (key, params) => {
      const translated = getTranslation(language, key) ?? getTranslation(defaultLanguage, key) ?? key;
      return typeof translated === 'string' ? interpolate(translated, params) : translated;
    };

    return {
      language,
      languages: Object.values(supportedLanguages),
      setLanguage,
      t,
    };
  }, [language]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);

  if (!context) {
    throw new Error('useI18n must be used inside I18nProvider');
  }

  return context;
}
