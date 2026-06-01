import React from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingHeader from '../../components/onboarding/OnboardingHeader';
import FinnChatBubble from '../../components/onboarding/FinnChatBubble';
import OnboardingOptionCard from '../../components/onboarding/OnboardingOptionCard';
import OnboardingContinueButton from '../../components/onboarding/OnboardingContinueButton';
import { useOnboarding } from '../../context/OnboardingContext';
import { useI18n } from '../../i18n/I18nContext';

export default function OnboardingStep1() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const { answers, updateAnswer } = useOnboarding();
  const selected = new Set(answers.interests);
  const interests = [
    {
      id: 'crypto',
      icon: 'currency_bitcoin',
      label: t('dashboard.crypto'),
      subLabel: t('onboarding.interestCryptoSub'),
      iconBgClass: 'bg-primary-container/20',
      iconTextClass: 'text-primary',
    },
    {
      id: 'stocks',
      icon: 'show_chart',
      label: t('onboarding.interestStocks'),
      subLabel: t('onboarding.interestStocksSub'),
      iconBgClass: 'bg-primary-container/20',
      iconTextClass: 'text-primary',
    },
    {
      id: 'forex',
      icon: 'payments',
      label: t('dashboard.forex'),
      subLabel: t('onboarding.interestForexSub'),
      iconBgClass: 'bg-primary-container/20',
      iconTextClass: 'text-primary',
    },
    {
      id: 'savings',
      icon: 'school',
      label: t('onboarding.interestSavings'),
      subLabel: t('onboarding.interestSavingsSub'),
      iconBgClass: 'bg-primary-container/20',
      iconTextClass: 'text-primary',
    },
  ];

  const toggle = (id) => {
    updateAnswer('interests', (() => {
      const next = new Set(answers.interests);
      next.has(id) ? next.delete(id) : next.add(id);
      return Array.from(next);
    })());
  };

  const handleContinue = () => {
    navigate('/onboarding/step3');
  };

  return (
    <div className="bg-[#090A0D] text-on-surface min-h-screen flex flex-col" style={{ backgroundImage: 'radial-gradient(at 0% 0%, rgba(99, 241, 134, 0.15) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(255, 186, 60, 0.1) 0px, transparent 50%)' }}>
      <OnboardingHeader currentStep={2} totalSteps={4} progressFraction="w-2/4" />

      <main data-scroll-root className="flex min-h-0 w-full max-w-lg flex-1 flex-col overflow-y-auto px-container-padding mx-auto">
        <div className="flex flex-grow flex-col gap-4">
          <FinnChatBubble
            message={t('onboarding.step1Message')}
            time="10:24 AM"
          />

          <div className="flex flex-col gap-3 pt-1">
            <h3 className="ml-1 text-[12px] font-semibold uppercase leading-4 tracking-wider text-on-surface-variant">
              {t('onboarding.selectAll')}
            </h3>
            <div className="grid grid-cols-1 gap-2.5">
              {interests.map((item) => (
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
