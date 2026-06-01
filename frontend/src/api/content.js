const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api';

async function request(path) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = data.message ?? data.detail ?? Object.values(data).flat().join(' ');
    throw new Error(detail || 'Unable to load content.');
  }

  return data;
}

export function getNewsArticles({ newsTypes = [] } = {}) {
  const params = new URLSearchParams();

  if (newsTypes.length > 0) {
    params.set('news_type', newsTypes.join(','));
  }

  const query = params.toString();
  return request(`/content/news/${query ? `?${query}` : ''}`);
}
