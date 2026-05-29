import React, { useState } from 'react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import GlassCard from '../components/ui/GlassCard';
import CategoryChips from '../components/ui/CategoryChips';
import { featuredArticle, dailyFeed, microcourse } from '../data/mockDashboard';

export default function Dashboard() {
  const [activeCategory, setActiveCategory] = useState('All');
  const categories = ['All', 'Crypto', 'Forex', 'My Microcourses'];

  return (
    <div className="bg-background text-on-surface min-h-screen pb-24">
      <TopBar />

      <main className="pt-20 px-container-padding space-y-stack-lg max-w-md mx-auto">
        <CategoryChips
          categories={categories}
          activeCategory={activeCategory}
          onCategoryChange={setActiveCategory}
        />

        <section className="relative rounded-xl overflow-hidden glass-card pulse-border-green group">
          <div className="p-stack-md space-y-stack-md">
            <div className="flex justify-between items-start">
              <div className="space-y-1">
                <span className="text-secondary font-label-sm text-label-sm uppercase tracking-widest">{featuredArticle.category}</span>
                <h2 className="font-title-md text-title-md text-on-surface">{featuredArticle.title}</h2>
              </div>
              <div className="bg-primary/20 p-2 rounded-lg">
                <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>trending_up</span>
              </div>
            </div>

            <div className="h-40 w-full relative bg-surface-container-lowest rounded-lg overflow-hidden border border-white/5">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent"></div>
              <svg className="absolute bottom-0 w-full h-24" preserveAspectRatio="none" viewBox="0 0 400 100">
                <path className="glow-path" d="M0,80 Q50,70 80,40 T150,50 T220,20 T300,60 T400,10" fill="none" stroke="#4be277" strokeWidth="2.5"></path>
              </svg>
              <div className="absolute top-4 right-4 flex flex-col items-end">
                <span className="font-mono-data text-mono-data text-primary">{featuredArticle.changeText}</span>
                <span className="font-label-sm text-label-sm text-on-surface-variant">{featuredArticle.changeLabel}</span>
              </div>
            </div>

            <button className="w-full py-3 bg-secondary text-on-secondary rounded-lg font-title-md text-title-md flex items-center justify-center gap-2 active:scale-[0.98] transition-transform shadow-[0_4px_12px_rgba(255,186,60,0.2)]">
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>play_circle</span>
              Play Audio Summary
            </button>
          </div>
        </section>

        <div className="space-y-stack-md">
          <div className="flex items-center justify-between">
            <h3 className="font-title-md text-title-md text-on-surface">Daily Feed</h3>
            <span className="font-label-sm text-label-sm text-secondary">View All</span>
          </div>

          {dailyFeed.map((item) => (
            <article key={item.id} className="relative h-[420px] rounded-xl overflow-hidden glass-card group">
              <img className="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:scale-105 transition-transform duration-700" src={item.image} alt={item.title} />
              <div className="absolute inset-0 bg-gradient-to-t from-surface via-surface/40 to-transparent"></div>
              <div className="absolute top-4 left-4 flex gap-2">
                <span className={`px-3 py-1 rounded-full text-on-tertiary font-label-sm text-label-sm font-bold uppercase ${item.type === 'Crypto Alert' ? 'bg-tertiary text-on-tertiary' : 'bg-secondary-container text-on-secondary-container'}`}>{item.type}</span>
                {item.isNew && <span className="px-3 py-1 rounded-full bg-secondary text-on-secondary font-label-sm text-label-sm font-bold uppercase animate-pulse">New</span>}
              </div>
              <div className="absolute bottom-6 left-6 right-6 space-y-3">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center border ${item.iconBgClass} ${item.iconBorderClass}`}>
                    <span className={`material-symbols-outlined ${item.iconColorClass}`}>{item.icon}</span>
                  </div>
                  <div>
                    <h4 className="font-headline-lg-mobile text-headline-lg-mobile text-white leading-tight">{item.title}</h4>
                    <p className="font-body-md text-body-md text-on-surface-variant line-clamp-2">{item.description}</p>
                  </div>
                </div>
              </div>
            </article>
          ))}

          <GlassCard className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary">school</span>
                <span className="text-secondary font-label-sm text-label-sm uppercase font-bold">Microcourse of the Day</span>
              </div>
              <span className="text-on-surface-variant font-label-sm text-label-sm">{microcourse.duration}</span>
            </div>
            <h4 className="font-title-md text-title-md text-on-surface">{microcourse.title}</h4>
            <div className="space-y-2">
              <div className="flex justify-between font-label-sm text-label-sm">
                <span className="text-on-surface-variant">Your Progress</span>
                <span className="text-secondary">{microcourse.progress}%</span>
              </div>
              <div className="w-full h-1.5 bg-surface-container rounded-full overflow-hidden">
                <div className="h-full bg-secondary transition-all" style={{ width: `${microcourse.progress}%` }}></div>
              </div>
            </div>
            <button className="w-full flex items-center justify-between p-4 bg-surface-container-high rounded-lg hover:bg-surface-variant transition-all active:scale-[0.98]">
              <span className="font-body-md text-body-md font-semibold">Resume Learning</span>
              <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
                <span className="material-symbols-outlined text-on-secondary" style={{ fontVariationSettings: "'FILL' 1" }}>play_arrow</span>
              </div>
            </button>
          </GlassCard>
        </div>
      </main>
      <BottomNav />
    </div>
  );
}

