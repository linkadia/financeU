const CURRENT_USER_KEY = 'financu.currentUser';
const LEGACY_CURRENT_USER_KEY = 'finanu.currentUser';
const PENDING_SIGNUP_TOKEN_KEY = 'financu.pendingSignupToken';

export function getCurrentUser() {
  try {
    const currentUser = localStorage.getItem(CURRENT_USER_KEY);
    if (currentUser) {
      return JSON.parse(currentUser);
    }

    const legacyUser = localStorage.getItem(LEGACY_CURRENT_USER_KEY);
    if (!legacyUser) {
      return null;
    }

    localStorage.setItem(CURRENT_USER_KEY, legacyUser);
    localStorage.removeItem(LEGACY_CURRENT_USER_KEY);
    return JSON.parse(legacyUser);
  } catch {
    return null;
  }
}

export function setCurrentUser(user) {
  localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(user));
  localStorage.removeItem(LEGACY_CURRENT_USER_KEY);
}

export function clearCurrentUser() {
  localStorage.removeItem(CURRENT_USER_KEY);
  localStorage.removeItem(LEGACY_CURRENT_USER_KEY);
}

export function getPendingSignupToken() {
  try {
    return sessionStorage.getItem(PENDING_SIGNUP_TOKEN_KEY) || '';
  } catch {
    return '';
  }
}

export function setPendingSignupToken(token) {
  try {
    if (token) {
      sessionStorage.setItem(PENDING_SIGNUP_TOKEN_KEY, token);
    }
  } catch {
    // Ignore storage failures so signup can still rely on the URL token.
  }
}

export function clearPendingSignupToken() {
  try {
    sessionStorage.removeItem(PENDING_SIGNUP_TOKEN_KEY);
  } catch {
    // Ignore storage failures.
  }
}
