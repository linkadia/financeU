import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useI18n } from '../../i18n/I18nContext';
import {
  applyConsent,
  EMPTY_PREFERENCES,
  getPreferences,
  readStoredConsent,
  saveConsent,
} from '../../analytics/consent';

function PreferenceSwitch({ checked, disabled, label, description, onChange }) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-lg border border-white/10 bg-surface-container-lowest p-4">
      <div className="min-w-0">
        <p className="font-semibold text-on-surface">{label}</p>
        <p className="mt-1 text-sm leading-5 text-on-surface-variant">{description}</p>
      </div>
      <button
        aria-checked={checked}
        aria-label={label}
        className={`relative mt-0.5 inline-flex h-7 w-12 shrink-0 items-center rounded-full border p-1 transition-colors focus:outline-none focus:ring-2 focus:ring-secondary focus:ring-offset-2 focus:ring-offset-background ${
          checked ? 'border-secondary bg-secondary' : 'border-white/20 bg-surface-container-high'
        } ${disabled ? 'cursor-not-allowed opacity-80' : ''}`}
        disabled={disabled}
        onClick={onChange}
        role="switch"
        type="button"
      >
        <span
          className={`h-5 w-5 rounded-full bg-white shadow transition-transform ${checked ? 'translate-x-5' : 'translate-x-0'}`}
        />
      </button>
    </div>
  );
}

export default function CookieBanner() {
  const { t } = useI18n();
  const triggerRef = useRef(null);
  const dialogRef = useRef(null);
  const [isVisible, setIsVisible] = useState(() => !readStoredConsent());
  const [isConfiguring, setIsConfiguring] = useState(false);
  const [preferences, setPreferences] = useState(() => getPreferences());
  const [showSettingsTrigger, setShowSettingsTrigger] = useState(() => {
    const stored = readStoredConsent();
    return !stored || !stored.analytics || !stored.marketing;
  });

  useEffect(() => {
    if (!isVisible) return undefined;

    dialogRef.current?.focus();

    const handleKeyDown = (event) => {
      if (event.key === 'Escape' && isConfiguring) {
        setIsConfiguring(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isConfiguring, isVisible]);

  const openSettings = () => {
    setPreferences(getPreferences(readStoredConsent()));
    setIsConfiguring(true);
    setIsVisible(true);
  };

  const commitPreferences = (nextPreferences) => {
    const stored = saveConsent(nextPreferences);
    applyConsent(stored);
    setPreferences(getPreferences(stored));
    setShowSettingsTrigger(!stored.analytics || !stored.marketing);
    setIsConfiguring(false);
    setIsVisible(false);
    window.setTimeout(() => triggerRef.current?.focus(), 0);
  };

  const acceptAll = () => commitPreferences({ analytics: true, marketing: true });
  const rejectAll = () => commitPreferences(EMPTY_PREFERENCES);

  return (
    <>
      {isVisible && (
        <section
          aria-describedby="cookie-banner-description"
          aria-labelledby="cookie-banner-title"
          className="fixed inset-x-4 bottom-24 z-[60] mx-auto max-w-3xl rounded-2xl border border-white/10 bg-surface-container-high p-5 shadow-2xl shadow-black/40 sm:inset-x-6 sm:p-6"
          ref={dialogRef}
          role="dialog"
          tabIndex={-1}
        >
          <div className="space-y-4">
            <div className="space-y-2">
              <h2 className="text-xl font-semibold text-on-surface" id="cookie-banner-title">
                {isConfiguring ? t('privacy.settingsTitle') : t('privacy.bannerTitle')}
              </h2>
              <p className="text-sm leading-6 text-on-surface-variant" id="cookie-banner-description">
                {isConfiguring ? t('privacy.settingsDescription') : t('privacy.bannerDescription')}{' '}
                <Link className="font-semibold text-secondary hover:underline" to="/privacy#cookies">
                  {t('privacy.policyTitle')}
                </Link>
              </p>
            </div>

            {isConfiguring ? (
              <fieldset className="space-y-3" aria-label={t('privacy.whatWeUse')}>
                <PreferenceSwitch
                  checked
                  disabled
                  description={t('privacy.essentialDescription')}
                  label={t('privacy.essential')}
                />
                <PreferenceSwitch
                  checked={preferences.analytics}
                  description={t('privacy.analyticsDescription')}
                  label={t('privacy.analytics')}
                  onChange={() => setPreferences((current) => ({ ...current, analytics: !current.analytics }))}
                />
                <PreferenceSwitch
                  checked={preferences.marketing}
                  description={t('privacy.marketingDescription')}
                  label={t('privacy.marketing')}
                  onChange={() => setPreferences((current) => ({ ...current, marketing: !current.marketing }))}
                />
              </fieldset>
            ) : (
              <div className="rounded-lg border border-white/10 bg-surface-container-lowest p-4 text-sm leading-6 text-on-surface-variant">
                <p>
                  <span className="font-semibold text-on-surface">{t('privacy.essential')}:</span>{' '}
                  {t('privacy.essentialDescription')}
                </p>
                <p className="mt-2">{t('privacy.cookiesIntro')}</p>
              </div>
            )}

            <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
              {isConfiguring ? (
                <>
                  <button
                    className="min-h-11 rounded-lg border border-white/20 bg-surface-container-lowest px-4 py-2.5 text-sm font-semibold text-on-surface transition-colors hover:bg-surface-container-high focus:outline-none focus:ring-2 focus:ring-secondary"
                    onClick={() => setIsConfiguring(false)}
                    type="button"
                  >
                    {t('common.close')}
                  </button>
                  <button
                    className="min-h-11 rounded-lg bg-secondary px-4 py-2.5 text-sm font-semibold text-on-secondary transition-colors hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-secondary focus:ring-offset-2 focus:ring-offset-background"
                    onClick={() => commitPreferences(preferences)}
                    type="button"
                  >
                    {t('privacy.savePreferences')}
                  </button>
                </>
              ) : (
                <>
                  <button
                    className="min-h-11 rounded-lg border border-white/20 bg-surface-container-lowest px-4 py-2.5 text-sm font-semibold text-on-surface transition-colors hover:bg-surface-container-high focus:outline-none focus:ring-2 focus:ring-secondary"
                    onClick={rejectAll}
                    type="button"
                  >
                    {t('privacy.rejectAll')}
                  </button>
                  <button
                    className="min-h-11 rounded-lg border border-white/20 bg-surface-container-lowest px-4 py-2.5 text-sm font-semibold text-on-surface transition-colors hover:bg-surface-container-high focus:outline-none focus:ring-2 focus:ring-secondary"
                    onClick={acceptAll}
                    type="button"
                  >
                    {t('privacy.acceptAll')}
                  </button>
                  <button
                    className="min-h-11 rounded-lg border border-secondary bg-secondary/10 px-4 py-2.5 text-sm font-semibold text-secondary transition-colors hover:bg-secondary/20 focus:outline-none focus:ring-2 focus:ring-secondary"
                    onClick={() => setIsConfiguring(true)}
                    type="button"
                  >
                    {t('privacy.configure')}
                  </button>
                </>
              )}
            </div>
          </div>
        </section>
      )}

      {!isVisible && showSettingsTrigger && (
        <button
          className="fixed bottom-24 right-4 z-[55] rounded-full border border-white/10 bg-surface-container-high px-3 py-2 text-xs font-semibold text-on-surface-variant shadow-lg transition-colors hover:text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary sm:right-6"
          onClick={openSettings}
          ref={triggerRef}
          type="button"
        >
          {t('privacy.cookieSettings')}
        </button>
      )}
    </>
  );
}
