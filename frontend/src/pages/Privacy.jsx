import React, { useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import LanguageSwitcher from '../components/LanguageSwitcher';
import { useI18n } from '../i18n/I18nContext';
import { useCookieConsent } from '../context/CookieConsentContext';
import logoUrl from '../assets/logoFinancU.svg';

const SECTIONS = [
  ['controller', 'controllerTitle'], ['data', 'dataTitle'], ['purposes', 'purposesTitle'],
  ['legal-basis', 'legalBasisTitle'], ['cookies', 'cookiesTitle'],
  ['third-parties', 'thirdPartiesTitle'], ['retention', 'retentionTitle'], ['rights', 'rightsTitle'],
];

function PolicySection({ title, children, id }) {
  return (
    <section aria-labelledby={`${id}-title`} className="privacy-section" id={id} tabIndex={-1}>
      <h2 id={`${id}-title`}>{title}</h2>
      <div className="privacy-section-copy">{children}</div>
    </section>
  );
}

function CookieCategories({ t }) {
  const categories = [
    { name: t('privacy.essential'), purpose: t('privacy.essentialDescription'), status: t('privacy.alwaysActive'), retention: t('privacy.consentRetention') },
    { name: t('privacy.analytics'), purpose: t('privacy.analyticsDescription'), status: t('privacy.optional'), retention: t('privacy.analyticsRetention') },
  ];

  return (
    <>
      <div className="privacy-cookie-table">
        <table>
          <caption className="sr-only">{t('privacy.whatWeUse')}</caption>
          <thead><tr>
            <th scope="col">{t('privacy.category')}</th><th scope="col">{t('privacy.purpose')}</th>
            <th scope="col">{t('privacy.status')}</th><th scope="col">{t('privacy.retentionTitle')}</th>
          </tr></thead>
          <tbody>{categories.map((category) => <tr key={category.name}>
            <th scope="row">{category.name}</th><td>{category.purpose}</td>
            <td>{category.status}</td><td>{category.retention}</td>
          </tr>)}</tbody>
        </table>
      </div>
      <div className="privacy-cookie-cards">
        {categories.map((category) => <div className="privacy-cookie-card" key={category.name}>
          <div className="cookie-category-heading"><h3>{category.name}</h3><span className="cookie-badge">{category.status}</span></div>
          <p>{category.purpose}</p>
          <dl><dt>{t('privacy.retentionTitle')}</dt><dd>{category.retention}</dd></dl>
        </div>)}
      </div>
    </>
  );
}

export default function Privacy() {
  const { t } = useI18n();
  const { hash } = useLocation();
  const { openPreferences } = useCookieConsent();

  useEffect(() => {
    const previousTitle = document.title;
    document.title = t('privacy.policyTitle');
    return () => { document.title = previousTitle; };
  }, [t]);

  return (
    <div className="privacy-page">
      <header className="privacy-topbar">
        <div className="privacy-topbar-inner">
          <Link aria-label={t('privacy.backToApp')} className="privacy-brand" to="/"><img alt="FinancU" src={logoUrl} /></Link>
          <LanguageSwitcher compact />
        </div>
      </header>
      <main className="privacy-main">
        <div className="privacy-intro">
          <Link className="privacy-back" to="/"><span aria-hidden="true">←</span> {t('privacy.backToApp')}</Link>
          <p className="cookie-eyebrow">FinancU · {t('privacy.bannerTitle')}</p>
          <h1>{t('privacy.policyTitle')}</h1>
          <p className="privacy-lead">{t('privacy.pageIntro')}</p>
          <p className="privacy-lead"><a className="cookie-policy-link" href="https://business.safety.google/privacy/" rel="noopener noreferrer" target="_blank">{t('privacy.googleDataUse')}</a></p>
          <p className="privacy-date">{t('privacy.effectiveDate')}</p>
        </div>
        <div className="privacy-layout">
          <nav aria-label={t('privacy.contents')} className="privacy-contents">
            <p>{t('privacy.contents')}</p>
            {SECTIONS.map(([id, key]) => <Link aria-current={hash === `#${id}` ? 'location' : undefined} key={id} to={`/privacy#${id}`}>{t(`privacy.${key}`)}</Link>)}
          </nav>
          <article className="privacy-article">
            <PolicySection id="controller" title={t('privacy.controllerTitle')}>
              <p>{t('privacy.controller')}</p>
              <p>{t('privacy.email').split('info@kyomudigital.com')[0]}<a href="mailto:info@kyomudigital.com">info@kyomudigital.com</a>.</p>
            </PolicySection>
            <PolicySection id="data" title={t('privacy.dataTitle')}><p>{t('privacy.dataText')}</p></PolicySection>
            <PolicySection id="purposes" title={t('privacy.purposesTitle')}><p>{t('privacy.purposesText')}</p></PolicySection>
            <PolicySection id="legal-basis" title={t('privacy.legalBasisTitle')}><p>{t('privacy.legalBasis')}</p></PolicySection>
            <PolicySection id="cookies" title={t('privacy.cookiesTitle')}>
              <div className="privacy-preferences-callout">
                <div><h3>{t('privacy.settingsTitle')}</h3><p>{t('privacy.preferencesIntro')}</p></div>
                <button className="cookie-button cookie-button-save" onClick={openPreferences} type="button">{t('privacy.cookieSettings')}</button>
                <p className="privacy-preferences-hint">{t('privacy.preferencesHint')}</p>
              </div>
              <p>{t('privacy.cookiesIntro')}</p>
              <CookieCategories t={t} />
              <div className="mt-6 space-y-3">
                <h3 className="text-base font-semibold text-on-surface">{t('privacy.consentRecordTitle')}</h3>
                <p>{t('privacy.consentRecord')}</p>
                <p>{t('privacy.consentRecordRetention')}</p>
              </div>
            </PolicySection>
            <PolicySection id="third-parties" title={t('privacy.thirdPartiesTitle')}><p>{t('privacy.thirdParties')}</p></PolicySection>
            <PolicySection id="retention" title={t('privacy.retentionTitle')}><p>{t('privacy.retention')}</p></PolicySection>
            <PolicySection id="rights" title={t('privacy.rightsTitle')}>
              <p>{t('privacy.rights')}</p><p>{t('privacy.updatePreferences')}</p>
              <button className="cookie-configure privacy-inline-settings" onClick={openPreferences} type="button">{t('privacy.cookieSettings')} <span aria-hidden="true">→</span></button>
            </PolicySection>
          </article>
        </div>
      </main>
    </div>
  );
}
