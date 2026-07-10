import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { loginUser, requestPasswordReset } from '../api/users';
import LanguageSwitcher from '../components/LanguageSwitcher';
import { useI18n } from '../i18n/I18nContext';
import { translateApiError } from '../utils/apiErrors';
import { getCurrentUser, getPendingSignupToken, setCurrentUser } from '../utils/session';
import logoUrl from '../assets/logoFinancU.svg';

export default function Login() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [retryAfter, setRetryAfter] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isResetOpen, setIsResetOpen] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  const [resetError, setResetError] = useState('');
  const [resetResult, setResetResult] = useState(null);
  const [isResetSubmitting, setIsResetSubmitting] = useState(false);
  const pendingSignupToken = getPendingSignupToken();
  const signupPath = pendingSignupToken
    ? `/signup?token=${encodeURIComponent(pendingSignupToken)}`
    : '/signup';

  useEffect(() => {
    const currentUser = getCurrentUser();
    if (currentUser?.onboarding_completed) {
      navigate('/dashboard', { replace: true });
    }
  }, [navigate]);

  useEffect(() => {
    if (retryAfter <= 0) return undefined;

    setError(t('errors.throttled', { seconds: String(retryAfter) }));
    const timeoutId = window.setTimeout(() => {
      setRetryAfter((current) => Math.max(current - 1, 0));
    }, 1000);

    return () => window.clearTimeout(timeoutId);
  }, [retryAfter]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (retryAfter > 0) return;

    setIsSubmitting(true);

    try {
      const user = await loginUser({ identifier: identifier.trim(), password });
      setCurrentUser(user);
      setError('');
      setRetryAfter(0);
      navigate(user.onboarding_completed ? '/dashboard' : '/onboarding/step1');
    } catch (requestError) {
      if (requestError.status === 429 && requestError.secondsRemaining) {
        setRetryAfter(requestError.secondsRemaining);
      }
      setError(translateApiError(requestError, t));
    } finally {
      setIsSubmitting(false);
    }
  };

  const openPasswordReset = () => {
    setResetEmail(identifier.includes('@') ? identifier : '');
    setResetError('');
    setResetResult(null);
    setIsResetOpen(true);
  };

  const closePasswordReset = () => {
    setIsResetOpen(false);
    setResetError('');
    setResetResult(null);
    setIsResetSubmitting(false);
  };

  const handlePasswordReset = async (event) => {
    event.preventDefault();
    setResetError('');
    setResetResult(null);
    setIsResetSubmitting(true);

    try {
      const result = await requestPasswordReset({ email: resetEmail.trim() });
      setResetResult(result);
    } catch (requestError) {
      setResetError(translateApiError(requestError, t));
    } finally {
      setIsResetSubmitting(false);
    }
  };

  return (
    <div className="min-h-[100dvh] bg-background text-on-surface flex flex-col overflow-x-hidden">
      <header className="sticky top-0 z-50 flex h-16 w-full items-center justify-between border-b border-white/10 bg-surface/80 px-container-padding shadow-sm backdrop-blur-xl">
        <div className="flex items-center gap-base text-primary">
          <img alt="FinancU Logo" className="h-8 w-auto object-contain" src={logoUrl} />
        </div>
        <div className="flex items-center">
          <LanguageSwitcher compact />
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col items-center justify-center px-container-padding py-stack-lg sm:py-10">
        <section className="w-full max-w-sm text-center">
          <h1 className="mb-base font-headline-xl text-headline-xl tracking-tight text-on-surface">
            {t('auth.welcome')}
          </h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant">
            {t('auth.welcomeSubtitle')}
          </p>
        </section>

        <form className="mt-10 w-full max-w-sm space-y-stack-md" onSubmit={handleSubmit}>
          <label className="block">
            <span className="sr-only">{t('auth.usernameOrEmail')}</span>
            <span className="group relative flex items-center rounded-xl border border-white/10 bg-surface-container-lowest transition-all duration-200 focus-within:border-secondary focus-within:shadow-[0_0_8px_rgba(255,186,60,0.2)]">
              <span className="material-symbols-outlined absolute left-4 text-on-surface-variant">person</span>
              <input
                className="w-full border-none bg-transparent py-4 pl-12 pr-4 font-body-md text-on-surface placeholder:text-outline focus:ring-0"
                placeholder={t('auth.usernameOrEmail')}
                type="text"
                autoComplete="username"
                value={identifier}
                onChange={(event) => {
                  setIdentifier(event.target.value);
                  if (error) {
                    setError('');
                    setRetryAfter(0);
                  }
                }}
              />
            </span>
          </label>

          <div className="space-y-base">
            <label className="block">
              <span className="sr-only">{t('auth.password')}</span>
              <span className="group relative flex items-center rounded-xl border border-white/10 bg-surface-container-lowest transition-all duration-200 focus-within:border-secondary focus-within:shadow-[0_0_8px_rgba(255,186,60,0.2)]">
                <span className="material-symbols-outlined absolute left-4 text-on-surface-variant">lock</span>
                <input
                  className="w-full border-none bg-transparent py-4 pl-12 pr-12 font-body-md text-on-surface placeholder:text-outline focus:ring-0"
                  placeholder={t('auth.password')}
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => {
                    setPassword(event.target.value);
                    if (error) {
                      setError('');
                      setRetryAfter(0);
                    }
                  }}
                />
                <button
                  className="absolute right-4 text-on-surface-variant transition-colors hover:text-on-surface"
                  type="button"
                  onClick={() => setShowPassword((current) => !current)}
                  aria-label={showPassword ? t('auth.hidePassword') : t('auth.showPassword')}
                >
                  <span className="material-symbols-outlined">
                    {showPassword ? 'visibility_off' : 'visibility'}
                  </span>
                </button>
              </span>
            </label>

            <div className="flex justify-end">
              <button
                className="font-label-md text-label-md text-secondary transition-all hover:underline"
                type="button"
                onClick={openPasswordReset}
              >
                {t('auth.forgotPassword')}
              </button>
            </div>
          </div>

          {error && (
            <div className="rounded-xl border border-error/40 bg-error-container/30 px-4 py-3 font-label-md text-label-md text-on-error-container" role="alert" aria-live="polite">
              {error}
            </div>
          )}

          <button
            className="w-full rounded-xl bg-[#f2ae2e] py-4 font-bold text-on-primary-container shadow-lg shadow-primary/10 transition-all duration-200 hover:opacity-90 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
            type="submit"
            disabled={isSubmitting || retryAfter > 0}
          >
            {isSubmitting ? t('auth.signingIn') : t('auth.login')}
          </button>
        </form>
      </main>

      <footer className="w-full px-container-padding py-stack-lg text-center">
        <p className="font-body-md text-body-md text-on-surface-variant">
          {t('auth.noAccount')}{' '}
          <Link className="font-bold text-secondary hover:underline" to={signupPath}>
            {t('auth.signUp')}
          </Link>
        </p>
      </footer>

      {isResetOpen && (
        <div
          className="fixed inset-0 z-[70] flex items-center justify-center bg-black/60 px-container-padding backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-labelledby="password-reset-title"
        >
          <div className="w-full max-w-md rounded-xl border border-white/10 bg-surface p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 id="password-reset-title" className="font-headline-lg text-headline-lg text-on-surface">
                  {t('auth.resetPasswordTitle')}
                </h2>
                <p className="mt-2 font-body-md text-body-md text-on-surface-variant">
                  {t('auth.resetPasswordDescription')}
                </p>
              </div>
              <button
                className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container-high hover:text-on-surface"
                type="button"
                onClick={closePasswordReset}
                aria-label={t('common.close')}
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <form className="mt-6 space-y-stack-md" onSubmit={handlePasswordReset}>
              <label className="block">
                <span className="sr-only">{t('auth.email')}</span>
                <span className="group relative flex items-center rounded-xl border border-white/10 bg-surface-container-lowest transition-all duration-200 focus-within:border-secondary focus-within:shadow-[0_0_8px_rgba(255,186,60,0.2)]">
                  <span className="material-symbols-outlined absolute left-4 text-on-surface-variant">mail</span>
                  <input
                    className="w-full border-none bg-transparent py-4 pl-12 pr-4 font-body-md text-on-surface placeholder:text-outline focus:ring-0"
                    placeholder={t('auth.email')}
                    type="email"
                    autoComplete="email"
                    required
                    value={resetEmail}
                    onChange={(event) => {
                      setResetEmail(event.target.value);
                      if (resetError) setResetError('');
                      if (resetResult) setResetResult(null);
                    }}
                  />
                </span>
              </label>

              {resetError && (
                <div className="rounded-xl border border-error/40 bg-error-container/30 px-4 py-3 font-label-md text-label-md text-on-error-container" role="alert">
                  {resetError}
                </div>
              )}

              {resetResult && (
                <div className="rounded-xl border border-secondary/30 bg-secondary/10 px-4 py-3 font-body-sm text-body-sm text-on-surface" role="status">
                  <p>
                    {resetResult.temporary_password
                      ? t('auth.resetPasswordSuccessDev')
                      : t('auth.resetPasswordSuccess')}
                  </p>
                  {resetResult.temporary_password && (
                    <p className="mt-3 break-all rounded-lg bg-surface-container px-3 py-2 font-mono text-sm text-secondary">
                      {resetResult.temporary_password}
                    </p>
                  )}
                </div>
              )}

              <button
                className="w-full rounded-xl bg-[#f2ae2e] py-4 font-bold text-on-primary-container shadow-lg shadow-primary/10 transition-all duration-200 hover:opacity-90 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
                type="submit"
                disabled={isResetSubmitting}
              >
                {isResetSubmitting ? t('auth.sendingReset') : t('auth.sendReset')}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
