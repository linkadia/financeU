import { apiRequest } from './client';

export async function recordCookieConsent(record) {
  const response = await apiRequest('/privacy/cookie-consents/', {
    method: 'POST',
    body: JSON.stringify(record),
    keepalive: true,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error('Unable to record cookie consent.');
    error.status = response.status;
    throw error;
  }
  return data;
}
