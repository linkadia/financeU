import { defaultLanguage, translations } from '../i18n/translations';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api';

async function request(path, options) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = data.message ?? data.detail ?? Object.values(data).flat().join(' ');
    const error = new Error(detail || translations[defaultLanguage].common.somethingWrong);
    error.status = response.status;
    error.code = data.error;
    error.secondsRemaining = data.seconds_remaining;
    error.payload = data;
    throw error;
  }

  return data;
}

export function loginUser({ identifier, username, password }) {
  return request('/users/login/', {
    method: 'POST',
    body: JSON.stringify({ identifier: identifier ?? username, password }),
  });
}

export function createUserProfile({ username, email, password }) {
  return request('/users/profiles/', {
    method: 'POST',
    body: JSON.stringify({
      username,
      email,
      display_name: username,
      password,
    }),
  });
}

export function completeOnboarding(userId, onboarding) {
  return request(`/users/profiles/${userId}/complete-onboarding/`, {
    method: 'POST',
    body: JSON.stringify(onboarding),
  });
}

export function getUserSettings(userId) {
  return request(`/users/profiles/${userId}/settings/`);
}

export function updateUserSettings(userId, settings) {
  return request(`/users/profiles/${userId}/settings/`, {
    method: 'PATCH',
    body: JSON.stringify(settings),
  });
}
