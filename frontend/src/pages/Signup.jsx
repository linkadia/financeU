import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { createUserProfile } from '../api/users';
import LanguageSwitcher from '../components/LanguageSwitcher';
import { useI18n } from '../i18n/I18nContext';
import { translateApiError } from '../utils/apiErrors';
import { setCurrentUser } from '../utils/session';
import logoUrl from '../assets/logoFinancU.svg';

const initialForm = {
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
};

export default function Signup() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const [form, setForm] = useState(initialForm);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
    if (error) setError('');
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (form.password.length < 8) {
      setError(t('auth.passwordLength'));
      return;
    }

    if (form.password !== form.confirmPassword) {
      setError(t('auth.passwordsMismatch'));
      return;
    }

    setIsSubmitting(true);

    try {
      const user = await createUserProfile(form);
      setCurrentUser(user);
      setError('');
      navigate('/onboarding/step1');
    } catch (requestError) {
      setError(translateApiError(requestError, t));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-[100dvh] bg-background text-on-surface flex flex-col overflow-x-hidden">
      <header className="sticky top-0 z-50 flex h-16 w-full items-center justify-between border-b border-white/10 bg-surface/80 px-container-padding shadow-sm backdrop-blur-xl">
        <Link className="flex items-center gap-base text-primary" to="/" aria-label={t('auth.backToLogin')}>
          <img alt="FinancU Logo" className="h-8 w-auto object-contain" src={logoUrl} />
        </Link>
        <div className="flex items-center">
          <LanguageSwitcher compact />
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-4xl items-center px-container-padding pt-stack-md">
        <Link
          className="inline-flex h-10 w-10 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container-high hover:text-on-surface active:scale-95"
          to="/"
          aria-label={t('common.back')}
        >
          <span className="material-symbols-outlined">arrow_back</span>
        </Link>
      </div>

      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col items-center px-container-padding py-stack-lg sm:justify-center sm:py-10">
        <section className="w-full max-w-md text-center">
          <h1 className="mb-base font-headline-xl text-headline-xl tracking-tight text-on-surface">
            {t('auth.signupTitle')}
          </h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant">
            {t('auth.signupSubtitle')}
          </p>
        </section>

        <form className="mt-8 w-full max-w-md space-y-stack-md" onSubmit={handleSubmit}>
          <label className="block">
            <span className="sr-only">{t('auth.username')}</span>
            <span className="group relative flex items-center rounded-xl border border-white/10 bg-surface-container-lowest transition-all duration-200 focus-within:border-secondary focus-within:shadow-[0_0_8px_rgba(255,186,60,0.2)]">
              <span className="material-symbols-outlined absolute left-4 text-on-surface-variant">person</span>
              <input
                className="w-full border-none bg-transparent py-4 pl-12 pr-4 font-body-md text-on-surface placeholder:text-outline focus:ring-0"
                placeholder={t('auth.username')}
                type="text"
                autoComplete="username"
                required
                value={form.username}
                onChange={(event) => updateField('username', event.target.value)}
              />
            </span>
          </label>

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
                value={form.email}
                onChange={(event) => updateField('email', event.target.value)}
              />
            </span>
          </label>

          <div className="grid gap-gutter sm:grid-cols-2">
            <label className="block">
              <span className="sr-only">{t('auth.password')}</span>
              <span className="group relative flex items-center rounded-xl border border-white/10 bg-surface-container-lowest transition-all duration-200 focus-within:border-secondary focus-within:shadow-[0_0_8px_rgba(255,186,60,0.2)]">
                <span className="material-symbols-outlined absolute left-4 text-on-surface-variant">lock</span>
                <input
                  className="w-full border-none bg-transparent py-4 pl-12 pr-12 font-body-md text-on-surface placeholder:text-outline focus:ring-0"
                  placeholder={t('auth.password')}
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={form.password}
                  onChange={(event) => updateField('password', event.target.value)}
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

            <label className="block">
              <span className="sr-only">{t('auth.confirmPassword')}</span>
              <span className="group relative flex items-center rounded-xl border border-white/10 bg-surface-container-lowest transition-all duration-200 focus-within:border-secondary focus-within:shadow-[0_0_8px_rgba(255,186,60,0.2)]">
                <span className="material-symbols-outlined absolute left-4 text-on-surface-variant">lock_reset</span>
                <input
                  className="w-full border-none bg-transparent py-4 pl-12 pr-12 font-body-md text-on-surface placeholder:text-outline focus:ring-0"
                  placeholder={t('auth.confirmPassword')}
                  type={showConfirmPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={form.confirmPassword}
                  onChange={(event) => updateField('confirmPassword', event.target.value)}
                />
                <button
                  className="absolute right-4 text-on-surface-variant transition-colors hover:text-on-surface"
                  type="button"
                  onClick={() => setShowConfirmPassword((current) => !current)}
                  aria-label={showConfirmPassword ? t('auth.hidePassword') : t('auth.showPassword')}
                >
                  <span className="material-symbols-outlined">
                    {showConfirmPassword ? 'visibility_off' : 'visibility'}
                  </span>
                </button>
              </span>
            </label>
          </div>

          {error && (
            <div className="rounded-xl border border-error/40 bg-error-container/30 px-4 py-3 font-label-md text-label-md text-on-error-container" role="alert">
              {error}
            </div>
          )}

          <button
            className="w-full rounded-xl bg-[#f2ae2e] py-4 font-bold text-on-primary-container shadow-lg shadow-primary/10 transition-all duration-200 hover:opacity-90 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? t('auth.creatingAccount') : t('auth.createAccount')}
          </button>
        </form>
      </main>

      <footer className="w-full px-container-padding py-stack-lg text-center">
        <p className="font-body-md text-body-md text-on-surface-variant">
          {t('auth.alreadyAccount')}{' '}
          <Link className="font-bold text-secondary hover:underline" to="/">
            {t('auth.signIn')}
          </Link>
        </p>
      </footer>
    </div>
  );
}
