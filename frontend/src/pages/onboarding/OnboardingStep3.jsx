import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingHeader from '../../components/onboarding/OnboardingHeader';
import FinnChatBubble from '../../components/onboarding/FinnChatBubble';
import OnboardingOptionCard from '../../components/onboarding/OnboardingOptionCard';
import OnboardingContinueButton from '../../components/onboarding/OnboardingContinueButton';

const GOALS = [
  {
    id: 'emergency',
    icon: 'emergency_home',
    label: 'Building an Emergency Fund',
    subLabel: 'Safety net for unexpected life events',
    iconBgClass: 'bg-primary/10',
    iconTextClass: 'text-primary',
  },
  {
    id: 'investing',
    icon: 'trending_up',
    label: 'Investing in Crypto/Stocks',
    subLabel: 'Growing wealth through markets',
    iconBgClass: 'bg-secondary/10',
    iconTextClass: 'text-secondary',
  },
  {
    id: 'purchase',
    icon: 'shopping_cart',
    label: 'Saving for a Major Purchase',
    subLabel: 'Home, travel, or education',
    iconBgClass: 'bg-tertiary/10',
    iconTextClass: 'text-tertiary',
  },
  {
    id: 'retirement',
    icon: 'bedroom_parent',
    label: 'Retirement Planning',
    subLabel: 'Long-term financial security',
    iconBgClass: 'bg-primary-fixed/10',
    iconTextClass: 'text-primary-fixed',
  },
];

export default function OnboardingStep3() {
  const navigate = useNavigate();
  const [selected, setSelected] = useState(null);

  const handleContinue = () => {
    navigate('/onboarding/step4');
  };

  return (
    <div className="bg-[#090A0D] text-on-surface min-h-screen flex flex-col" style={{ backgroundImage: 'radial-gradient(at 0% 0%, rgba(99, 241, 134, 0.1) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(242, 174, 46, 0.05) 0px, transparent 50%)' }}>
      <OnboardingHeader currentStep={3} progressFraction="w-3/4" />

      <main className="flex-1 flex flex-col w-full max-w-lg mx-auto px-container-padding overflow-y-auto">
        <div className="flex flex-col gap-stack-lg mt-stack-md flex-grow">
          <FinnChatBubble
            message="Lastly, what's your primary financial goal for the next 12 months?"
            time="10:25 AM"
          />

          <div className="flex flex-col gap-stack-md">
            <h3 className="font-label-md text-on-surface-variant uppercase tracking-wider ml-1">
              SELECT YOUR GOAL
            </h3>
            <div className="grid grid-cols-1 gap-gutter">
              {GOALS.map((item) => (
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
