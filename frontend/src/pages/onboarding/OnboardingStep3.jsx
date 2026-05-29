import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { completeOnboarding } from '../../api/users';
import OnboardingHeader from '../../components/onboarding/OnboardingHeader';
import FinnChatBubble from '../../components/onboarding/FinnChatBubble';
import OnboardingOptionCard from '../../components/onboarding/OnboardingOptionCard';
import OnboardingContinueButton from '../../components/onboarding/OnboardingContinueButton';
import { useOnboarding } from '../../context/OnboardingContext';
import { useI18n } from '../../i18n/I18nContext';
import { getCurrentUser, setCurrentUser } from '../../utils/session';

export default function OnboardingStep3() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const { answers, updateAnswer, clearOnboardingDraft } = useOnboarding();
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const goals = [
    {
      id: 'emergency',
      icon: 'emergency_home',
      label: t('onboarding.goalEmergency'),
      subLabel: t('onboarding.goalEmergencySub'),
      iconBgClass: 'bg-primary/10',
      iconTextClass: 'text-primary',
    },
    {
      id: 'investing',
      icon: 'trending_up',
      label: t('onboarding.goalInvesting'),
      subLabel: t('onboarding.goalInvestingSub'),
      iconBgClass: 'bg-secondary/10',
      iconTextClass: 'text-secondary',
    },
    {
      id: 'purchase',
      icon: 'shopping_cart',
      label: t('onboarding.goalPurchase'),
      subLabel: t('onboarding.goalPurchaseSub'),
      iconBgClass: 'bg-tertiary/10',
      iconTextClass: 'text-tertiary',
    },
    {
      id: 'retirement',
      icon: 'bedroom_parent',
      label: t('onboarding.goalRetirement'),
      subLabel: t('onboarding.goalRetirementSub'),
      iconBgClass: 'bg-primary-fixed/10',
      iconTextClass: 'text-primary-fixed',
    },
  ];

  const handleContinue = async () => {
    const currentUser = getCurrentUser();
    if (!currentUser?.id) {
      navigate('/');
      return;
    }

    setError('');
    setIsSubmitting(true);

    try {
      const updatedUser = await completeOnboarding(currentUser.id, {
        interests: answers.interests,
        risk_profile: answers.riskProfile,
        goal: answers.goal,
        selected_agent: answers.selectedAgent,
      });

      setCurrentUser(updatedUser);
      clearOnboardingDraft();
      navigate('/dashboard');
    } catch (requestError) {
      setError(requestError.message);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-[#090A0D] text-on-surface min-h-screen flex flex-col" style={{ backgroundImage: 'radial-gradient(at 0% 0%, rgba(99, 241, 134, 0.1) 0px, transparent 50%), radial-gradient(at 100% 100%, rgba(242, 174, 46, 0.05) 0px, transparent 50%)' }}>
      <OnboardingHeader currentStep={4} totalSteps={4} progressFraction="w-full" />

      <main data-scroll-root className="flex min-h-0 w-full max-w-lg flex-1 flex-col overflow-y-auto px-container-padding mx-auto">
        <div className="flex flex-grow flex-col gap-4">
          <FinnChatBubble
            message={t('onboarding.step3Message')}
            time="10:25 AM"
          />

          <div className="flex flex-col gap-3 pt-1">
            <h3 className="ml-1 text-[12px] font-semibold uppercase leading-4 tracking-wider text-on-surface-variant">
              {t('onboarding.selectGoal')}
            </h3>
            <div className="grid grid-cols-1 gap-2.5">
              {goals.map((item) => (
                <OnboardingOptionCard
                  key={item.id}
                  icon={item.icon}
                  label={item.label}
                  subLabel={item.subLabel}
                  iconBgClass={item.iconBgClass}
                  iconTextClass={item.iconTextClass}
                  selected={answers.goal === item.id}
                  onToggle={() => updateAnswer('goal', item.id)}
                />
              ))}
            </div>
          </div>
        </div>

        {error && (
          <div className="rounded-lg border border-error/40 bg-error-container/30 px-4 py-3 text-[14px] font-medium text-on-error-container" role="alert">
            {error}
          </div>
        )}

        <OnboardingContinueButton
          disabled={!answers.goal || !answers.selectedAgent || isSubmitting}
          onClick={handleContinue}
          label={isSubmitting ? t('onboarding.completing') : t('onboarding.completeProfile')}
        />
      </main>
    </div>
  );
}
