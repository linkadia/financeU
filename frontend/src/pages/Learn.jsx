import React from 'react';
import TopBar from '../components/layout/TopBar';
import BottomNav from '../components/layout/BottomNav';
import GlassCard from '../components/ui/GlassCard';
import { recommendedCourses, learningPaths, dailyInsight } from '../data/mockLearn';

export default function Learn() {
  return (
    <div className="bg-background text-on-surface min-h-screen pb-24 selection:bg-primary-container/30">
      <TopBar />

      <main className="pt-20 pb-32 max-w-md mx-auto">
        <section className="px-container-padding pt-stack-lg pb-stack-lg">
          <GlassCard className="p-stack-lg relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-secondary/10 rounded-full blur-3xl -mr-16 -mt-16"></div>
            <div className="flex items-center justify-between relative z-10">
              <div className="space-y-base">
                <h1 className="font-headline-lg-mobile text-headline-lg-mobile tracking-tight text-on-surface">Level Up Your Finance</h1>
                <p className="text-on-surface-variant font-body-md max-w-[200px]">Unlock institutional-grade insights daily.</p>
                <button className="mt-base bg-secondary text-on-secondary px-stack-md py-2 rounded-lg font-label-md hover:brightness-110 active:scale-95 transition-all">
                  Continue Journey
                </button>
              </div>
              <div className="relative flex items-center justify-center">
                <svg className="w-24 h-24 transform -rotate-90">
                  <circle className="text-white/5" cx="48" cy="48" fill="transparent" r="40" stroke="currentColor" strokeWidth="8"></circle>
                  <circle className="text-secondary drop-shadow-[0_0_8px_rgba(81,225,120,0.5)]" cx="48" cy="48" fill="transparent" r="40" stroke="currentColor" strokeDasharray="251.2" strokeDashoffset="163.28" strokeWidth="8"></circle>
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                  <span className="font-mono-data text-[18px] text-secondary">35%</span>
                  <span className="text-[8px] font-label-sm uppercase tracking-widest text-on-surface-variant">Progress</span>
                </div>
              </div>
            </div>
          </GlassCard>
        </section>

        <section className="mb-stack-lg">
          <div className="px-container-padding flex justify-between items-center mb-stack-md">
            <h2 className="font-title-md text-title-md">Recommended for You</h2>
            <button className="text-primary font-label-md flex items-center gap-1">
              View All <span className="material-symbols-outlined text-sm">chevron_right</span>
            </button>
          </div>
          <div className="flex overflow-x-auto hide-scrollbar gap-gutter px-container-padding snap-x">
            {recommendedCourses.map((course) => (
              <div key={course.id} className="snap-start min-w-[200px] flex-shrink-0">
                <div className="relative w-full aspect-[4/3] rounded-xl overflow-hidden mb-2">
                  <img className="w-full h-full object-cover" src={course.image} alt={course.title} />
                  <div className="absolute bottom-2 left-2">
                    <span className="bg-surface/80 backdrop-blur-md text-[10px] font-label-sm px-2 py-1 rounded-lg text-on-surface">{course.duration}</span>
                  </div>
                </div>
                <span className={`text-[10px] font-label-sm uppercase tracking-widest mb-1 block ${course.categoryColor}`}>{course.category}</span>
                <h3 className="font-label-md text-label-md line-clamp-1">{course.title}</h3>
              </div>
            ))}
          </div>
        </section>

        <section className="px-container-padding">
          <h2 className="font-title-md text-title-md mb-stack-md">Learning Paths</h2>
          <div className="grid grid-cols-1 gap-stack-md">
            {learningPaths.map((path) => (
              <GlassCard key={path.id} className={`p-stack-md flex items-center gap-stack-md hover:bg-surface-container-high transition-all group ${path.isActive ? 'border-primary/20 bg-primary/5' : ''}`}>
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${path.iconBgClass} ${path.iconTextClass}`}>
                  <span className="material-symbols-outlined text-2xl">{path.icon}</span>
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-center mb-1">
                    <h3 className="font-title-md text-label-md">{path.title}</h3>
                    <span className="text-[10px] font-mono-data text-on-surface-variant">{path.completedLessons}/{path.totalLessons} Lessons</span>
                  </div>
                  <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${path.barClass}`} style={{ width: `${path.progressPercent}%` }}></div>
                  </div>
                </div>
                <span className={`material-symbols-outlined transition-colors ${path.isActive ? 'text-primary' : 'text-on-surface-variant group-hover:text-primary'}`} style={path.isActive ? { fontVariationSettings: "'FILL' 1" } : {}}>{path.actionIcon}</span>
              </GlassCard>
            ))}
          </div>
        </section>

        <section className="px-container-padding mt-stack-lg">
          <div className="grid grid-cols-2 gap-stack-md">
            <GlassCard className="col-span-2 p-stack-md bg-gradient-to-br from-secondary/5 to-transparent border-secondary/20">
              <div className="flex items-center gap-2 mb-2">
                <span className="material-symbols-outlined text-secondary text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>tips_and_updates</span>
                <span className="text-[10px] font-label-sm uppercase tracking-wider text-secondary">Tip of the Day</span>
              </div>
              <p className="font-body-md text-on-surface leading-tight">{dailyInsight.tip}</p>
            </GlassCard>
            <GlassCard className="p-stack-md flex flex-col justify-between">
              <h4 className="font-label-sm text-on-surface-variant">Streak</h4>
              <div className="flex items-end gap-1">
                <span className="text-headline-lg-mobile font-mono-data text-primary">{dailyInsight.streak}</span>
                <span className="text-label-sm text-on-surface-variant pb-1">days</span>
              </div>
            </GlassCard>
            <GlassCard className="p-stack-md flex flex-col justify-between overflow-hidden relative">
              <div className="absolute -right-2 -bottom-2 opacity-10 rotate-12">
                <span className="material-symbols-outlined text-6xl">military_tech</span>
              </div>
              <h4 className="font-label-sm text-on-surface-variant">Ranking</h4>
              <div className="flex items-end gap-1">
                <span className="text-headline-lg-mobile font-mono-data text-on-surface">{dailyInsight.ranking}</span>
              </div>
            </GlassCard>
          </div>
        </section>
      </main>

      <BottomNav />
    </div>
  );
}
