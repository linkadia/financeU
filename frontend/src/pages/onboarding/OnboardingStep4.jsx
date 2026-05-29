import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingHeader from '../../components/onboarding/OnboardingHeader';
import FinnChatBubble from '../../components/onboarding/FinnChatBubble';
import OnboardingOptionCard from '../../components/onboarding/OnboardingOptionCard';

const BUDGETS = [
  {
    id: 'under100',
    icon: 'savings',
    label: 'Under €100',
    subLabel: 'Starting small and steady',
    iconBgClass: 'bg-primary/10',
    iconTextClass: 'text-primary',
  },
  {
    id: '100to500',
    icon: 'wallet',
    label: '€100 - €500',
    subLabel: 'Consistent wealth building',
    iconBgClass: 'bg-secondary/10',
    iconTextClass: 'text-secondary',
  },
  {
    id: '500to2000',
    icon: 'account_balance',
    label: '€500 - €2,000',
    subLabel: 'Accelerated portfolio growth',
    iconBgClass: 'bg-tertiary/10',
    iconTextClass: 'text-tertiary',
  },
  {
    id: 'over2000',
    icon: 'trending_up',
    label: 'Over €2,000',
    subLabel: 'High-impact market strategy',
    iconBgClass: 'bg-primary-fixed/10',
    iconTextClass: 'text-primary-fixed',
  },
];

export default function OnboardingStep4() {
  const navigate = useNavigate();
  const [selected, setSelected] = useState(null);

  const handleComplete = () => {
    navigate('/onboarding/select-agent');
  };

  return (
    <div className="bg-background text-on-surface min-h-screen flex flex-col">
      <OnboardingHeader currentStep={4} progressFraction="w-full" />

      <main className="flex-1 flex flex-col w-full max-w-lg mx-auto px-container-padding overflow-y-auto">
        <div className="flex flex-col gap-stack-lg mt-stack-md flex-grow">
          <FinnChatBubble
            message="Great! One last thing: what's your monthly investment budget?"
            time="10:25 AM"
          />

          <section className="grid grid-cols-1 gap-base flex-grow">
            {BUDGETS.map((item) => (
              <OnboardingOptionCard
                key={item.id}
                icon={item.icon}
                label={item.label}
                subLabel={item.subLabel}
                iconBgClass={item.iconBgClass}
                iconTextClass={item.iconTextClass}
                selected={selected === item.id}
                onToggle={() => setSelected(item.id)}
              />
            ))}
          </section>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-transparent pb-8 pt-4 flex flex-col gap-stack-md mt-auto">
          <button
            onClick={handleComplete}
            disabled={!selected}
            className={`w-full py-4 bg-secondary text-on-secondary font-title-md rounded-xl shadow-lg transition-all active:scale-[0.98] flex items-center justify-center gap-2 ${
              !selected ? 'opacity-50 cursor-not-allowed' : 'hover:brightness-110'
            }`}
          >
            Complete Profile
            <span className="material-symbols-outlined">arrow_forward</span>
          </button>
          <p className="font-label-sm text-center text-on-surface-variant">
            This information helps us tailor your experience.
          </p>
        </div>
      </main>
    </div>
  );
}
