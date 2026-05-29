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
        group relative flex items-center justify-between w-full p-stack-md glass-panel rounded-xl
        transition-all duration-200 text-left overflow-hidden
        hover:bg-surface-container
        ${selected ? 'pulse-border-onboarding bg-surface-container' : ''}
      `}
    >
      <div className="flex items-center gap-stack-md z-10">
        <div className={`w-10 h-10 flex items-center justify-center rounded-lg ${iconBgClass} ${iconTextClass}`}>
          <span className="material-symbols-outlined">{icon}</span>
        </div>
        <div>
          <p className={`font-title-md text-on-surface transition-colors ${selected ? 'text-secondary' : 'group-hover:text-secondary'}`}>
            {label}
          </p>
          <p className="font-label-sm text-on-surface-variant">{subLabel}</p>
        </div>
      </div>
      <span className={`material-symbols-outlined text-secondary transition-opacity z-10 ${selected ? 'opacity-100' : 'opacity-0'}`}>
        check_circle
      </span>
      <div className={`absolute inset-0 bg-secondary/5 transition-opacity ${selected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`} />
    </button>
  );
}
