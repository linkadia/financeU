const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8001/api';
const DEFAULT_FALLBACK_BASE_URLS = ['http://127.0.0.1:8000/api'];
const DEFAULT_TIMEOUT_MS = 5000;

function splitBaseUrls(value) {
  return (value ?? '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function uniqueUrls(urls) {
  return [...new Set(urls.map((url) => url.replace(/\/$/, '')))];
}

export function getApiBaseUrls() {
  return uniqueUrls([
    import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
    ...splitBaseUrls(import.meta.env.VITE_API_FALLBACK_BASE_URLS),
    ...DEFAULT_FALLBACK_BASE_URLS,
  ]);
}

function isSafeToRetry(options = {}) {
  const method = (options.method ?? 'GET').toUpperCase();
  return method === 'GET' || method === 'HEAD';
}

async function fetchWithTimeout(url, options, timeoutMs) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(url, {
      ...options,
      signal: controller.signal,
    });
  } finally {
    window.clearTimeout(timeoutId);
  }
}

export async function apiRequest(path, options = {}) {
  const baseUrls = isSafeToRetry(options) ? getApiBaseUrls() : getApiBaseUrls().slice(0, 1);
  let lastNetworkError = null;

  for (const baseUrl of baseUrls) {
    try {
      return await fetchWithTimeout(
        `${baseUrl}${path}`,
        {
          headers: {
            'Content-Type': 'application/json',
            ...options.headers,
          },
          ...options,
        },
        Number(import.meta.env.VITE_API_TIMEOUT_MS ?? DEFAULT_TIMEOUT_MS)
      );
    } catch (error) {
      lastNetworkError = error;
    }
  }

  throw lastNetworkError ?? new Error('Unable to connect to the API.');
}
