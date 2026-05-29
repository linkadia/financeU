export const learningCategories = [
  {
    id: 1,
    name: "Crypto",
    slug: "crypto",
    description: "Blockchain, wallets, tokens and DeFi basics.",
    icon: "currency_bitcoin",
    order: 1,
    is_active: true
  },
  {
    id: 2,
    name: "Forex",
    slug: "forex",
    description: "Currency pairs, pips, leverage and trading risk.",
    icon: "candlestick_chart",
    order: 2,
    is_active: true
  },
  {
    id: 3,
    name: "Personal Finance",
    slug: "personal-finance",
    description: "Budgeting, saving, debt and everyday money habits.",
    icon: "account_balance_wallet",
    order: 3,
    is_active: true
  }
];

export const courseTypes = [
  { id: 1, name: "Quick Start", slug: "quick-start", order: 1, is_active: true },
  { id: 2, name: "Fundamentals", slug: "fundamentals", order: 2, is_active: true },
  { id: 3, name: "Strategy", slug: "strategy", order: 3, is_active: true }
];

export const learningLevels = [
  { id: 1, name: "Beginner", slug: "beginner", order: 1, is_active: true },
  { id: 2, name: "Intermediate", slug: "intermediate", order: 2, is_active: true },
  { id: 3, name: "Advanced", slug: "advanced", order: 3, is_active: true }
];

