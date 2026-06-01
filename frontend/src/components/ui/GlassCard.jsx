import React from 'react';

export default function GlassCard({ children, className = '', ...props }) {
  return (
    <div 
      className={`glass-card rounded-xl border border-white/10 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
