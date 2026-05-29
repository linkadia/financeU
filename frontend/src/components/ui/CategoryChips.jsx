import React, { useState } from 'react';

export default function CategoryChips({ categories, activeCategory, onCategoryChange }) {
  return (
    <section className="flex overflow-x-auto hide-scrollbar gap-gutter py-2 -mx-container-padding px-container-padding">
      {categories.map((cat) => {
        const isActive = cat === activeCategory;
        return (
          <button
            key={cat}
            onClick={() => onCategoryChange(cat)}
            className={`px-5 py-2 rounded-full font-label-md text-label-md whitespace-nowrap transition-colors ${
              isActive 
                ? 'bg-secondary text-on-secondary shadow-[0_0_12px_rgba(255,186,60,0.4)]'
                : 'bg-surface-container-high text-on-surface-variant hover:bg-surface-variant/50'
            }`}
          >
            {cat}
          </button>
        );
      })}
    </section>
  );
}
