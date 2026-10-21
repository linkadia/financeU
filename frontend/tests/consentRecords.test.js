import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';

const source = readFileSync(new URL('../src/analytics/consentRecords.js', import.meta.url), 'utf8');
const apiSource = readFileSync(new URL('../src/api/privacy.js', import.meta.url), 'utf8');
const key = 'financu.pendingConsentRecords';
const choice = { consentId: '8919f8e1-3065-4111-9eee-0754b30c14ff', analytics: true, marketing: false, version: '1.0', updatedAt: '2026-10-21T10:00:00.000Z' };
const options = { action: 'accept_all', language: 'pl' };
const plain = (value) => JSON.parse(JSON.stringify(value));
const fail = (status) => Object.assign(new Error('Request failed'), { status });

function recorder({ send = async () => ({}), storage = new Map(), blocked = false } = {}) {
  const calls = [];
  let sequence = 0;
  const context = vm.createContext({
    window: { location: { pathname: '/privacy', search: '?token=secret', hash: '#cookies' } },
    localStorage: {
      getItem(name) { if (blocked) throw new Error('Blocked'); return storage.get(name) ?? null; },
      setItem(name, value) { if (blocked) throw new Error('Blocked'); storage.set(name, value); },
      removeItem(name) { if (blocked) throw new Error('Blocked'); storage.delete(name); },
    },
    generateConsentId: () => `00000000-0000-4000-8000-${String(++sequence).padStart(12, '0')}`,
    recordCookieConsent: async (record) => { calls.push(plain(record)); return send(record); },
  });
  const api = vm.runInContext(`${source.replace(/^import .*;\n/gm, '').replace(/^export /gm, '')}\n;({ recordConsent, flushConsentRecords });`, context);
  return { api, calls, storage, pending: () => JSON.parse(storage.get(key) || '[]') };
}

test('a decision is queued before sending, includes its action, and contains only the page path', async () => {
  const { api, calls, pending } = recorder();
  const request = api.recordConsent(choice, options);
  assert.equal(pending().length, 1);
  await request;
  assert.deepEqual(calls[0], {
    event_id: '00000000-0000-4000-8000-000000000001', consent_id: choice.consentId,
    action: 'accept_all', analytics: true, marketing: false, policy_version: '1.0',
    language: 'pl', page_path: '/privacy', client_recorded_at: choice.updatedAt,
  });
  assert.deepEqual(pending(), []);
});

test('each action records the chosen categories with a distinct event identifier', async () => {
  const { api, calls } = recorder();
  await api.recordConsent(choice, options);
  await api.recordConsent({ ...choice, analytics: false }, { ...options, action: 'reject_all' });
  await api.recordConsent({ ...choice, analytics: false }, { ...options, action: 'custom' });
  assert.deepEqual(calls.map(({ action }) => action), ['accept_all', 'reject_all', 'custom']);
  assert.deepEqual(calls.map(({ analytics }) => analytics), [true, false, false]);
  assert.equal(new Set(calls.map(({ event_id }) => event_id)).size, 3);
  assert.equal(new Set(calls.map(({ consent_id }) => consent_id)).size, 1);
});

test('network failures survive a new visit and retain the original event and timestamp', async () => {
  const previous = recorder({ send: async () => { throw fail(); } });
  await previous.api.recordConsent(choice, options);
  assert.equal(previous.pending().length, 1);
  const nextVisit = recorder({ storage: previous.storage });
  await nextVisit.api.flushConsentRecords();
  assert.deepEqual(nextVisit.calls[0], previous.calls[0]);
  assert.deepEqual(nextVisit.pending(), []);
});

test('timeouts, throttling and server failures stay pending until a later retry', async () => {
  for (const status of [408, 429, 500, 503]) {
    let offline = true;
    const { api, calls, pending } = recorder({ send: async () => { if (offline) throw fail(status); } });
    await api.recordConsent(choice, options);
    assert.equal(pending().length, 1, String(status));
    offline = false;
    await api.flushConsentRecords();
    assert.deepEqual(calls[0], calls[1]);
    assert.deepEqual(pending(), []);
  }
});

test('invalid requests and conflicting identifiers are not retried indefinitely', async () => {
  for (const status of [400, 401, 403, 404, 409, 422]) {
    const { api, calls, pending } = recorder({ send: async () => { throw fail(status); } });
    await api.recordConsent(choice, options);
    await api.flushConsentRecords();
    assert.deepEqual(pending(), []);
    assert.equal(calls.length, 1, String(status));
  }
});

test('a new decision queued during an in-flight request is preserved and sent', async () => {
  let release;
  let started;
  let first = true;
  const blocked = new Promise((resolve) => { release = resolve; });
  const inFlight = new Promise((resolve) => { started = resolve; });
  const { api, calls, pending } = recorder({ send: async () => {
    if (first) { first = false; started(); await blocked; }
  } });
  const firstDecision = api.recordConsent(choice, options);
  await inFlight;
  const secondDecision = api.recordConsent({ ...choice, analytics: false }, { ...options, action: 'custom' });
  assert.equal(pending().length, 2);
  release();
  await Promise.all([firstDecision, secondDecision]);
  assert.equal(calls.length, 2);
  assert.notEqual(calls[0].event_id, calls[1].event_id);
  assert.deepEqual(pending(), []);
});

test('multiple flush triggers serialize delivery rather than sending the same pending event twice', async () => {
  let offline = true;
  const { api, calls } = recorder({ send: async () => { if (offline) throw fail(); } });
  await api.recordConsent(choice, options);
  offline = false;
  await Promise.all([api.flushConsentRecords(), api.flushConsentRecords(), api.flushConsentRecords()]);
  assert.equal(calls.length, 2);
});

test('the queue retains the ten most recent pending decisions', async () => {
  const { api, pending } = recorder({ send: async () => { throw fail(); } });
  for (let index = 0; index < 11; index++) await api.recordConsent(choice, options);
  assert.equal(pending().length, 10);
  assert.equal(pending()[0].event_id, '00000000-0000-4000-8000-000000000002');
});

test('blocked storage falls back to a direct request', async () => {
  const { api, calls } = recorder({ blocked: true });
  await api.recordConsent(choice, options);
  assert.equal(calls.length, 1);
});

test('corrupt queue data does not prevent a fresh decision', async () => {
  for (const value of ['{', '{}', '[null, 123, {}]']) {
    const { api, calls } = recorder({ storage: new Map([[key, value]]) });
    await api.recordConsent(choice, options);
    assert.equal(calls.length, 1);
  }
});

test('the API adapter accepts new records and idempotent responses and preserves error status', async () => {
  for (const status of [200, 201, 409, 429, 503]) {
    let request;
    const context = vm.createContext({ apiRequest: async (path, config) => {
      request = { path, config };
      return { ok: status < 400, status, json: async () => ({ event_id: 'test' }) };
    } });
    const send = vm.runInContext(`${apiSource.replace(/^import .*;\n/gm, '').replace(/^export /gm, '')}\n;recordCookieConsent;`, context);
    if (status < 400) await send({ action: 'custom' });
    else await assert.rejects(send({ action: 'custom' }), (error) => error.status === status);
    assert.equal(request.path, '/privacy/cookie-consents/');
    assert.equal(request.config.method, 'POST');
    assert.equal(request.config.keepalive, true);
  }
});
