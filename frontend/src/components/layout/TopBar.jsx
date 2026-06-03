import React from 'react';
import LanguageSwitcher from '../LanguageSwitcher';
import logoUrl from '../../assets/logoFinancU.svg';

export default function TopBar() {
  return (
    <header className="fixed top-0 w-full z-50 bg-surface/80 backdrop-blur-xl dark:bg-surface/80 border-b border-white/10 shadow-sm flex justify-between items-center px-container-padding h-16">
      <div className="flex items-center gap-3">
        <img
          alt="FinanU"
          className="h-6 w-auto object-contain"
          src={logoUrl}
          width={50}
          height={50}
        />
      </div>
      <div className="flex items-center">
        <LanguageSwitcher compact />
      </div>
    </header>
  );
}
