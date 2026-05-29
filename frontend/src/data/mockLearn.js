export const recommendedCourses = [
  {
    id: 1,
    title: "Mastering ETFs",
    category: "Investing",
    duration: "8 min",
    image: "https://lh3.googleusercontent.com/aida-public/AB6AXuAg7JNUvBGKi7fy65FIxpJZtBmzlmdMxyX1mfs_-Zqn_HyfyvTtZpLgyV0R8xQmmcoled8_lz7Tuk4wu0v-K4TYMF_1Udxw3-JvXTqr4ifoPPvEwq0Cg8G6x2fSpGBb3Ha_r489EVCI54R5x8_CIz1_jIAGRXlrOAsu97Vd3nRgeFIR0ydr1pVYlxbvtWZbTSL8lkXq5FrQWiOG7N3HJoc_k4G2-j7xV6QTCUTwRoT7THNWw53_0mkxxJMWtGYahafOZ13jPuQ1LS-q",
    categoryColor: "text-primary"
  },
  {
    id: 2,
    title: "Options 101",
    category: "Trading",
    duration: "12 min",
    image: "https://lh3.googleusercontent.com/aida-public/AB6AXuDwyrdQ-5x0wZjVmzoGpklJOw-7TKH7pw-vvtxD_Qf5ZAlB6W1wOEt2hF3q_NgOh8wG_7xTYkEQSE8gEYREmuLELX_phUOawU2yqamWIAIXfmxEbTAxS6UzDiD5glYztkFGyeCLusDqyc_pSKzQuL9DZLOlaMErksqGI1c_ZyjYckfS6ADhxcGEe2_9PuhmQZBu6uBmPXEKAdRAW4Sn0S64E4CwN2CF7rtQs1gPaTbHjmKOGPGp9JXEQqyQNnPotqGbXPGrl5LcNN78",
    categoryColor: "text-secondary"
  },
  {
    id: 3,
    title: "DeFi Deep Dive",
    category: "Crypto",
    duration: "15 min",
    image: "https://lh3.googleusercontent.com/aida-public/AB6AXuCWBiEVJLpNsx3KMIgomltGua9yoAMRPxSXF2TWUH-7BFB-IH5XMFqB_dZp-YruBxkR7g9Mku82J_ip8z7uZfww1SoVYN7NiVuKl_AzVlMtXXu45KGvBl4ZBskSmQ7I22gF3YvA7V7O3bELxYdYLZteS-IkOmvbR7SdRzUocBf5KJQcAhYs9THSXIh9WPBjq2Zf3wkgrw_hVZ8Y5TvvXY7nGuTXyQTQg5g1xtBhd9Vie0ufUfNGkZfMQNW20Jy92l31Ub3Wb4eVihYu",
    categoryColor: "text-tertiary-container"
  }
];

export const learningPaths = [
  {
    id: 1,
    title: "Crypto Fundamentals",
    completedLessons: 3,
    totalLessons: 10,
    progressPercent: 30,
    icon: "currency_bitcoin",
    color: "secondary",
    iconBgClass: "bg-secondary/10",
    iconTextClass: "text-secondary",
    barClass: "bg-secondary shadow-[0_0_8px_rgba(81,225,120,0.5)]",
    actionIcon: "play_circle"
  },
  {
    id: 2,
    title: "Advanced Trading",
    completedLessons: 7,
    totalLessons: 12,
    progressPercent: 58,
    icon: "show_chart",
    color: "primary",
    iconBgClass: "bg-primary/10",
    iconTextClass: "text-primary",
    barClass: "bg-primary shadow-[0_0_8px_rgba(255,207,131,0.5)]",
    actionIcon: "play_circle",
    isActive: true
  },
  {
    id: 3,
    title: "Wealth Management",
    completedLessons: 0,
    totalLessons: 8,
    progressPercent: 0,
    icon: "account_balance_wallet",
    color: "tertiary-container",
    iconBgClass: "bg-tertiary-container/10",
    iconTextClass: "text-tertiary-container",
    barClass: "bg-tertiary-container",
    actionIcon: "lock"
  }
];

export const dailyInsight = {
  tip: "Diversification isn't just about stocks; consider asset correlation across your entire portfolio.",
  streak: 12,
  ranking: "Top 5%"
};
