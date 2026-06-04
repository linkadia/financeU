import React from 'react';
import { useNavigate } from 'react-router-dom';
import LanguageSwitcher from '../LanguageSwitcher';
import { useI18n } from '../../i18n/I18nContext';
import logoUrl from '../../assets/logoFinancU.svg';

/**
 * Shared header for all onboarding steps.
 * @param {number} currentStep  - 1-based step number
 * @param {number} totalSteps   - total steps (default 4)
 * @param {string} progressFraction - Tailwind class for progress width, e.g. 'w-1/4'
 */
export default function OnboardingHeader({ currentStep, totalSteps = 4, progressFraction }) {
  const navigate = useNavigate();
  const { t } = useI18n();

  return (
    <>
      {/* Thin progress bar at the very top */}
      <div className="fixed top-0 left-0 w-full h-1 bg-surface-container-highest z-[60]">
        <div
          className={`h-full bg-secondary transition-all duration-700 ease-out ${progressFraction}`}
        />
      </div>

      <header className="sticky top-0 z-50 mt-1 flex h-16 w-full items-center justify-between border-b border-white/10 bg-surface/80 px-container-padding backdrop-blur-xl">
        <div className="flex items-center">
          <img
            src={logoUrl}
            alt="FinancU Logo"
            className="h-6 md:h-8 object-contain"
          />
        </div>
        <div className="flex items-center">
          <LanguageSwitcher compact />
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-lg items-center justify-between px-container-padding py-stack-md">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex h-10 w-10 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container-high hover:text-on-surface active:scale-95"
          aria-label={t('common.back')}
          type="button"
        >
          <span className="material-symbols-outlined">arrow_back</span>
        </button>
        <div className="flex items-center gap-2">
          <span className="font-label-md text-on-surface-variant bg-surface-container px-3 py-1 rounded-full">
            {t('onboarding.stepOf', { current: currentStep, total: totalSteps })}
          </span>
        </div>
      </div>
    </>
  );
}
