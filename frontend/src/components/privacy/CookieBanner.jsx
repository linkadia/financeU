import React, { useLayoutEffect, useRef } from 'react';
import { Dialog } from '@mui/material';
import { Link } from 'react-router-dom';
import { useI18n } from '../../i18n/I18nContext';
import { useCookieConsent } from '../../context/CookieConsentContext';
import { CONSENT_ACTIONS, EMPTY_PREFERENCES } from '../../analytics/consent';

function CookieIcon() {
  return <span aria-hidden="true" className="material-symbols-outlined">cookie</span>;
}

export default function CookieBanner() {
  const { t } = useI18n();
  const bannerRef = useRef(null);
  const {
    showBanner, hasBottomNav, isPreferencesOpen, draft, setDraft, storageWarning,
    openPreferences, closePreferences, commitPreferences, setBannerHeight,
  } = useCookieConsent();

  useLayoutEffect(() => {
    if (!showBanner || !bannerRef.current) return undefined;
    const banner = bannerRef.current;
    const updateHeight = () => setBannerHeight(banner.getBoundingClientRect().height);
    updateHeight();
    const observer = new ResizeObserver(updateHeight);
    observer.observe(banner);
    return () => observer.disconnect();
  }, [showBanner, setBannerHeight]);

  return (
    <>
      {showBanner && (
        <section aria-labelledby="cookie-banner-title" className={`cookie-banner ${hasBottomNav ? 'cookie-above-nav' : ''}`} ref={bannerRef}>
          <div className="cookie-banner-heading">
            <span className="cookie-icon"><CookieIcon /></span>
            <h2 id="cookie-banner-title">{t('privacy.bannerTitle')}</h2>
          </div>
          <p className="cookie-copy">{t('privacy.bannerDescription')}{' '}
            <Link className="cookie-policy-link" to="/privacy#cookies">{t('privacy.policyLink')}</Link>
          </p>
          <div className="cookie-choice-actions">
            <button className="cookie-button cookie-button-choice" onClick={() => commitPreferences(EMPTY_PREFERENCES, CONSENT_ACTIONS.rejectAll)} type="button">{t('privacy.rejectAll')}</button>
            <button className="cookie-button cookie-button-choice" onClick={() => commitPreferences({ analytics: true }, CONSENT_ACTIONS.acceptAll)} type="button">{t('privacy.acceptAll')}</button>
          </div>
          <button className="cookie-configure" data-cookie-settings-trigger onClick={openPreferences} type="button">{t('privacy.configure')}</button>
        </section>
      )}

      {!showBanner && !isPreferencesOpen && (
        <div className={`cookie-settings-access ${hasBottomNav ? 'cookie-above-nav' : ''}`}>
          {storageWarning && <p className="cookie-storage-warning" role="status">{t('privacy.storageWarning')}</p>}
          <button aria-label={t('privacy.cookieSettings')} className="cookie-settings-trigger" data-cookie-settings-trigger onClick={openPreferences} type="button">
            <CookieIcon /><span className="cookie-trigger-full">{t('privacy.cookieSettings')}</span><span className="cookie-trigger-short" aria-hidden="true">{t('privacy.cookiesShort')}</span>
          </button>
        </div>
      )}

      <Dialog
        open={isPreferencesOpen}
        onClose={closePreferences}
        aria-labelledby="cookie-settings-title"
        aria-describedby="cookie-settings-description"
        disableRestoreFocus
        maxWidth={false}
        transitionDuration={0}
        slotProps={{ paper: { className: 'cookie-preferences' } }}
        sx={{ '& .MuiDialog-container': { alignItems: { xs: 'flex-end', sm: 'center' } } }}
      >
        <header className="cookie-dialog-header">
          <div>
            <p className="cookie-eyebrow">FinancU</p>
            <h2 id="cookie-settings-title">{t('privacy.settingsTitle')}</h2>
          </div>
          <button aria-label={t('privacy.closeSettings')} className="cookie-close" onClick={closePreferences} type="button" autoFocus>
            <span className="material-symbols-outlined" aria-hidden="true">close</span>
          </button>
        </header>
        <div className="cookie-dialog-content">
          <p className="cookie-copy" id="cookie-settings-description">{t('privacy.settingsDescription')}</p>
          <div className="cookie-category">
            <div className="cookie-category-heading"><h3>{t('privacy.essential')}</h3><span className="cookie-badge cookie-badge-active">{t('privacy.alwaysActive')}</span></div>
            <p>{t('privacy.essentialDescription')}</p>
          </div>
          <div className="cookie-category">
            <div className="cookie-category-heading">
              <h3>{t('privacy.analytics')}</h3>
              <button
                aria-checked={draft.analytics} aria-label={t('privacy.analytics')} aria-describedby="cookie-analytics-description"
                className={`cookie-switch ${draft.analytics ? 'is-checked' : ''}`}
                onClick={() => setDraft((current) => ({ ...current, analytics: !current.analytics }))} role="switch" type="button"
              ><span /></button>
            </div>
            <p id="cookie-analytics-description">{t('privacy.analyticsDescription')}</p>
          </div>
          <Link className="cookie-policy-link cookie-dialog-policy" onClick={() => closePreferences({ restore: false })} to="/privacy#cookies">{t('privacy.policyTitle')} <span aria-hidden="true">↗</span></Link>
        </div>
        <footer className="cookie-dialog-actions">
          <button className="cookie-button cookie-button-neutral" onClick={closePreferences} type="button">{t('common.close')}</button>
          <button className="cookie-button cookie-button-save" onClick={() => commitPreferences(draft, CONSENT_ACTIONS.custom)} type="button">{t('privacy.savePreferences')}</button>
        </footer>
      </Dialog>
    </>
  );
}
