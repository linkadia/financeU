import React from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingHeader from '../../components/onboarding/OnboardingHeader';
import FinnChatBubble from '../../components/onboarding/FinnChatBubble';
import OnboardingOptionCard from '../../components/onboarding/OnboardingOptionCard';
import OnboardingContinueButton from '../../components/onboarding/OnboardingContinueButton';
import { useOnboarding } from '../../context/OnboardingContext';
import { useI18n } from '../../i18n/I18nContext';

export default function OnboardingStep2() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const { answers, updateAnswer } = useOnboarding();
  const riskProfiles = [
    {
      id: 'low',
      icon: 'shield',
      label: t('onboarding.riskLow'),
      subLabel: t('onboarding.riskLowSub'),
      iconBgClass: 'bg-primary-container/20',
      iconTextClass: 'text-primary',
    },
    {
      id: 'medium',
      icon: 'balance',
      label: t('onboarding.riskMedium'),
      subLabel: t('onboarding.riskMediumSub'),
      iconBgClass: 'bg-primary-container/20',
      iconTextClass: 'text-primary',
    },
    {
      id: 'high',
      icon: 'trending_up',
      label: t('onboarding.riskHigh'),
      subLabel: t('onboarding.riskHighSub'),
      iconBgClass: 'bg-primary-container/20',
      iconTextClass: 'text-primary',
    },
  ];

  const handleContinue = () => {
    navigate('/onboarding/step4');
  };

  return (
    <div className="bg-[#090A0D] text-on-surface min-h-screen flex flex-col" style={{ backgroundImage: 'radial-gradient(at 0% 0%, rgba(255, 186, 60, 0.08) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(242, 174, 46, 0.05) 0px, transparent 50%)' }}>
      <OnboardingHeader currentStep={3} totalSteps={4} progressFraction="w-3/4" />

      <main data-scroll-root className="flex min-h-0 w-full max-w-lg flex-1 flex-col overflow-y-auto px-container-padding mx-auto">
        <div className="flex flex-grow flex-col gap-4">
          <FinnChatBubble
            message={t('onboarding.step2Message')}
            time="10:25 AM"
          />

          <div className="flex flex-col gap-3 pt-1">
            <h3 className="ml-1 text-[12px] font-semibold uppercase leading-4 tracking-wider text-on-surface-variant">
              {t('onboarding.selectProfile')}
            </h3>
            <div className="grid grid-cols-1 gap-2.5">
              {riskProfiles.map((item) => (
                <OnboardingOptionCard
                  key={item.id}
                  icon={item.icon}
                  label={item.label}
                  subLabel={item.subLabel}
                  iconBgClass={item.iconBgClass}
                  iconTextClass={item.iconTextClass}
                  selected={answers.riskProfile === item.id}
                  onToggle={() => updateAnswer('riskProfile', item.id)}
                />
              ))}
            </div>
          </div>
        </div>

        <OnboardingContinueButton
          disabled={!answers.riskProfile}
          onClick={handleContinue}
        />
      </main>
    </div>
  );
}
