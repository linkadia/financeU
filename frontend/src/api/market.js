import { apiRequest } from './client';

async function request(path) {
  const response = await apiRequest(path);

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = data.message ?? data.detail ?? Object.values(data).flat().join(' ');
    throw new Error(detail || 'Unable to load market data.');
  }

  return data;
}

export function getLatestMarketSnapshots({ category, featured = true, lang = 'en' } = {}) {
  const params = new URLSearchParams();

  if (featured) {
    params.set('featured', 'true');
  }

  if (category) {
    params.set('category', category);
  }

  params.set('lang', lang === 'pl' ? 'pl' : 'en');

  return request(`/market/snapshots/latest/?${params.toString()}`);
}
