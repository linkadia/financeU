import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingHeader from '../../components/onboarding/OnboardingHeader';
import { useOnboarding } from '../../context/OnboardingContext';
import { FINN_AVATAR, NOVA_AVATAR } from '../../data/agents';
import { useI18n } from '../../i18n/I18nContext';

export default function SelectAgent() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const { answers, updateAnswer } = useOnboarding();
  const [selectedAgent, setSelectedAgent] = useState(answers.selectedAgent || null);
  const agents = [
    {
      id: 'finn',
      avatar: FINN_AVATAR,
      name: 'Finn',
      tagline: t('onboarding.agentFinnTagline'),
      level: t('onboarding.noviceIntermediate'),
      description: t('onboarding.agentFinnDescription'),
      accentColor: 'primary',
      accentHex: '#ffcf83',
      gradientClass: 'from-primary/10 to-transparent',
      bgIcon: 'school',
    },
    {
      id: 'nova',
      avatar: NOVA_AVATAR,
      name: 'Nova',
      tagline: t('onboarding.agentNovaTagline'),
      level: t('onboarding.advanced'),
      description: t('onboarding.agentNovaDescription'),
      accentColor: 'secondary',
      accentHex: '#ffba3c',
      gradientClass: 'from-secondary/10 to-transparent',
      bgIcon: 'query_stats',
    },
  ];

  const handleSelect = (agent) => {
    setSelectedAgent(agent.id);
    updateAnswer('selectedAgent', agent.id);
    navigate('/onboarding/step2');
  };

  return (
    <div className="flex min-h-screen flex-col bg-background text-on-surface">
      <OnboardingHeader currentStep={1} totalSteps={4} progressFraction="w-1/4" />

      <main data-scroll-root className="mx-auto flex w-full max-w-2xl flex-1 flex-col overflow-y-auto px-container-padding py-stack-lg">
        <section className="mb-10 space-y-stack-sm text-center">
          <h1 className="font-headline-xl text-headline-xl tracking-tight text-on-surface">{t('onboarding.welcome')}</h1>
          <p className="mx-auto max-w-lg font-body-lg text-body-lg text-on-surface-variant">
            {t('onboarding.chooseAgent')}
          </p>
        </section>

        <div className="grid grid-cols-1 gap-stack-lg md:grid-cols-2">
          {agents.map((agent) => (
            <button
              key={agent.id}
              onClick={() => handleSelect(agent)}
              className={`
                glass-card group relative overflow-hidden rounded-xl bg-gradient-to-br p-stack-lg text-left transition-all duration-300 active:scale-95
                ${agent.gradientClass}
                ${selectedAgent === agent.id ? 'ring-2 ring-offset-2 ring-offset-background' : ''}
              `}
              style={selectedAgent === agent.id ? { ['--tw-ring-color']: agent.accentHex } : {}}
              type="button"
            >
              <div className="relative z-10">
                <div className="mb-stack-md flex items-start justify-between">
                  <div className="h-20 w-20 overflow-hidden rounded-full border-2 border-white/10 transition-colors group-hover:border-white/30">
                    <img src={agent.avatar} alt={`${agent.name} AI`} className="h-full w-full object-cover" />
                  </div>
                  <span className={`rounded-full border border-${agent.accentColor}/20 bg-${agent.accentColor}/10 px-3 py-1 font-label-sm text-label-sm text-${agent.accentColor}`}>
                    {agent.level}
                  </span>
                </div>
                <h2 className="mb-stack-sm font-headline-lg-mobile text-headline-lg-mobile text-on-surface">{agent.name}</h2>
                <h3 className={`mb-stack-md font-label-md text-label-md text-${agent.accentColor}`}>{agent.tagline}</h3>
                <p className="mb-stack-lg font-body-md text-body-md leading-relaxed text-on-surface-variant">{agent.description}</p>
                <div className={`flex items-center gap-base font-label-md text-label-md text-${agent.accentColor}`}>
                  <span>{t('onboarding.selectAgent', { name: agent.name })}</span>
                  <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                </div>
              </div>
              <div className="absolute -bottom-8 -right-8 opacity-5 transition-opacity group-hover:opacity-10">
                <span className="material-symbols-outlined text-[120px]">{agent.bgIcon}</span>
              </div>
            </button>
          ))}
        </div>
      </main>
    </div>
  );
}
