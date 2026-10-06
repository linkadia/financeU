import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useI18n } from '../i18n/I18nContext';

function PolicySection({ title, children, id }) {
  return (
    <section className="space-y-2" id={id}>
      <h2 className="text-xl font-semibold text-on-surface">{title}</h2>
      <div className="space-y-3 text-[15px] leading-6 text-on-surface-variant">{children}</div>
    </section>
  );
}

export default function Privacy() {
  const { t } = useI18n();

  useEffect(() => {
    const previousTitle = document.title;
    document.title = t('privacy.policyTitle');

    return () => {
      document.title = previousTitle;
    };
  }, [t]);

  return (
    <div className="min-h-screen bg-background px-container-padding py-8 text-on-surface sm:py-12">
      <main className="mx-auto max-w-3xl space-y-8">
        <header className="space-y-4">
          <Link className="inline-flex text-sm font-semibold text-secondary hover:underline" to="/">
            ← {t('privacy.backToApp')}
          </Link>
          <div className="space-y-2">
            <h1 className="text-3xl font-bold tracking-tight text-on-surface sm:text-4xl">
              {t('privacy.policyTitle')}
            </h1>
            <p className="text-sm text-on-surface-variant">{t('privacy.effectiveDate')}</p>
          </div>
        </header>

        <div className="glass-panel space-y-8 rounded-2xl p-5 sm:p-8">
          <PolicySection title={t('privacy.controllerTitle')}>
            <p>{t('privacy.controller')}</p>
            <p>{t('privacy.email')}</p>
          </PolicySection>

          <PolicySection title={t('privacy.dataTitle')}>
            <p>{t('privacy.dataText')}</p>
          </PolicySection>

          <PolicySection title={t('privacy.purposesTitle')}>
            <p>{t('privacy.purposesText')}</p>
          </PolicySection>

          <PolicySection title={t('privacy.legalBasisTitle')}>
            <p>{t('privacy.legalBasis')}</p>
          </PolicySection>

          <PolicySection title={t('privacy.cookiesTitle')} id="cookies">
            <p>{t('privacy.cookiesIntro')}</p>
            <div className="overflow-x-auto rounded-lg border border-white/10">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-surface-container-high text-on-surface">
                  <tr>
                    <th className="px-4 py-3 font-semibold">{t('privacy.whatWeUse')}</th>
                    <th className="px-4 py-3 font-semibold">{t('privacy.yes')}</th>
                    <th className="px-4 py-3 font-semibold">{t('privacy.retentionTitle')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10 text-on-surface-variant">
                  <tr>
                    <td className="px-4 py-3">{t('privacy.essential')}</td>
                    <td className="px-4 py-3">{t('privacy.yes')}</td>
                    <td className="px-4 py-3">{t('privacy.retention')}</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3">{t('privacy.analytics')}</td>
                    <td className="px-4 py-3">{t('privacy.no')}</td>
                    <td className="px-4 py-3">{t('privacy.analyticsRetention')}</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3">{t('privacy.marketing')}</td>
                    <td className="px-4 py-3">{t('privacy.no')}</td>
                    <td className="px-4 py-3">{t('privacy.marketingDescription')}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </PolicySection>

          <PolicySection title={t('privacy.thirdPartiesTitle')}>
            <p>{t('privacy.thirdParties')}</p>
          </PolicySection>

          <PolicySection title={t('privacy.retentionTitle')}>
            <p>{t('privacy.retention')}</p>
          </PolicySection>

          <PolicySection title={t('privacy.rightsTitle')}>
            <p>{t('privacy.rights')}</p>
            <p>{t('privacy.updatePreferences')}</p>
          </PolicySection>
        </div>
      </main>
    </div>
  );
}
