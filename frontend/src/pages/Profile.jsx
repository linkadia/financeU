import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import { getUserSettings, updateUserSettings } from '../api/users';
import { useI18n } from '../i18n/I18nContext';
import { clearCurrentUser, getCurrentUser, setCurrentUser } from '../utils/session';

const emptyForm = {
  username: '',
  email: '',
  display_name: '',
  onboarding_interests: [],
  onboarding_risk_profile: '',
  onboarding_goal: '',
  selected_agent: '',
  current_password: '',
  new_password: '',
};

export default function Profile() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const currentUser = useMemo(() => getCurrentUser(), []);
  const interests = [
    { id: 'crypto', label: t('profile.crypto') },
    { id: 'stocks', label: t('profile.stocks') },
    { id: 'forex', label: t('profile.forex') },
    { id: 'savings', label: t('profile.investingBasics') },
  ];
  const riskProfiles = [
    { id: 'low', label: t('profile.low') },
    { id: 'medium', label: t('profile.medium') },
    { id: 'high', label: t('profile.high') },
  ];
  const goals = [
    { id: 'emergency', label: t('profile.emergencyFund') },
    { id: 'investing', label: t('profile.cryptoStocks') },
    { id: 'purchase', label: t('profile.majorPurchase') },
    { id: 'retirement', label: t('profile.retirement') },
  ];
  const agents = [
    { id: 'finn', label: 'Finn' },
    { id: 'nova', label: 'Nova' },
  ];
  const [form, setForm] = useState(emptyForm);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!currentUser?.id) {
      navigate('/', { replace: true });
      return;
    }

    getUserSettings(currentUser.id)
      .then((settings) => {
        setForm({
          ...emptyForm,
          ...settings,
          onboarding_interests: settings.onboarding_interests ?? [],
        });
      })
      .catch((requestError) => setError(requestError.message))
      .finally(() => setIsLoading(false));
  }, [currentUser, navigate]);

  const updateField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
    setError('');
    setStatus('');
  };

  const toggleInterest = (id) => {
    setForm((current) => {
      const selected = new Set(current.onboarding_interests);
      selected.has(id) ? selected.delete(id) : selected.add(id);
      return { ...current, onboarding_interests: Array.from(selected) };
    });
    setError('');
    setStatus('');
  };

  const handleSave = async (event) => {
    event.preventDefault();
    if (!currentUser?.id) return;

    if (form.new_password && !form.current_password) {
      setError(t('profile.enterCurrentPassword'));
      return;
    }

    setIsSaving(true);
    setError('');
    setStatus('');

    try {
      const updatedUser = await updateUserSettings(currentUser.id, {
        ...form,
        display_name: form.username,
      });
      setCurrentUser(updatedUser);
      setForm((current) => ({
        ...current,
        ...updatedUser,
        onboarding_interests: updatedUser.onboarding_interests ?? [],
        current_password: '',
        new_password: '',
      }));
      setStatus(t('profile.settingsSaved'));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleLogout = () => {
    clearCurrentUser();
    navigate('/', { replace: true });
  };

  return (
    <div className="relative min-h-screen bg-background pb-24 text-on-surface">
      <TopBar />

      <main className="mx-auto max-w-md space-y-stack-md px-container-padding pt-20">
        <header className="space-y-1">
          <h1 className="text-[28px] font-semibold leading-9 text-on-surface">{t('profile.settings')}</h1>
          <p className="text-[14px] leading-5 text-on-surface-variant">
            {t('profile.accountDetails')}
          </p>
        </header>

        {isLoading ? (
          <section className="glass-card rounded-lg p-4 text-on-surface-variant">{t('common.loadingSettings')}</section>
        ) : (
          <form className="space-y-stack-md" onSubmit={handleSave}>
            <section className="glass-card rounded-lg p-4">
              <div className="mb-4 flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">badge</span>
                <h2 className="text-[18px] font-semibold leading-6">{t('profile.personalDetails')}</h2>
              </div>

              <div className="space-y-3">
                <TextField label={t('profile.username')} value={form.username} onChange={(value) => updateField('username', value)} autoComplete="username" />
                <TextField label={t('profile.email')} type="email" value={form.email} onChange={(value) => updateField('email', value)} autoComplete="email" />
              </div>
            </section>

            <section className="glass-card rounded-lg p-4">
              <div className="mb-4 flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary">tune</span>
                <h2 className="text-[18px] font-semibold leading-6">{t('profile.onboardingPreferences')}</h2>
              </div>

              <SettingGroup label={t('profile.interests')}>
                <div className="grid grid-cols-2 gap-2">
                  {interests.map((item) => (
                    <ChipButton
                      key={item.id}
                      selected={form.onboarding_interests.includes(item.id)}
                      onClick={() => toggleInterest(item.id)}
                    >
                      {item.label}
                    </ChipButton>
                  ))}
                </div>
              </SettingGroup>

              <SettingGroup label={t('profile.riskProfile')}>
                <SegmentedOptions options={riskProfiles} value={form.onboarding_risk_profile} onChange={(value) => updateField('onboarding_risk_profile', value)} />
              </SettingGroup>

              <SettingGroup label={t('profile.primaryGoal')}>
                <SelectField
                  value={form.onboarding_goal}
                  onChange={(value) => updateField('onboarding_goal', value)}
                  options={goals}
                  placeholder={t('common.selectOption')}
                />
              </SettingGroup>

              <SettingGroup label={t('profile.aiCompanion')}>
                <SegmentedOptions options={agents} value={form.selected_agent} onChange={(value) => updateField('selected_agent', value)} />
              </SettingGroup>
            </section>

            <section className="glass-card rounded-lg p-4">
              <div className="mb-4 flex items-center gap-2">
                <span className="material-symbols-outlined text-primary">lock</span>
                <h2 className="text-[18px] font-semibold leading-6">{t('profile.security')}</h2>
              </div>

              <div className="space-y-3">
                <TextField label={t('profile.currentPassword')} type="password" value={form.current_password} onChange={(value) => updateField('current_password', value)} autoComplete="current-password" />
                <TextField label={t('profile.newPassword')} type="password" value={form.new_password} onChange={(value) => updateField('new_password', value)} autoComplete="new-password" />
              </div>
            </section>

            {error && (
              <div className="rounded-lg border border-error/40 bg-error-container/30 px-4 py-3 text-[14px] font-medium text-on-error-container" role="alert">
                {error}
              </div>
            )}

            {status && (
              <div className="rounded-lg border border-secondary/30 bg-secondary/10 px-4 py-3 text-[14px] font-medium text-secondary" role="status">
                {status}
              </div>
            )}

            <div className="sticky bottom-20 -mx-container-padding bg-gradient-to-t from-background via-background/95 to-background/0 px-container-padding pb-4 pt-5">
              <button
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-secondary py-3.5 text-[16px] font-semibold text-on-secondary shadow-lg transition-all active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
                type="submit"
                disabled={isSaving}
              >
                <span className="material-symbols-outlined text-[20px]">save</span>
                {isSaving ? t('profile.saving') : t('profile.saveSettings')}
              </button>
            </div>

            <button
              className="flex w-full items-center justify-center gap-2 rounded-lg border border-white/10 bg-surface-container-lowest py-3 text-[15px] font-semibold text-on-surface-variant transition-colors hover:bg-surface-container"
              type="button"
              onClick={handleLogout}
            >
              <span className="material-symbols-outlined text-[20px]">logout</span>
              {t('profile.signOut')}
            </button>
          </form>
        )}
      </main>

      <BottomNav />
    </div>
  );
}

function TextField({ label, value, onChange, type = 'text', autoComplete }) {
  return (
    <label className="block">
      <span className="mb-1 block text-[12px] font-semibold uppercase leading-4 tracking-wide text-on-surface-variant">
        {label}
      </span>
      <input
        className="w-full rounded-lg border border-white/10 bg-surface-container-lowest px-3 py-3 text-[15px] text-on-surface placeholder:text-outline focus:border-secondary focus:ring-secondary"
        type={type}
        value={value ?? ''}
        autoComplete={autoComplete}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function SettingGroup({ label, children }) {
  return (
    <div className="mb-4 last:mb-0">
      <p className="mb-2 text-[12px] font-semibold uppercase leading-4 tracking-wide text-on-surface-variant">
        {label}
      </p>
      {children}
    </div>
  );
}

function ChipButton({ selected, onClick, children }) {
  return (
    <button
      className={`rounded-lg border px-3 py-2 text-[13px] font-semibold transition-colors ${
        selected
          ? 'border-secondary bg-secondary/15 text-secondary'
          : 'border-white/10 bg-surface-container-lowest text-on-surface-variant hover:bg-surface-container'
      }`}
      type="button"
      onClick={onClick}
    >
      {children}
    </button>
  );
}

function SegmentedOptions({ options, value, onChange }) {
  return (
    <div className="grid grid-cols-3 gap-2">
      {options.map((option) => (
        <ChipButton key={option.id} selected={value === option.id} onClick={() => onChange(option.id)}>
          {option.label}
        </ChipButton>
      ))}
    </div>
  );
}

function SelectField({ options, value, onChange, placeholder }) {
  return (
    <select
      className="w-full rounded-lg border border-white/10 bg-surface-container-lowest px-3 py-3 text-[15px] text-on-surface focus:border-secondary focus:ring-secondary"
      value={value ?? ''}
      onChange={(event) => onChange(event.target.value)}
    >
      <option value="">{placeholder}</option>
      {options.map((option) => (
        <option key={option.id} value={option.id}>
          {option.label}
        </option>
      ))}
    </select>
  );
}
