const FIELD_LABEL_KEYS = {
  current_password: 'profile.currentPassword',
  email: 'auth.email',
  new_password: 'profile.newPassword',
  password: 'auth.password',
  signup_token: 'auth.signupToken',
  username: 'auth.username',
};

export function translateApiError(error, t) {
  if (!error) {
    return t('common.somethingWrong');
  }

  if (error.status === 429) {
    return t('errors.throttled', {
      seconds: String(error.secondsRemaining ?? 0),
    });
  }

  const code = error.code || error.payload?.error;
  if (code) {
    const translated = t(`errors.${code}`);
    if (translated !== `errors.${code}`) {
      return translated;
    }
  }

  const payload = error.payload;
  if (payload && typeof payload === 'object') {
    const firstField = Object.keys(payload).find((key) => Array.isArray(payload[key]));
    if (firstField) {
      const labelKey = FIELD_LABEL_KEYS[firstField];
      const fieldLabel = labelKey ? t(labelKey) : firstField;
      return t('errors.fieldInvalid', { field: fieldLabel });
    }
  }

  return t('common.somethingWrong');
}
