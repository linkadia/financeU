import React from 'react';

export default function CategoryChips({ categories, activeCategory, onCategoryChange, className = '' }) {
  return (
    <section className={`flex overflow-x-auto hide-scrollbar gap-gutter py-2 -mx-container-padding px-container-padding ${className}`}>
      {categories.map((cat) => {
        const id = typeof cat === 'string' ? cat : cat.id;
        const label = typeof cat === 'string' ? cat : cat.label;
        const isActive = id === activeCategory;
        return (
          <button
            key={id}
            onClick={() => onCategoryChange(id)}
            className={`px-5 py-2 rounded-full font-label-md text-label-md whitespace-nowrap transition-colors ${
              isActive 
                ? 'bg-secondary text-on-secondary shadow-[0_0_12px_rgba(255,186,60,0.4)]'
                : 'bg-surface-container-high text-on-surface-variant hover:bg-surface-variant/50'
            }`}
          >
            {label}
          </button>
        );
      })}
    </section>
  );
}
