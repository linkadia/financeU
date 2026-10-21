import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { applyConsent, CONSENT_ACTIONS, getPreferences, readStoredConsent, saveConsent } from '../analytics/consent';
import { flushConsentRecords, recordConsent } from '../analytics/consentRecords';
import { useI18n } from '../i18n/I18nContext';

const CookieConsentContext = createContext(null);

export function CookieConsentProvider({ children }) {
  const { pathname } = useLocation();
  const { language } = useI18n();
  const [consent, setConsent] = useState(readStoredConsent);
  const [isPreferencesOpen, setPreferencesOpen] = useState(false);
  const [draft, setDraft] = useState(() => getPreferences());
  const [bannerHeight, setBannerHeight] = useState(260);
  const [storageWarning, setStorageWarning] = useState(false);
  const openerRef = useRef(null);
  const showBanner = !consent && pathname !== '/privacy' && !isPreferencesOpen;
  const hasBottomNav = ['/dashboard', '/learn', '/profile'].includes(pathname);

  useEffect(() => {
    flushConsentRecords();
    window.addEventListener('online', flushConsentRecords);
    return () => window.removeEventListener('online', flushConsentRecords);
  }, []);

  const restoreFocus = useCallback(() => {
    window.requestAnimationFrame(() => {
      const opener = openerRef.current;
      const target = opener?.isConnected ? opener : document.querySelector('[data-cookie-settings-trigger]');
      target?.focus({ preventScroll: true });
    });
  }, []);

  const openPreferences = useCallback(() => {
    openerRef.current = document.activeElement;
    setDraft(getPreferences(readStoredConsent() || consent));
    setPreferencesOpen(true);
  }, [consent]);

  const closePreferences = useCallback(({ restore = true } = {}) => {
    setPreferencesOpen(false);
    if (restore) restoreFocus();
  }, [restoreFocus]);

  const commitPreferences = useCallback((preferences, action = CONSENT_ACTIONS.custom) => {
    if (!isPreferencesOpen) openerRef.current = document.activeElement;
    const saved = saveConsent(preferences, consent);
    applyConsent(saved);
    setConsent(saved);
    setStorageWarning(!readStoredConsent());
    setPreferencesOpen(false);
    restoreFocus();
    recordConsent(saved, { action, language });
  }, [consent, isPreferencesOpen, language, restoreFocus]);

  return (
    <CookieConsentContext.Provider value={{
      consent, showBanner, hasBottomNav, isPreferencesOpen, draft, setDraft,
      openPreferences, closePreferences, commitPreferences, setBannerHeight, storageWarning,
    }}>
      <div className={showBanner ? 'cookie-entry-layout' : undefined} style={{ '--cookie-banner-space': `${bannerHeight + 24}px` }}>
        {children}
      </div>
    </CookieConsentContext.Provider>
  );
}

export function useCookieConsent() {
  const context = useContext(CookieConsentContext);
  if (!context) throw new Error('useCookieConsent must be used inside CookieConsentProvider');
  return context;
}
