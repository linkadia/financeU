import { recordCookieConsent } from '../api/privacy';
import { generateConsentId } from './consent';

const PENDING_RECORDS_KEY = 'financu.pendingConsentRecords';
const MAX_PENDING_RECORDS = 10;

function readPendingRecords() {
  try {
    const records = JSON.parse(localStorage.getItem(PENDING_RECORDS_KEY));
    return Array.isArray(records) ? records.filter((record) => record && typeof record.event_id === 'string') : [];
  } catch {
    return [];
  }
}

function writePendingRecords(records) {
  try {
    if (records.length) localStorage.setItem(PENDING_RECORDS_KEY, JSON.stringify(records.slice(-MAX_PENDING_RECORDS)));
    else localStorage.removeItem(PENDING_RECORDS_KEY);
    return true;
  } catch {
    return false;
  }
}

async function sendPendingRecords() {
  const settled = new Set();
  for (const record of readPendingRecords()) {
    try {
      await recordCookieConsent(record);
      settled.add(record.event_id);
    } catch (error) {
      // Invalid payloads and conflicts are final; temporary failures stay queued.
      if (error.status >= 400 && error.status < 500 && error.status !== 408 && error.status !== 429) {
        settled.add(record.event_id);
      }
    }
  }
  // Preserve decisions queued while an earlier request was in flight.
  writePendingRecords(readPendingRecords().filter((record) => !settled.has(record.event_id)));
}

let flushQueue = Promise.resolve();

export function flushConsentRecords() {
  flushQueue = flushQueue.then(sendPendingRecords).catch(() => {});
  return flushQueue;
}

export function recordConsent(stored, { action, language }) {
  const record = {
    event_id: generateConsentId(),
    consent_id: stored.consentId,
    action,
    analytics: stored.analytics,
    marketing: false,
    policy_version: stored.version,
    language,
    page_path: window.location.pathname,
    client_recorded_at: stored.updatedAt,
  };
  if (writePendingRecords([...readPendingRecords(), record])) return flushConsentRecords();
  return recordCookieConsent(record).catch(() => {});
}
