import { apiRequest } from './client';

async function request(path) {
  const response = await apiRequest(path);

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = data.message ?? data.detail ?? Object.values(data).flat().join(' ');
    throw new Error(detail || 'Unable to load content.');
  }

  return data;
}

export function getNewsArticles({ newsTypes = [], dateRange = '24h' } = {}) {
  const params = new URLSearchParams();

  if (newsTypes.length > 0) {
    params.set('news_type', newsTypes.join(','));
  }

  if (dateRange) {
    params.set('date_range', dateRange);
  }

  const query = params.toString();
  return request(`/content/news/${query ? `?${query}` : ''}`);
}
