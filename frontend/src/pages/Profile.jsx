import React from 'react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import GlassCard from '../components/ui/GlassCard';
import { userProfile, badges } from '../data/mockProfile';

export default function Profile() {
  return (
    <div className="bg-background text-on-surface min-h-screen pb-24 relative">
      <TopBar />

      <main className="pt-20 px-container-padding max-w-md mx-auto space-y-stack-lg">
        <section className="glass-card rounded-xl p-container-padding relative overflow-hidden">
          <div className="absolute -top-10 -right-10 w-32 h-32 bg-primary/10 blur-[60px] rounded-full"></div>
          <div className="flex justify-between items-end relative z-10">
            <div>
              <p className="font-label-sm text-label-sm text-on-surface-variant mb-1 uppercase tracking-wider">Total Balance</p>
              <div className="flex items-baseline gap-2">
                <span className="font-headline-xl text-headline-xl text-primary">1,250</span>
                <span className="font-title-md text-title-md text-primary">Points</span>
              </div>
            </div>
            <div className="text-right">
              <p className="font-label-sm text-label-sm text-on-surface-variant mb-1">Rank: Silver III</p>
              <div className="w-24 h-2 bg-surface-container-highest rounded-full overflow-hidden">
                <div className="bg-[#51e178] h-full w-[65%] shadow-[0_0_8px_rgba(81,225,120,0.5)]"></div>
              </div>
            </div>
          </div>
        </section>

        <section className="space-y-stack-md">
          <div className="flex justify-between items-center">
            <h2 className="font-title-md text-title-md text-on-surface">Your Achievements & Badges</h2>
            <button className="text-primary font-label-md text-label-md">View All</button>
          </div>
          <div className="grid grid-cols-3 gap-gutter">
            {badges.map((badge, index) => (
              <GlassCard key={badge.id} className={`p-base flex flex-col items-center text-center gap-2 ${index === 0 ? 'pulse-border-green' : ''} ${index === 2 ? 'grayscale opacity-50 relative' : ''}`}>
                {index === 2 && (
                  <div className="absolute top-1 right-1">
                    <span className="material-symbols-outlined text-[16px]">lock</span>
                  </div>
                )}
                <div className={`w-14 h-14 rounded-full flex items-center justify-center border ${index === 2 ? 'bg-surface-variant border-outline/20' : `bg-${badge.color}/20 border-${badge.color}/30`}`}>
                  <span className={`material-symbols-outlined text-[32px] ${index === 2 ? 'text-outline' : `text-${badge.color}`}`} style={index !== 2 ? { fontVariationSettings: "'FILL' 1" } : {}}>{badge.icon}</span>
                </div>
                <span className={`font-label-sm text-label-sm leading-tight ${index === 2 ? 'text-outline' : 'text-on-surface'}`}>{badge.title}</span>
              </GlassCard>
            ))}
          </div>
        </section>

        <section className="glass-card rounded-xl p-container-padding space-y-stack-md border-l-4 border-primary">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>quiz</span>
            <h2 className="font-title-md text-title-md text-on-surface">Today's Trading Playground Quiz</h2>
          </div>
          <div className="p-4 bg-surface-container rounded-lg border border-white/5">
            <p className="font-body-md text-body-md text-on-surface leading-snug">What does a "Bull Market" mean in financial terms?</p>
          </div>
          <div className="grid grid-cols-1 gap-base">
            <button className="w-full text-left p-4 rounded-xl border border-white/10 hover:border-primary/50 hover:bg-primary/5 transition-all group active:scale-[0.98]">
              <div className="flex justify-between items-center">
                <span className="font-label-md text-label-md text-on-surface">Prices are rising and optimism is high</span>
                <span className="material-symbols-outlined text-primary opacity-0 group-hover:opacity-100 transition-opacity">check_circle</span>
              </div>
            </button>
            <button className="w-full text-left p-4 rounded-xl border border-white/10 hover:border-error/50 hover:bg-error/5 transition-all group active:scale-[0.98]">
              <div className="flex justify-between items-center">
                <span className="font-label-md text-label-md text-on-surface">Prices are falling and pessimism prevails</span>
                <span className="material-symbols-outlined text-error opacity-0 group-hover:opacity-100 transition-opacity">cancel</span>
              </div>
            </button>
          </div>
        </section>

        <section className="grid grid-cols-2 gap-gutter">
          <GlassCard className="p-container-padding flex flex-col justify-between aspect-square">
            <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>workspace_premium</span>
            <div>
              <p className="font-headline-lg-mobile text-headline-lg-mobile text-on-surface">#24</p>
              <p className="font-label-sm text-label-sm text-on-surface-variant">Global Leaderboard</p>
            </div>
          </GlassCard>
          <GlassCard className="p-container-padding flex flex-col justify-between aspect-square">
            <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>auto_graph</span>
            <div>
              <p className="font-headline-lg-mobile text-headline-lg-mobile text-on-surface">12</p>
              <p className="font-label-sm text-label-sm text-on-surface-variant">Quizzes Solved</p>
            </div>
          </GlassCard>
        </section>
      </main>

      <BottomNav />
    </div>
  );
}
