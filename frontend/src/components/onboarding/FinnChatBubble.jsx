import React from 'react';

/**
 * Finn's AI chat bubble shown at the top of each onboarding step.
 */
export default function FinnChatBubble({ message, time = '10:24 AM' }) {
  return (
    <div className="flex flex-col gap-base max-w-[85%]">
      <div className="glass-panel p-stack-md rounded-xl rounded-tl-none">
        <p className="font-body-md text-on-surface">{message}</p>
      </div>
      <span className="font-label-sm text-on-surface-variant ml-1">{time}</span>
    </div>
  );
}
