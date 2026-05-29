import React from 'react';

/**
 * Continue button at the bottom of each onboarding step.
 */
export default function OnboardingContinueButton({ disabled, onClick, label = 'Continue' }) {
  return (
    <div className="sticky bottom-0 bg-transparent pb-8 pt-4 flex flex-col gap-stack-md">
      <button
        disabled={disabled}
        onClick={onClick}
        className={`
          w-full py-4 bg-secondary text-on-secondary font-title-md rounded-xl shadow-lg
          transition-all active:scale-[0.98] flex items-center justify-center gap-2
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:brightness-110'}
        `}
      >
        {label}
        <span className="material-symbols-outlined">arrow_forward</span>
      </button>
      <p className="font-label-sm text-center text-on-surface-variant">
        Don't worry, you can change these later in settings.
      </p>
    </div>
  );
}
