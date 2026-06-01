const CURRENT_USER_KEY = 'finanu.currentUser';

export function getCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem(CURRENT_USER_KEY));
  } catch {
    return null;
  }
}

export function setCurrentUser(user) {
  localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(user));
}

export function clearCurrentUser() {
  localStorage.removeItem(CURRENT_USER_KEY);
}
