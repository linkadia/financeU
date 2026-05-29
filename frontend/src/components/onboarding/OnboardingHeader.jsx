import React from 'react';
import { useNavigate } from 'react-router-dom';
import LanguageSwitcher from '../LanguageSwitcher';
import { useI18n } from '../../i18n/I18nContext';

const LOGO_URL =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuBEVed2cAWQhnZmCYEo8c7WnwYIxlNA8zO2VYCdovKuhg8KE8xlG8sQc2GXEJnMN9ixwYTJD6kYNpQY5zWsG8phfAnIPEbAVRwXXhi7uF2IfyHaMDGbrS9cbxmQ1uKXP6_JVfyznFvUHS4BGbnL8Lj_2hsO94H0FvU3lASYXdyoEWPjreBt9DIb-X8ccHLAdA3bkAYarOgY9tIlEr69X5ypl3nQV1XMAKsFN-5xraYqqsprwwB8RJ_DjBwylcNmUSw_KIjXOL-fLu0L';

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

      {/* TopAppBar */}
      <header className="sticky top-0 z-50 bg-surface/80 backdrop-blur-xl border-b border-white/10 flex justify-between items-center w-full px-container-padding h-16 mt-1">
        <div className="flex items-center gap-stack-md">
          <button
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-surface-container-high rounded-full transition-colors active:scale-95 duration-100"
            aria-label={t('common.back')}
          >
            <span className="material-symbols-outlined text-on-surface">arrow_back</span>
          </button>
          <img
            src={LOGO_URL}
            alt="FinanU Logo"
            className="h-6 md:h-8 object-contain"
          />
        </div>
        <div className="flex items-center gap-2">
          <LanguageSwitcher compact />
          <span className="font-label-md text-on-surface-variant bg-surface-container px-3 py-1 rounded-full">
            {t('onboarding.stepOf', { current: currentStep, total: totalSteps })}
          </span>
        </div>
      </header>
    </>
  );
}