export const courses = [
  {
    id: 1,
    title: "Crypto Basics",
    slug: "crypto-basics",
    description: "A beginner-friendly introduction to cryptocurrencies, Bitcoin and wallets.",
    category: learningCategories[0],
    course_type: courseTypes[0],
    level: learningLevels[0],
    thumbnail_url: "https://img.youtube.com/vi/Gc2en3nHxA4/hqdefault.jpg",
    estimated_duration_minutes: 24,
    order: 1,
    is_active: true,
    lessons: [
      {
        id: 1,
        title: "What is Bitcoin?",
        slug: "what-is-bitcoin",
        description: "A short explanation of Bitcoin as a decentralized digital asset.",
        youtube_url: "https://www.youtube.com/watch?v=Gc2en3nHxA4",
        youtube_video_id: "Gc2en3nHxA4",
        duration_minutes: 12,
        summary: "Bitcoin is introduced as a peer-to-peer monetary network with limited supply.",
        order: 1,
        is_active: true,
        quiz: {
          question: "What is one key characteristic of Bitcoin?",
          explanation: "Bitcoin runs on a decentralized network and has a limited supply schedule.",
          options: [
            { id: 1, text: "It is controlled by one central bank.", is_correct: false, order: 1 },
            { id: 2, text: "It is decentralized and has limited supply.", is_correct: true, order: 2 },
            { id: 3, text: "It can only be used by banks.", is_correct: false, order: 3 },
            { id: 4, text: "It has no public transaction history.", is_correct: false, order: 4 }
          ]
        }
      },
      {
        id: 2,
        title: "Crypto Wallets Explained",
        slug: "crypto-wallets-explained",
        description: "Learn what wallets store and why private keys matter.",
        youtube_url: "https://www.youtube.com/watch?v=AQO7KePXUEQ",
        youtube_video_id: "AQO7KePXUEQ",
        duration_minutes: 12,
        summary: "Wallets manage keys, not coins, and key security is essential.",
        order: 2,
        is_active: true,
        quiz: {
          question: "What does a crypto wallet primarily manage?",
          explanation: "Wallets manage cryptographic keys that allow users to control funds.",
          options: [
            { id: 5, text: "Passwords for streaming platforms.", is_correct: false, order: 1 },
            { id: 6, text: "Private and public keys.", is_correct: true, order: 2 },
            { id: 7, text: "Only fiat bank balances.", is_correct: false, order: 3 },
            { id: 8, text: "The blockchain itself.", is_correct: false, order: 4 }
          ]
        }
      }
    ]
  },
  {
    id: 2,
    title: "Forex Foundations",
    slug: "forex-foundations",
    description: "Understand currency pairs, pips, leverage and basic risk management.",
    category: learningCategories[1],
    course_type: courseTypes[1],
    level: learningLevels[0],
    thumbnail_url: "https://img.youtube.com/vi/YGUyI6K3eWY/hqdefault.jpg",
    estimated_duration_minutes: 30,
    order: 2,
    is_active: true,
    lessons: [
      {
        id: 3,
        title: "Currency Pairs",
        slug: "currency-pairs",
        description: "Understand base and quote currencies in the forex market.",
        youtube_url: "https://www.youtube.com/watch?v=YGUyI6K3eWY",
        youtube_video_id: "YGUyI6K3eWY",
        duration_minutes: 15,
        summary: "A currency pair expresses the price of one currency in another.",
        order: 1,
        is_active: true,
        quiz: {
          question: "In EUR/USD, what is EUR?",
          explanation: "The first currency in a pair is the base currency.",
          options: [
            { id: 9, text: "The quote currency.", is_correct: false, order: 1 },
            { id: 10, text: "The base currency.", is_correct: true, order: 2 },
            { id: 11, text: "The broker fee.", is_correct: false, order: 3 },
            { id: 12, text: "The interest rate.", is_correct: false, order: 4 }
          ]
        }
      },
      {
        id: 4,
        title: "Risk in Forex",
        slug: "risk-in-forex",
        description: "A practical overview of leverage, position size and stop losses.",
        youtube_url: "https://www.youtube.com/watch?v=0hL6ywQzE78",
        youtube_video_id: "0hL6ywQzE78",
        duration_minutes: 15,
        summary: "Risk management matters more than predicting every market move.",
        order: 2,
        is_active: true,
        quiz: {
          question: "Why is leverage risky?",
          explanation: "Leverage can magnify both gains and losses.",
          options: [
            { id: 13, text: "It removes all losses.", is_correct: false, order: 1 },
            { id: 14, text: "It magnifies gains and losses.", is_correct: true, order: 2 },
            { id: 15, text: "It guarantees a fixed return.", is_correct: false, order: 3 },
            { id: 16, text: "It only applies to savings accounts.", is_correct: false, order: 4 }
          ]
        }
      }
    ]
  },
  {
    id: 3,
    title: "Personal Finance Starter",
    slug: "personal-finance-starter",
    description: "Build a practical budget and start improving your financial habits.",
    category: learningCategories[2],
    course_type: courseTypes[0],
    level: learningLevels[0],
    thumbnail_url: "https://img.youtube.com/vi/sVKQn2I4HDM/hqdefault.jpg",
    estimated_duration_minutes: 26,
    order: 3,
    is_active: true,
    lessons: [
      {
        id: 5,
        title: "Budgeting Basics",
        slug: "budgeting-basics",
        description: "Learn how to separate income, fixed expenses and flexible spending.",
        youtube_url: "https://www.youtube.com/watch?v=sVKQn2I4HDM",
        youtube_video_id: "sVKQn2I4HDM",
        duration_minutes: 13,
        summary: "A budget is a plan for assigning every euro a job before spending it.",
        order: 1,
        is_active: true,
        quiz: {
          question: "What is the purpose of a budget?",
          explanation: "A budget helps plan income and expenses before money is spent.",
          options: [
            { id: 17, text: "To plan income and expenses.", is_correct: true, order: 1 },
            { id: 18, text: "To avoid checking transactions.", is_correct: false, order: 2 },
            { id: 19, text: "To increase every expense.", is_correct: false, order: 3 },
            { id: 20, text: "To replace income.", is_correct: false, order: 4 }
          ]
        }
      },
      {
        id: 6,
        title: "Emergency Funds",
        slug: "emergency-funds",
        description: "Understand why emergency savings reduce financial stress.",
        youtube_url: "https://www.youtube.com/watch?v=fVToMS2Q3XQ",
        youtube_video_id: "fVToMS2Q3XQ",
        duration_minutes: 13,
        summary: "Emergency funds protect your plan from unexpected expenses.",
        order: 2,
        is_active: true,
        quiz: {
          question: "What is an emergency fund for?",
          explanation: "It covers unexpected costs without disrupting the rest of the plan.",
          options: [
            { id: 21, text: "Unexpected expenses.", is_correct: true, order: 1 },
            { id: 22, text: "Guaranteed speculation.", is_correct: false, order: 2 },
            { id: 23, text: "Monthly entertainment only.", is_correct: false, order: 3 },
            { id: 24, text: "Avoiding all financial planning.", is_correct: false, order: 4 }
          ]
        }
      }
    ]
  }
];
