import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useI18n } from '../../i18n/I18nContext';

export default function BottomNav() {
  const location = useLocation();
  const currentPath = location.pathname;
  const { t } = useI18n();

  const navItems = [
    { path: '/dashboard', icon: 'rss_feed', label: t('nav.feed') },
    { path: '/learn', icon: 'school', label: t('nav.learn'), fill: true },
    { path: '/profile', icon: 'person', label: t('nav.profile') }
  ];

  return (
    <nav className="fixed bottom-0 w-full z-50 bg-surface/80 backdrop-blur-xl border-t border-white/10 shadow-lg flex justify-around items-center h-20 pb-safe px-4">
      {navItems.map((item) => {
        const isActive = currentPath === item.path || (currentPath === '/' && item.path === '/dashboard');
        
        return (
          <Link
            key={item.label}
            to={item.path}
            className={`flex flex-col items-center justify-center gap-1 min-w-[64px] h-full transition-all active:scale-95 ${
              isActive ? 'text-[#f2ae2e]' : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            <div className={isActive ? 'bg-[#f2ae2e]/20 rounded-full px-5 py-1' : 'px-5 py-1'}>
              <span 
                className="material-symbols-outlined block" 
                style={item.fill || isActive ? { fontVariationSettings: "'FILL' 1" } : {}}
              >
                {item.icon}
              </span>
            </div>
            <span className="font-label-sm text-label-sm font-medium">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
