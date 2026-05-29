import React, { createContext, useContext, useMemo, useState } from 'react';

const DRAFT_KEY = 'finanu.onboardingDraft';

const initialOnboarding = {
  selectedAgent: '',
  interests: [],
  riskProfile: '',
  goal: '',
};

const OnboardingContext = createContext(null);

function getStoredDraft() {
  try {
    return {
      ...initialOnboarding,
      ...JSON.parse(sessionStorage.getItem(DRAFT_KEY)),
    };
  } catch {
    return initialOnboarding;
  }
}

export function OnboardingProvider({ children }) {
  const [answers, setAnswers] = useState(getStoredDraft);

  const value = useMemo(() => {
    const updateAnswer = (field, value) => {
      setAnswers((current) => {
        const next = { ...current, [field]: value };
        sessionStorage.setItem(DRAFT_KEY, JSON.stringify(next));
        return next;
      });
    };

    const clearOnboardingDraft = () => {
      sessionStorage.removeItem(DRAFT_KEY);
      setAnswers(initialOnboarding);
    };

    return { answers, updateAnswer, clearOnboardingDraft };
  }, [answers]);

  return (
    <OnboardingContext.Provider value={value}>
      {children}
    </OnboardingContext.Provider>
  );
}

export function useOnboarding() {
  const context = useContext(OnboardingContext);
  if (!context) {
    throw new Error('useOnboarding must be used inside OnboardingProvider');
  }
  return context;
}
