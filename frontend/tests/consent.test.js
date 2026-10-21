import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { webcrypto } from 'node:crypto';
import { test } from 'node:test';
import vm from 'node:vm';

const runtimeSource = readFileSync(new URL('../src/analytics/consent.js', import.meta.url), 'utf8');
const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const bootstrap = html.match(/<script id="financu-consent-bootstrap">([\s\S]*?)<\/script>/)[1];
const denied = { analytics_storage: 'denied', ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied' };
const storedChoice = (overrides = {}) => ({ version: '1.2', consentId: '8919f8e1-3065-4111-9eee-0754b30c14ff', updatedAt: new Date().toISOString(), necessary: true, analytics: false, adsMeasurement: false, marketing: false, ...overrides });
const cookieFor = (value) => `financu_cookie_consent=${encodeURIComponent(JSON.stringify(value))}`;
const plain = (value) => JSON.parse(JSON.stringify(value));

function browser({ cookie = '', blocked = false, protocol = 'https:', crypto = webcrypto } = {}) {
  let cookieJar = cookie;
  let assignment;
  const document = {};
  Object.defineProperty(document, 'cookie', {
    get() { if (blocked) throw new Error('Storage blocked'); return cookieJar; },
    set(value) { if (blocked) throw new Error('Storage blocked'); assignment = value; cookieJar = value.split(';')[0]; },
  });
  const window = { location: { protocol }, crypto };
  const context = vm.createContext({ window, document });
  vm.runInContext(bootstrap, context);
  const api = vm.runInContext(`${runtimeSource.replace(/^export /gm, '')}\n;({ readStoredConsent, saveConsent, getPreferences, applyConsent, generateConsentId });`, context);
  return { window, api, assignment: () => assignment };
}

test('all optional permissions default to denied before tags load', () => {
  const { window, api } = browser();
  assert.deepEqual(plain(window.dataLayer[0]), { 0: 'consent', 1: 'default', 2: { ...denied, wait_for_update: 500 } });
  assert.equal(api.readStoredConsent(), null);
  assert.deepEqual(plain(api.getPreferences()), { analytics: false, adsMeasurement: false, marketing: false });
});

test('accepting grants analytics for 180 days and ignores any advertising preferences', () => {
  const { api, window, assignment } = browser();
  const saved = api.saveConsent({ analytics: true, adsMeasurement: true, marketing: true });
  api.applyConsent(saved);
  assert.equal(saved.necessary, true);
  assert.equal(saved.marketing, false);
  assert.equal(saved.adsMeasurement, false);
  assert.equal(saved.version, '1.2');
  assert.deepEqual(plain(api.readStoredConsent()), plain(saved));
  assert.match(assignment(), /Max-Age=15552000; Path=\/; SameSite=Lax; Secure$/);
  assert.deepEqual(plain(window.dataLayer[1][2]), { ...denied, analytics_storage: 'granted' });
  assert.deepEqual(plain(window.dataLayer[2]), { event: 'consent_update' });
});

test('rejecting and withdrawing a previous acceptance keep only necessary consent', () => {
  const { api, window } = browser({ cookie: cookieFor(storedChoice({ analytics: true })) });
  api.applyConsent(api.saveConsent({ analytics: false, adsMeasurement: false }));
  assert.equal(api.readStoredConsent().analytics, false);
  assert.equal(api.readStoredConsent().adsMeasurement, false);
  assert.deepEqual(plain(window.dataLayer[2][2]), denied);
  const reloaded = browser({ cookie: cookieFor(api.readStoredConsent()) });
  assert.deepEqual(plain(reloaded.window.dataLayer[1][2]), denied);
});

test('bootstrap and runtime restore analytics while keeping every advertising permission denied', () => {
  for (const analytics of [true, false]) {
    const { api, window } = browser({ cookie: `unrelated=1;${cookieFor(storedChoice({ analytics, marketing: true }))}` });
    const expected = { ...denied, analytics_storage: analytics ? 'granted' : 'denied' };
    assert.deepEqual(plain(api.getPreferences()), { analytics, adsMeasurement: false, marketing: false });
    assert.deepEqual(plain(window.dataLayer[1][2]), expected);
    api.applyConsent(api.saveConsent({ analytics, adsMeasurement: true, marketing: true }));
    assert.deepEqual(plain(window.dataLayer[2][2]), expected);
  }
});

test('invalid, corrupt and outdated consent never grants permissions in either reader', () => {
  const invalid = [null, {}, storedChoice({ version: 'old' }), storedChoice({ updatedAt: 'invalid' }),
    storedChoice({ updatedAt: 123 }), storedChoice({ analytics: 'false' }), storedChoice({ analytics: 1 }),
    storedChoice({ adsMeasurement: undefined }), storedChoice({ adsMeasurement: 'true' }),
    storedChoice({ adsMeasurement: 1 }), storedChoice({ adsMeasurement: null }),
    storedChoice({ adsMeasurement: true }), storedChoice({ version: '1.1', analytics: true, adsMeasurement: true }),
    storedChoice({ version: '1.0', analytics: true, adsMeasurement: undefined }),
    storedChoice({ consentId: undefined }), storedChoice({ consentId: 'not-a-uuid' }), storedChoice({ consentId: null })];
  const cookies = [...invalid.map(cookieFor), 'financu_cookie_consent=%E0%A4%A', 'financu_cookie_consent=%7B'];
  for (const cookie of cookies) {
    const { api, window } = browser({ cookie });
    assert.equal(api.readStoredConsent(), null, cookie);
    assert.equal(window.dataLayer.length, 1, cookie);
  }
});

test('choices and updates work when GTM is unavailable', () => {
  const { api, window } = browser();
  delete window.gtag;
  delete window.dataLayer;
  api.applyConsent(api.saveConsent({ analytics: true, adsMeasurement: true }));
  assert.equal(api.readStoredConsent().analytics, true);
  assert.deepEqual(plain(window.dataLayer[0][2]), { ...denied, analytics_storage: 'granted' });
});

test('blocked browser storage does not break initialization or a choice for the current visit', () => {
  const { api, window } = browser({ blocked: true });
  assert.equal(api.readStoredConsent(), null);
  assert.doesNotThrow(() => api.applyConsent(api.saveConsent({ analytics: false })));
  assert.deepEqual(plain(window.dataLayer[1][2]), denied);
});

test('local HTTP persistence omits Secure and silent consent updates omit the custom event', () => {
  const { api, assignment, window } = browser({ protocol: 'http:' });
  api.applyConsent(api.saveConsent({ analytics: true }), { emitEvent: false });
  assert.doesNotMatch(assignment(), /Secure/);
  assert.equal(window.dataLayer.length, 2);
});

test('legacy choices ask again and do not restore a grant before a fresh decision', () => {
  const previous = storedChoice({ analytics: true, consentId: undefined });
  const { api, window } = browser({ cookie: cookieFor(previous) });
  assert.equal(api.readStoredConsent(), null);
  assert.equal(window.dataLayer.length, 1);
  const saved = api.saveConsent({ analytics: false });
  assert.match(saved.consentId, /^[0-9a-f-]{36}$/i);
  assert.equal(api.readStoredConsent().analytics, false);
});

test('the browser identifier stays stable across decisions and policy versions', () => {
  const { api, window } = browser({ cookie: cookieFor(storedChoice({ version: '1.0', analytics: true, adsMeasurement: undefined })) });
  assert.equal(api.readStoredConsent(), null);
  assert.equal(window.dataLayer.length, 1);
  const accepted = api.saveConsent({ analytics: true, adsMeasurement: true });
  const rejected = api.saveConsent({ analytics: false });
  assert.equal(accepted.consentId, storedChoice().consentId);
  assert.equal(rejected.consentId, accepted.consentId);
  assert.equal(accepted.version, '1.2');
  assert.equal(rejected.adsMeasurement, false);
});

test('old advertising grants are not restored and a fresh analytics choice preserves the browser identifier', () => {
  const { api, window } = browser({ cookie: cookieFor(storedChoice({ version: '1.1', analytics: true, adsMeasurement: true })) });
  assert.equal(api.readStoredConsent(), null);
  assert.equal(window.dataLayer.length, 1);
  const saved = api.saveConsent({ analytics: true, adsMeasurement: false });
  api.applyConsent(saved);
  assert.equal(saved.consentId, storedChoice().consentId);
  assert.deepEqual(plain(window.dataLayer[1][2]), { ...denied, analytics_storage: 'granted' });
  const reloaded = browser({ cookie: cookieFor(saved) });
  assert.deepEqual(plain(reloaded.window.dataLayer[1][2]), { ...denied, analytics_storage: 'granted' });
});

test('an in-memory browser identifier is retained when cookie storage is blocked', () => {
  const { api } = browser({ blocked: true });
  const first = api.saveConsent({ analytics: true });
  const next = api.saveConsent({ analytics: false }, first);
  assert.equal(next.consentId, first.consentId);
});

test('UUID generation supports browsers without randomUUID', () => {
  const { api } = browser({ crypto: { getRandomValues: (bytes) => webcrypto.getRandomValues(bytes) } });
  const uuid = api.generateConsentId();
  assert.match(uuid, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
  assert.notEqual(api.generateConsentId(), uuid);
});
