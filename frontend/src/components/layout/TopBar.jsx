import React from 'react';

export default function TopBar() {
  return (
    <header className="fixed top-0 w-full z-50 bg-surface/80 backdrop-blur-xl dark:bg-surface/80 border-b border-white/10 shadow-sm flex justify-between items-center px-container-padding h-16">
      <div className="flex items-center gap-3">
        <img
          alt="FinanU"
          className="h-8 w-auto object-contain"
          src="https://lh3.googleusercontent.com/aida-public/AB6AXuC9wD1cKdaA927sd6AdZWeF2pjlIWA2_3jZyoj1jfq3ODBKnzDNuywPo7NlqmH1F75XHOxrC10fUOy4ihNWc78v9svW2PblWiGZCi3SBioiPhl4WfQsO3V5_k2oPW1Dz2uLitRU8SxhMoyqhszEXsAJSSd22_-G6Xu6D45_u2VRQZHz2fEQLVkyTzjvxvX79ACozIylitC8IY2nNiW-qOIJvv662Gx3V4mnGYSTMjKDV2hbk3aUPSwsRk-9Z77G7s4a9w7F6AZcKykr"
        />
      </div>
      <div className="flex items-center gap-4">
        <button className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-surface-variant/50 transition-colors active:scale-95 duration-200">
          <span className="material-symbols-outlined text-primary">notifications</span>
        </button>
      </div>
    </header>
  );
}
