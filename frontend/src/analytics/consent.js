const DEFAULT_COOKIE_NAME = 'financu_cookie_consent';
const DEFAULT_POLICY_VERSION = '1.2';
const CONSENT_COOKIE_MAX_AGE = 60 * 60 * 24 * 180;
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

const consentConfig = typeof window !== 'undefined' && window.__FINANCU_CONSENT_CONFIG__
  ? window.__FINANCU_CONSENT_CONFIG__
  : {};

export const CONSENT_COOKIE_NAME = consentConfig.cookieName || DEFAULT_COOKIE_NAME;
export const COOKIE_POLICY_VERSION = consentConfig.policyVersion || DEFAULT_POLICY_VERSION;
export const CONSENT_ACTIONS = Object.freeze({ acceptAll: 'accept_all', rejectAll: 'reject_all', custom: 'custom' });

export function generateConsentId() {
  if (window.crypto.randomUUID) return window.crypto.randomUUID();
  const bytes = window.crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

function isConsentId(value) {
  return typeof value === 'string' && UUID_PATTERN.test(value);
}

export const EMPTY_PREFERENCES = Object.freeze({
  analytics: false,
  adsMeasurement: false,
  marketing: false,
});

function getConsentValues(preferences) {
  return {
    analytics_storage: preferences.analytics === true ? 'granted' : 'denied',
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
  };
}

function normalisePreferences(value) {
  if (!value || !isConsentId(value.consentId) || value.version !== COOKIE_POLICY_VERSION || typeof value.analytics !== 'boolean'
    || value.adsMeasurement !== false
    || typeof value.updatedAt !== 'string' || !Number.isFinite(Date.parse(value.updatedAt))) {
    return null;
  }

  return {
    version: COOKIE_POLICY_VERSION,
    updatedAt: value.updatedAt,
    consentId: value.consentId,
    necessary: true,
    analytics: value.analytics,
    adsMeasurement: false,
    marketing: false,
  };
}

function readConsentCookie() {
  if (typeof document === 'undefined') return null;

  try {
    const cookie = document.cookie.split(';').map((entry) => entry.trim())
      .find((entry) => entry.startsWith(`${CONSENT_COOKIE_NAME}=`));
    if (!cookie) return null;
    return JSON.parse(decodeURIComponent(cookie.slice(CONSENT_COOKIE_NAME.length + 1)));
  } catch {
    return null;
  }
}

export function readStoredConsent() {
  return normalisePreferences(readConsentCookie());
}

export function saveConsent(preferences, previousConsent = null) {
  const previousId = readConsentCookie()?.consentId || previousConsent?.consentId;
  const value = {
    version: COOKIE_POLICY_VERSION,
    updatedAt: new Date().toISOString(),
    consentId: isConsentId(previousId) ? previousId : generateConsentId(),
    necessary: true,
    analytics: preferences.analytics === true,
    adsMeasurement: false,
    marketing: false,
  };

  if (typeof document !== 'undefined') {
    const secure = window.location.protocol === 'https:' ? '; Secure' : '';
    try {
      document.cookie = [
        `${CONSENT_COOKIE_NAME}=${encodeURIComponent(JSON.stringify(value))}`,
        `Max-Age=${CONSENT_COOKIE_MAX_AGE}`,
        'Path=/',
        'SameSite=Lax',
        secure.slice(2),
      ].filter(Boolean).join('; ');
    } catch {
      // The controller still applies the choice for this visit if cookies are blocked.
    }
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
    analytics: value.analytics === true,
    adsMeasurement: false,
    marketing: false,
  };
}
