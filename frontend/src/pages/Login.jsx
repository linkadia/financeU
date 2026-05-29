import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { loginUser } from '../api/users';
import LanguageSwitcher from '../components/LanguageSwitcher';
import { useI18n } from '../i18n/I18nContext';
import { getCurrentUser, setCurrentUser } from '../utils/session';

const LOGO_URL =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuBEVed2cAWQhnZmCYEo8c7WnwYIxlNA8zO2VYCdovKuhg8KE8xlG8sQc2GXEJnMN9ixwYTJD6kYNpQY5zWsG8phfAnIPEbAVRwXXhi7uF2IfyHaMDGbrS9cbxmQ1uKXP6_JVfyznFvUHS4BGbnL8Lj_2hsO94H0FvU3lASYXdyoEWPjreBt9DIb-X8ccHLAdA3bkAYarOgY9tIlEr69X5ypl3nQV1XMAKsFN-5xraYqqsprwwB8RJ_DjBwylcNmUSw_KIjXOL-fLu0L';

function getThrottleMessage(seconds) {
  return `Has realizado demasiados intentos. Por seguridad, intentalo de nuevo en ${seconds} segundos.`;
}

export default function Login() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [error, setError] = useState('');
  const [retryAfter, setRetryAfter] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const currentUser = getCurrentUser();
    if (currentUser?.onboarding_completed) {
      navigate('/dashboard', { replace: true });
    }
  }, [navigate]);

  useEffect(() => {
    if (retryAfter <= 0) return undefined;

    setError(getThrottleMessage(retryAfter));
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
      setError(requestError.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-[100dvh] bg-background text-on-surface flex flex-col overflow-x-hidden">
      <header className="sticky top-0 z-50 flex h-16 w-full items-center justify-between border-b border-white/10 bg-surface/80 px-container-padding shadow-sm backdrop-blur-xl">
        <div className="flex items-center gap-base text-primary">
          <img alt="FinanU Logo" className="h-8 w-auto object-contain" src={LOGO_URL} />
        </div>
        <div className="relative flex items-center gap-3">
          <LanguageSwitcher compact />
          <button
            className="rounded-full p-base text-on-surface-variant transition-colors hover:bg-surface-container-high"
            type="button"
            aria-label={t('common.help')}
            aria-expanded={showHelp}
            onClick={() => setShowHelp((current) => !current)}
          >
            <span className="material-symbols-outlined">help_outline</span>
          </button>

          {showHelp && (
            <section className="absolute right-0 top-12 z-[80] w-[min(320px,calc(100vw-32px))] rounded-xl border border-white/10 bg-surface-container p-4 text-left shadow-2xl">
              <div className="mb-2 flex items-start justify-between gap-3">
                <h2 className="text-[18px] font-semibold leading-6 text-on-surface">{t('auth.aboutTitle')}</h2>
                <button
                  className="-mr-1 -mt-1 rounded-full p-1 text-on-surface-variant transition-colors hover:bg-surface-container-high hover:text-on-surface"
                  type="button"
                  aria-label={t('common.close')}
                  onClick={() => setShowHelp(false)}
                >
                  <span className="material-symbols-outlined text-[20px]">close</span>
                </button>
              </div>
              <p className="text-[14px] leading-5 text-on-surface-variant">
                {t('auth.aboutText')}
              </p>
            </section>
          )}
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
            <span className="group relative flex items-center rounded-xl border border-white/10 bg-surface-container-lowest transition-all duration-200 focus-within:border-secondary focus-within:shadow-[0_0_8px_rgba(81,225,120,0.2)]">
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
              <span className="group relative flex items-center rounded-xl border border-white/10 bg-surface-container-lowest transition-all duration-200 focus-within:border-secondary focus-within:shadow-[0_0_8px_rgba(81,225,120,0.2)]">
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
              <a className="font-label-md text-label-md text-secondary transition-all hover:underline" href="#">
                {t('auth.forgotPassword')}
              </a>
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
          <Link className="font-bold text-secondary hover:underline" to="/signup">
            {t('auth.signUp')}
          </Link>
        </p>
      </footer>
    </div>
  );
}
