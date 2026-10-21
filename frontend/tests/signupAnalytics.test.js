import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';

const source = readFileSync(new URL('../src/analytics/signup.js', import.meta.url), 'utf8');
const signupSource = readFileSync(new URL('../src/pages/Signup.jsx', import.meta.url), 'utf8');
const submitBody = signupSource.match(/const handleSubmit = async \(event\) => \{([\s\S]*?)\n  \};/)[1];

function tracker(window = {}) {
  const context = vm.createContext({ window });
  const createSignupTracker = vm.runInContext(`${source.replace(/^export /gm, '')}\n;createSignupTracker;`, context);
  return { window, createSignupTracker };
}

test('a confirmed signup reports only a fixed event and method, without account or transaction data', () => {
  const { window, createSignupTracker } = tracker();
  const track = createSignupTracker();
  assert.equal(track({ analytics: true, email: 'private@example.test', user_id: 'private', token: 'secret', msisdn: '48123456789', transactionId: 'paid' }), true);
  assert.deepEqual(JSON.parse(JSON.stringify(window.dataLayer)), [{ event: 'financu_sign_up', method: 'email' }]);
});

test('rejected, missing and withdrawn consent never enqueue a signup event or replay it after acceptance', () => {
  for (const preferences of [null, {}, { analytics: false }, { analytics: 'true' }]) {
    const { window, createSignupTracker } = tracker();
    const track = createSignupTracker();
    assert.equal(track(preferences), false);
    assert.equal(track({ analytics: true }), false);
    assert.equal(window.dataLayer, undefined);
  }
});

test('repeated callbacks report one registration while separate signup views remain independent', () => {
  const { window, createSignupTracker } = tracker();
  const track = createSignupTracker();
  assert.equal(track({ analytics: true }), true);
  assert.equal(track({ analytics: true }), false);
  assert.equal(window.dataLayer.length, 1);
  assert.equal(createSignupTracker()({ analytics: true }), true);
  assert.equal(window.dataLayer.length, 2);
});

test('blocked analytics or GTM does not interrupt registration', () => {
  const { createSignupTracker } = tracker({ dataLayer: { push() { throw new Error('Blocked'); } } });
  assert.doesNotThrow(() => assert.equal(createSignupTracker()({ analytics: true }), false));
});

// Exercise the real submit handler with its API/session boundaries stubbed, including in-flight choices.
function signupForm({ create = async () => ({ id: 'local-test' }), analytics = true } = {}) {
  const window = {};
  const calls = [];
  const errors = [];
  const analyticsConsentRef = { current: analytics };
  const context = vm.createContext({
    window, analyticsConsentRef, submittingRef: { current: false },
    form: { username: 'test', email: 'private@example.test', password: 'local-only-password', confirmPassword: 'local-only-password' },
    tokenStatus: 'valid', signupToken: 'local-test-token',
    normalizeMobile: () => '', t: (key) => key,
    createUserProfile: async (payload) => { calls.push('request'); return create(payload); },
    setCurrentUser: () => calls.push('session'), clearPendingSignupToken: () => calls.push('clear-token'),
    setIsSubmitting: () => {}, setError: (error) => errors.push(error),
    setStoredSignupToken: () => {}, setTokenStatus: () => {},
    translateApiError: (error) => error.message, navigate: () => calls.push('navigate'),
  });
  vm.runInContext(`${source.replace(/^export /gm, '')}\nconst signupTrackerRef = { current: createSignupTracker() };`, context);
  const submit = vm.runInContext(`(async (event) => {${submitBody}\n})`, context);
  return { calls, errors, window, analyticsConsentRef, submit: () => submit({ preventDefault() {} }) };
}

test('signup waits for backend confirmation before recording and moving to onboarding', async () => {
  let confirm;
  const form = signupForm({ create: () => new Promise((resolve) => { confirm = resolve; }) });
  const request = form.submit();
  assert.deepEqual(form.calls, ['request']);
  assert.equal(form.window.dataLayer, undefined);
  confirm({ id: 'local-test' });
  await request;
  assert.deepEqual(form.calls, ['request', 'session', 'clear-token', 'navigate']);
  assert.equal(form.window.dataLayer[0].event, 'financu_sign_up');
});

test('a rejected subscription or failed registration does not create an analytics event or session', async () => {
  for (const code of ['subscription_not_eligible', 'invalid_signup_token', 'network_failure']) {
    const form = signupForm({ create: async () => { throw Object.assign(new Error(code), { code }); } });
    await form.submit();
    assert.deepEqual(form.calls, code === 'invalid_signup_token' ? ['request', 'clear-token'] : ['request']);
    assert.equal(form.window.dataLayer, undefined);
    assert.deepEqual(form.errors, [code]);
  }
});

test('a second submit during the pending request does not duplicate account creation or the event', async () => {
  let confirm;
  const form = signupForm({ create: () => new Promise((resolve) => { confirm = resolve; }) });
  const first = form.submit();
  await form.submit();
  assert.deepEqual(form.calls, ['request']);
  confirm({ id: 'local-test' });
  await first;
  assert.equal(form.window.dataLayer.length, 1);
  assert.equal(form.calls.filter((call) => call === 'navigate').length, 1);
});

test('consent revoked while registration is pending suppresses analytics but preserves successful registration', async () => {
  let confirm;
  const form = signupForm({ create: () => new Promise((resolve) => { confirm = resolve; }) });
  const request = form.submit();
  form.analyticsConsentRef.current = false;
  confirm({ id: 'local-test' });
  await request;
  assert.deepEqual(form.calls, ['request', 'session', 'clear-token', 'navigate']);
  assert.equal(form.window.dataLayer, undefined);
});
