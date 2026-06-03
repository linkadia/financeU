import { apiRequest } from './client';

async function request(path, options = {}) {
  const response = await apiRequest(path, options);

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
