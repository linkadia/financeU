import React from 'react';

/**
 * Finn's AI chat bubble shown at the top of each onboarding step.
 */
export default function FinnChatBubble({ message, time = '10:24 AM' }) {
  return (
    <div className="sticky top-0 z-30 -mx-container-padding bg-background/95 px-container-padding pb-3 pt-3 backdrop-blur-xl">
      <div className="flex max-w-[92%] flex-col gap-1">
        <div className="glass-panel rounded-xl rounded-tl-none px-4 py-3">
          <p className="text-[15px] leading-5 text-on-surface">{message}</p>
        </div>
        <span className="ml-1 text-[11px] font-medium leading-4 tracking-wide text-on-surface-variant">
          {time}
        </span>
      </div>
    </div>
  );
}
