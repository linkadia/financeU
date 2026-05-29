import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const LOGO_URL =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuBEVed2cAWQhnZmCYEo8c7WnwYIxlNA8zO2VYCdovKuhg8KE8xlG8sQc2GXEJnMN9ixwYTJD6kYNpQY5zWsG8phfAnIPEbAVRwXXhi7uF2IfyHaMDGbrS9cbxmQ1uKXP6_JVfyznFvUHS4BGbnL8Lj_2hsO94H0FvU3lASYXdyoEWPjreBt9DIb-X8ccHLAdA3bkAYarOgY9tIlEr69X5ypl3nQV1XMAKsFN-5xraYqqsprwwB8RJ_DjBwylcNmUSw_KIjXOL-fLu0L';

const FINN_AVATAR =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuA0gvVl-pk_RvaxYyQny8IQCgmnz71W9mT9ZmbtbCSL5iJyL1TNtB9qc4_23KD8td59zo10Hvs5UFoBiUb1Dbp8SMZUWiVx01nGitBFx3DuFgm_679OMbvwv1iUECKmnBGnW7FwTS4S2op8VaCRYjzsLRX9GybhQFFGyRIQ0wUhpTfDOMzOqDsyJQ3p5WtveAXeJM1idE3VjuRPCNIs0RWRpTKqZ1vrTkKgLdf6f_beVpmXWVRflTkqhmcGgbwAWzqGwZ0e59CqgIlb';

const NOVA_AVATAR =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuDVGSnNA6PQ4euhijViaZy9HWmWY3FGXMVikDef5PvQ10xD1YLOGkJxSPLPT3eyyMgQOSPqyRKCm_GXBOYQZsOMU9UyGjnnK753D_TKi9xxYHu3t4wsf3sMA4GtY76zmnq_gm_ceVfQVn0UJAEOY5XZVQ0BiUye83QZSiz5lUMLLJMC5HbIeuRAthqCNIshOQ7Ns_25MTx45N3ELVWQ7ptQcxsN7YWWLT-XoYkxgw7_HobQD9uK1I8Tuyjlg78_DiEwHvov6e9OUxDE';

const AGENTS = [
  {
    id: 'finn',
    avatar: FINN_AVATAR,
    name: 'Finn',
    tagline: 'The Mentor',
    level: 'Novice - Intermediate',
    description:
      '"I\'m here to help you master the basics. We\'ll focus on building a strong foundation, managing risk, and understanding the core mechanics of the market."',
    accentColor: 'primary',
    accentHex: '#63f186',
    gradientClass: 'from-primary/10 to-transparent',
    bgIcon: 'school',
  },
  {
    id: 'nova',
    avatar: NOVA_AVATAR,
    name: 'Nova',
    tagline: 'The Strategist',
    level: 'Advanced',
    description:
      '"I provide deep-dive technical analysis and macro indicators. We\'ll skip the basics and focus on execution, algorithmic signals, and complex portfolio strategies."',
    accentColor: 'secondary',
    accentHex: '#ffba3c',
    gradientClass: 'from-secondary/10 to-transparent',
    bgIcon: 'query_stats',
  },
];

export default function SelectAgent() {
  const navigate = useNavigate();
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [toast, setToast] = useState(null);

  const handleSelect = (agent) => {
    setSelectedAgent(agent.id);
    setToast({ message: `Setting up your experience with ${agent.name}...`, color: agent.accentHex });
    setTimeout(() => {
      setToast(null);
      navigate('/dashboard');
    }, 1800);
  };

  return (
    <div className="bg-background text-on-surface min-h-screen flex flex-col">
      {/* TopBar */}
      <header className="sticky top-0 z-50 bg-surface/80 backdrop-blur-xl border-b border-white/10 shadow-sm flex justify-between items-center w-full px-container-padding h-16">
        <div className="flex items-center gap-base">
          <img src={LOGO_URL} alt="FinanU Logo" className="h-8 w-auto object-contain" />
        </div>
        <button className="material-symbols-outlined hover:bg-surface-container-high transition-colors p-base rounded-full text-on-surface-variant">
          notifications
        </button>
      </header>

      <main className="flex-grow px-container-padding py-stack-lg max-w-2xl mx-auto w-full">
        {/* Welcome header */}
        <section className="text-center mb-10 space-y-stack-sm">
          <h1 className="font-headline-xl text-headline-xl text-on-surface tracking-tight">Welcome to FinanU</h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant max-w-lg mx-auto">
            Choose your AI companion to personalize your financial journey. Your guide will tailor insights to your expertise.
          </p>
        </section>

        {/* Agent cards – single column on mobile, 2-col on md+ */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-stack-lg">
          {AGENTS.map((agent) => (
            <button
              key={agent.id}
              onClick={() => handleSelect(agent)}
              className={`
                glass-card group text-left rounded-xl p-stack-lg transition-all duration-300 active:scale-95 relative overflow-hidden
                bg-gradient-to-br ${agent.gradientClass}
                ${selectedAgent === agent.id ? 'ring-2 ring-offset-2 ring-offset-background' : ''}
              `}
              style={selectedAgent === agent.id ? { ['--tw-ring-color']: agent.accentHex } : {}}
            >
              <div className="relative z-10">
                <div className="flex justify-between items-start mb-stack-md">
                  <div className="w-20 h-20 rounded-full overflow-hidden border-2 border-white/10 group-hover:border-white/30 transition-colors">
                    <img src={agent.avatar} alt={`${agent.name} AI`} className="w-full h-full object-cover" />
                  </div>
                  <span className={`bg-${agent.accentColor}/10 text-${agent.accentColor} px-3 py-1 rounded-full font-label-sm text-label-sm border border-${agent.accentColor}/20`}>
                    {agent.level}
                  </span>
                </div>
                <h2 className="font-headline-lg-mobile text-headline-lg-mobile text-on-surface mb-stack-sm">{agent.name}</h2>
                <h3 className={`font-label-md text-label-md text-${agent.accentColor} mb-stack-md`}>{agent.tagline}</h3>
                <p className="font-body-md text-body-md text-on-surface-variant mb-stack-lg leading-relaxed">{agent.description}</p>
                <div className={`flex items-center gap-base text-${agent.accentColor} font-label-md text-label-md`}>
                  <span>Select {agent.name}</span>
                  <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                </div>
              </div>
              {/* Background decoration */}
              <div className="absolute -bottom-8 -right-8 opacity-5 group-hover:opacity-10 transition-opacity">
                <span className="material-symbols-outlined text-[120px]">{agent.bgIcon}</span>
              </div>
            </button>
          ))}
        </div>
      </main>

      {/* Toast notification */}
      {toast && (
        <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 bg-surface-container-high text-on-surface px-6 py-3 rounded-full shadow-2xl flex items-center gap-base border border-white/10 animate-bounce" style={{ borderColor: toast.color }}>
          <span className="material-symbols-outlined" style={{ color: toast.color }}>check_circle</span>
          <span className="font-label-md">{toast.message}</span>
        </div>
      )}
    </div>
  );
}
