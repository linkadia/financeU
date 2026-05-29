import React from 'react';

/**
 * A selectable option card used throughout the onboarding quiz.
 * 
 * @param {string}   icon        - Material Symbol icon name
 * @param {string}   label       - Primary option label
 * @param {string}   subLabel    - Secondary description
 * @param {string}   iconBgClass - Tailwind class for icon bg (e.g. 'bg-primary/10')
 * @param {string}   iconTextClass - Tailwind class for icon color (e.g. 'text-primary')
 * @param {boolean}  selected    - Whether this card is selected
 * @param {function} onToggle    - Callback when card is clicked
 * @param {boolean}  multiSelect - If true, toggling doesn't deselect others
 */
export default function OnboardingOptionCard({
  icon,
  label,
  subLabel,
  iconBgClass = 'bg-primary/10',
  iconTextClass = 'text-primary',
  selected,
  onToggle,
}) {
  return (
    <button
      onClick={onToggle}
      className={`
        group relative flex min-h-[74px] w-full items-center justify-between rounded-lg glass-panel px-3 py-3
        transition-all duration-200 text-left overflow-hidden
        hover:bg-surface-container
        ${selected ? 'pulse-border-onboarding bg-surface-container' : ''}
      `}
    >
      <div className="z-10 flex min-w-0 items-center gap-3">
        <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${iconBgClass} ${iconTextClass}`}>
          <span className="material-symbols-outlined text-[22px]">{icon}</span>
        </div>
        <div className="min-w-0">
          <p className={`text-[16px] font-semibold leading-5 text-on-surface transition-colors ${selected ? 'text-secondary' : 'group-hover:text-secondary'}`}>
            {label}
          </p>
          <p className="mt-0.5 text-[12px] font-medium leading-4 tracking-wide text-on-surface-variant">
            {subLabel}
          </p>
        </div>
      </div>
      <span className={`material-symbols-outlined z-10 shrink-0 pl-2 text-[22px] text-secondary transition-opacity ${selected ? 'opacity-100' : 'opacity-0'}`}>
        check_circle
      </span>
      <div className={`absolute inset-0 bg-secondary/5 transition-opacity ${selected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`} />
    </button>
  );
}
