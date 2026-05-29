import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingHeader from '../../components/onboarding/OnboardingHeader';
import FinnChatBubble from '../../components/onboarding/FinnChatBubble';
import OnboardingOptionCard from '../../components/onboarding/OnboardingOptionCard';
import OnboardingContinueButton from '../../components/onboarding/OnboardingContinueButton';

const RISK_PROFILES = [
  {
    id: 'low',
    icon: 'shield',
    label: 'Low',
    subLabel: 'I prefer steady, low-risk growth',
    iconBgClass: 'bg-primary-container/20',
    iconTextClass: 'text-primary',
  },
  {
    id: 'medium',
    icon: 'balance',
    label: 'Medium',
    subLabel: "I'm okay with some fluctuations",
    iconBgClass: 'bg-primary-container/20',
    iconTextClass: 'text-primary',
  },
  {
    id: 'high',
    icon: 'trending_up',
    label: 'High',
    subLabel: 'Aggressive growth focus',
    iconBgClass: 'bg-primary-container/20',
    iconTextClass: 'text-primary',
  },
];

export default function OnboardingStep2() {
  const navigate = useNavigate();
  const [selected, setSelected] = useState(null);

  const handleContinue = () => {
    navigate('/onboarding/step3');
  };

  return (
    <div className="bg-[#090A0D] text-on-surface min-h-screen flex flex-col" style={{ backgroundImage: 'radial-gradient(at 0% 0%, rgba(99, 241, 134, 0.08) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(242, 174, 46, 0.05) 0px, transparent 50%)' }}>
      <OnboardingHeader currentStep={2} progressFraction="w-2/4" />

      <main className="flex-1 flex flex-col w-full max-w-lg mx-auto px-container-padding overflow-y-auto">
        <div className="flex flex-col gap-stack-lg mt-stack-md flex-grow">
          <FinnChatBubble
            message="Understanding your risk comfort helps me tailor my suggestions. How do you feel about market volatility?"
            time="10:25 AM"
          />

          <div className="flex flex-col gap-stack-md pt-4">
            <h3 className="font-label-md text-on-surface-variant uppercase tracking-wider ml-1">
              Select your profile
            </h3>
            <div className="grid grid-cols-1 gap-gutter">
              {RISK_PROFILES.map((item) => (
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
            </div>
          </div>
        </div>

        <OnboardingContinueButton
          disabled={!selected}
          onClick={handleContinue}
        />
      </main>
    </div>
  );
}
