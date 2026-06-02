const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = data.message ?? data.detail ?? Object.values(data).flat().join(' ');
    throw new Error(detail || 'Unable to load learning catalog.');
  }

  return data;
}

export function getLearningCatalog(language) {
  const params = new URLSearchParams({ language });
  return request(`/learning/catalog/?${params.toString()}`);
}

export function getLearningProgress(userId) {
  const params = new URLSearchParams({ user_id: userId });
  return request(`/learning/progress/?${params.toString()}`);
}

export function submitLessonExam({ lessonId, userId, answers }) {
  return request(`/learning/lessons/${lessonId}/submit/`, {
    method: 'POST',
    body: JSON.stringify({
      user_id: userId,
      answers,
    }),
  });
}
