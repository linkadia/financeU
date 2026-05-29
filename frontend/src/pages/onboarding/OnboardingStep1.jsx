import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingHeader from '../../components/onboarding/OnboardingHeader';
import FinnChatBubble from '../../components/onboarding/FinnChatBubble';
import OnboardingOptionCard from '../../components/onboarding/OnboardingOptionCard';
import OnboardingContinueButton from '../../components/onboarding/OnboardingContinueButton';

const INTERESTS = [
  {
    id: 'crypto',
    icon: 'currency_bitcoin',
    label: 'Crypto',
    subLabel: 'Bitcoin, Ethereum & Web3',
    iconBgClass: 'bg-primary-container/20',
    iconTextClass: 'text-primary',
  },
  {
    id: 'stocks',
    icon: 'show_chart',
    label: 'Stock Market',
    subLabel: 'Global equities & ETF strategies',
    iconBgClass: 'bg-primary-container/20',
    iconTextClass: 'text-primary',
  },
  {
    id: 'forex',
    icon: 'payments',
    label: 'Forex',
    subLabel: 'Major & minor currency pairs',
    iconBgClass: 'bg-primary-container/20',
    iconTextClass: 'text-primary',
  },
  {
    id: 'savings',
    icon: 'savings',
    label: 'Personal Saving',
    subLabel: 'Budgeting & high-yield accounts',
    iconBgClass: 'bg-primary-container/20',
    iconTextClass: 'text-primary',
  },
];

export default function OnboardingStep1() {
  const navigate = useNavigate();
  const [selected, setSelected] = useState(new Set());

  const toggle = (id) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const handleContinue = () => {
    navigate('/onboarding/step2');
  };

  return (
    <div className="bg-[#090A0D] text-on-surface min-h-screen flex flex-col" style={{ backgroundImage: 'radial-gradient(at 0% 0%, rgba(99, 241, 134, 0.15) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(255, 186, 60, 0.1) 0px, transparent 50%)' }}>
      <OnboardingHeader currentStep={1} progressFraction="w-1/4" />

      <main className="flex-1 flex flex-col w-full max-w-lg mx-auto px-container-padding overflow-y-auto">
        <div className="flex flex-col gap-stack-lg mt-stack-md flex-grow">
          <FinnChatBubble
            message="Welcome to FinanU! I'm Finn, your personalized wealth navigator. To help me build your custom dashboard, what are your main financial interests?"
            time="10:24 AM"
          />

          <div className="flex flex-col gap-stack-md">
            <h3 className="font-label-md text-on-surface-variant uppercase tracking-wider ml-1">
              Select all that apply
            </h3>
            <div className="grid grid-cols-1 gap-gutter">
              {INTERESTS.map((item) => (
                <OnboardingOptionCard
                  key={item.id}
                  icon={item.icon}
                  label={item.label}
                  subLabel={item.subLabel}
                  iconBgClass={item.iconBgClass}
                  iconTextClass={item.iconTextClass}
                  selected={selected.has(item.id)}
                  onToggle={() => toggle(item.id)}
                />
              ))}
            </div>
          </div>
        </div>

        <OnboardingContinueButton
          disabled={selected.size === 0}
          onClick={handleContinue}
        />
      </main>
    </div>
  );
}
