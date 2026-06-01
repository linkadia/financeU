import React from 'react';
import { useI18n } from '../../i18n/I18nContext';

/**
 * Continue button at the bottom of each onboarding step.
 */
export default function OnboardingContinueButton({ disabled, onClick, label = 'Continue' }) {
  const { t } = useI18n();

  return (
    <div className="sticky bottom-0 -mx-container-padding mt-3 flex flex-col gap-2 bg-gradient-to-t from-background via-background/95 to-background/0 px-container-padding pb-5 pt-5">
      <button
        disabled={disabled}
        onClick={onClick}
        className={`
          flex w-full items-center justify-center gap-2 rounded-lg bg-secondary py-3.5 text-[16px] font-semibold text-on-secondary shadow-lg
          transition-all active:scale-[0.98] flex items-center justify-center gap-2
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:brightness-110'}
        `}
      >
        {label === 'Continue' ? t('common.continue') : label}
        <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
      </button>
      <p className="text-center text-[12px] font-medium leading-4 tracking-wide text-on-surface-variant">
        {t('onboarding.changeLater')}
      </p>
    </div>
  );
}
