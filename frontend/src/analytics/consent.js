const DEFAULT_COOKIE_NAME = 'financu_cookie_consent';
const DEFAULT_POLICY_VERSION = '1.0';
const CONSENT_COOKIE_MAX_AGE = 60 * 60 * 24 * 180;

const consentConfig = typeof window !== 'undefined' && window.__FINANCU_CONSENT_CONFIG__
  ? window.__FINANCU_CONSENT_CONFIG__
  : {};

export const CONSENT_COOKIE_NAME = consentConfig.cookieName || DEFAULT_COOKIE_NAME;
export const COOKIE_POLICY_VERSION = consentConfig.policyVersion || DEFAULT_POLICY_VERSION;

export const EMPTY_PREFERENCES = Object.freeze({
  analytics: false,
  marketing: false,
});

function getConsentValues(preferences) {
  return {
    analytics_storage: preferences.analytics ? 'granted' : 'denied',
    ad_storage: preferences.marketing ? 'granted' : 'denied',
    ad_user_data: preferences.marketing ? 'granted' : 'denied',
    ad_personalization: preferences.marketing ? 'granted' : 'denied',
  };
}

function normalisePreferences(value) {
  if (!value || value.version !== COOKIE_POLICY_VERSION || !value.updatedAt) {
    return null;
  }

  return {
    version: COOKIE_POLICY_VERSION,
    updatedAt: value.updatedAt,
    necessary: true,
    analytics: Boolean(value.analytics),
    marketing: Boolean(value.marketing),
  };
}

export function readStoredConsent() {
  if (typeof document === 'undefined') return null;

  const cookie = document.cookie
    .split('; ')
    .find((entry) => entry.startsWith(`${CONSENT_COOKIE_NAME}=`));

  if (!cookie) return null;

  try {
    const value = JSON.parse(decodeURIComponent(cookie.slice(CONSENT_COOKIE_NAME.length + 1)));
    return normalisePreferences(value);
  } catch {
    return null;
  }
}

export function saveConsent(preferences) {
  const value = {
    version: COOKIE_POLICY_VERSION,
    updatedAt: new Date().toISOString(),
    necessary: true,
    analytics: Boolean(preferences.analytics),
    marketing: Boolean(preferences.marketing),
  };

  if (typeof document !== 'undefined') {
    const secure = window.location.protocol === 'https:' ? '; Secure' : '';
    document.cookie = [
      `${CONSENT_COOKIE_NAME}=${encodeURIComponent(JSON.stringify(value))}`,
      `Max-Age=${CONSENT_COOKIE_MAX_AGE}`,
      'Path=/',
      'SameSite=Lax',
      secure.slice(2),
    ].filter(Boolean).join('; ');
  }

  return value;
}

export function applyConsent(preferences, { emitEvent = true } = {}) {
  if (typeof window === 'undefined') return;

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function gtag() {
    window.dataLayer.push(arguments);
  };

  window.gtag('consent', 'update', getConsentValues(preferences));

  if (emitEvent) {
    window.dataLayer.push({ event: 'consent_update' });
  }
}

export function getPreferences(value = readStoredConsent()) {
  if (!value) return { ...EMPTY_PREFERENCES };

  return {
    analytics: Boolean(value.analytics),
    marketing: Boolean(value.marketing),
  };
}
