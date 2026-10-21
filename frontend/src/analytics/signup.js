// Each signup view can report one backend-confirmed registration, with no account data.
export function createSignupTracker() {
  let recorded = false;

  return function trackSignup(preferences) {
    if (recorded) return false;
    recorded = true;
    if (preferences?.analytics !== true || typeof window === 'undefined') return false;

    try {
      window.dataLayer = window.dataLayer || [];
      window.dataLayer.push({ event: 'financu_sign_up', method: 'email' });
      return true;
    } catch {
      // Analytics must never interrupt a successful registration or navigation.
      return false;
    }
  };
}
