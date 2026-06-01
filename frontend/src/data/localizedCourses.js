const categoryCopy = {
  pl: [
    ['Finanse osobiste', 'Budżetowanie, oszczędzanie, długi i codzienne nawyki finansowe.'],
    ['Inwestowanie', 'ETF-y, dywersyfikacja, ryzyko i długi horyzont.'],
    ['Krypto', 'Bitcoin, portfele, bezpieczeństwo i ryzyko zmienności.'],
    ['Forex', 'Pary walutowe, dźwignia, pipsy i zarządzanie ryzykiem.'],
    ['Ekonomia', 'Inflacja, stopy procentowe i decyzje banków centralnych.'],
  ],
  en: [
    ['Personal Finance', 'Budgeting, saving, debt and everyday money habits.'],
    ['Investing', 'ETFs, diversification, risk and long-term compounding.'],
    ['Crypto', 'Bitcoin, wallets, security and volatility risk.'],
    ['Forex', 'Currency pairs, leverage, pips and risk management.'],
    ['Economics', 'Inflation, interest rates and central-bank decisions.'],
  ],
};

const typeCopy = {
  pl: ['Wideo', 'Audio', 'Tekst', 'Kurs'],
  en: ['Video', 'Audio', 'Text', 'Course'],
};

const levelCopy = {
  pl: ['Początkujący', 'Średnio zaawansowany', 'Zaawansowany'],
  en: ['Beginner', 'Intermediate', 'Advanced'],
};

const exams = {
  en: {
    budget: [
      ['What is the main job of a budget?', ['To plan income and expenses.', 'To hide transactions.', 'To spend every euro immediately.'], 0],
      ['Why separate fixed and flexible spending?', ['It shows what can be adjusted.', 'It removes all taxes.', 'It guarantees investment returns.'], 0],
      ['A good budget should be:', ['Reviewed and updated.', 'Ignored after one month.', 'Only kept in memory.'], 0],
    ],
    literacyCourse: [
      ['Why use a structured finance course?', ['It builds concepts in order.', 'It removes the need to make decisions.', 'It guarantees wealth.'], 0],
      ['Which topic belongs in financial literacy?', ['Debt and interest.', 'Only chart patterns.', 'Only luxury spending.'], 0],
      ['What should a learner do after a lesson?', ['Apply one idea to their own plan.', 'Skip reflection.', 'Take more risk immediately.'], 0],
    ],
    planetMoney: [
      ['What can an economics podcast help with?', ['Understanding money stories in context.', 'Replacing a personal budget.', 'Guaranteeing stock picks.'], 0],
      ['Why listen regularly?', ['To build intuition about markets and incentives.', 'To avoid learning basics.', 'To copy every opinion.'], 0],
      ['What is the right posture for podcast learning?', ['Extract principles, then verify decisions.', 'Treat every episode as advice.', 'Ignore risk.'], 0],
    ],
    etf: [
      ['What is a common benefit of ETFs?', ['Diversification.', 'Guaranteed profit.', 'No market risk.'], 0],
      ['Why do fees matter?', ['They compound against returns over time.', 'They only matter for banks.', 'They remove volatility.'], 0],
      ['What should match an ETF choice?', ['Goal, risk and time horizon.', 'Only social media trends.', 'A random ticker.'], 0],
    ],
    bitcoin: [
      ['Which feature best describes Bitcoin?', ['A decentralized network.', 'A central-bank account.', 'A guaranteed-income product.'], 0],
      ['What does limited supply mean?', ['Issuance follows a capped schedule.', 'Units are unlimited.', 'Every bank can print it.'], 0],
      ['What is a key user responsibility?', ['Protecting keys and avoiding scams.', 'Sharing seed phrases.', 'Ignoring custody.'], 0],
    ],
    forexRisk: [
      ['Why is leverage risky?', ['It magnifies gains and losses.', 'It removes all losses.', 'It guarantees fixed returns.'], 0],
      ['What helps manage trading risk?', ['Position sizing and stop-loss planning.', 'Increasing size after every loss.', 'Ignoring volatility.'], 0],
      ['What is a realistic learning goal?', ['Understand mechanics before trading.', 'Win every trade.', 'Avoid all losses forever.'], 0],
    ],
  },
  pl: {
    budget: [
      ['Po co tworzyć budżet?', ['Aby planować dochody i wydatki.', 'Aby ukrywać transakcje.', 'Aby wydawać wszystko od razu.'], 0],
      ['Dlaczego warto mieć poduszkę bezpieczeństwa?', ['Chroni przed niespodziewanymi kosztami.', 'Gwarantuje zysk.', 'Zastępuje każdy dochód.'], 0],
      ['Co pomaga utrzymać plan?', ['Regularny przegląd wydatków.', 'Brak kontroli.', 'Losowe decyzje.'], 0],
    ],
    restart: [
      ['Co jest pierwszym krokiem przy finansowym restarcie?', ['Ustalenie sytuacji i priorytetów.', 'Ignorowanie problemu.', 'Ryzykowna inwestycja na start.'], 0],
      ['Dlaczego małe kroki mają sens?', ['Kumulują się w czasie.', 'Działają tylko jeden dzień.', 'Zawsze są bez znaczenia.'], 0],
      ['Co ogranicza powrót do błędów?', ['System i regularność.', 'Większy dług konsumpcyjny.', 'Brak celów.'], 0],
    ],
    podcast: [
      ['Do czego przydaje się podcast finansowy?', ['Do budowania nawyku uczenia się.', 'Do gwarantowanych rekomendacji.', 'Do unikania liczb.'], 0],
      ['Jak słuchać treści edukacyjnych?', ['Notować jedną rzecz do wdrożenia.', 'Kopiować każdą opinię.', 'Pomijać kontekst.'], 0],
      ['Co powinno zostać po odcinku?', ['Lepsze pytanie lub konkretna decyzja.', 'Impulsywny zakup.', 'Większe ryzyko.'], 0],
    ],
    etf: [
      ['Po co inwestorzy używają ETF-ów?', ['Dla szerokiej ekspozycji i dywersyfikacji.', 'Dla gwarancji zysku.', 'Dla braku zmienności.'], 0],
      ['Dlaczego koszty są ważne?', ['Obniżają wynik przez lata.', 'Nie mają znaczenia.', 'Usuwają ryzyko.'], 0],
      ['Co powinno pasować do strategii?', ['Cel, ryzyko i horyzont.', 'Tylko modny ticker.', 'Przypadkowa decyzja.'], 0],
    ],
    cryptoSafety: [
      ['Co jest ważne w krypto?', ['Bezpieczeństwo kluczy i zrozumienie ryzyka.', 'Udostępnianie seed phrase.', 'Ignorowanie zmienności.'], 0],
      ['Czym jest zmienność?', ['Silne wahania ceny.', 'Gwarantowany zysk.', 'Stała cena.'], 0],
      ['Jaka postawa jest rozsądna?', ['Najpierw edukacja, potem decyzje.', 'Najpierw pożyczka.', 'Decyzje pod presją.'], 0],
    ],
    economy: [
      ['Dlaczego inflacja ma znaczenie?', ['Zmienia siłę nabywczą pieniądza.', 'Nie wpływa na budżet.', 'Gwarantuje wyższy zysk.'], 0],
      ['Co robią stopy procentowe?', ['Wpływają na koszt kredytu i oszczędzanie.', 'Usuwają ryzyko.', 'Zawsze rosną.'], 0],
      ['Po co śledzić podstawy ekonomii?', ['Aby lepiej rozumieć decyzje finansowe.', 'Aby przewidzieć każdy dzień rynku.', 'Aby przestać budżetować.'], 0],
    ],
  },
};

const resources = {
  en: [
    {
      id: 101,
      title: 'Money Habits Starter',
      slug: 'money-habits-starter',
      description: 'A mixed English path with video, course, article and podcast resources.',
      category: 'personal-finance',
      level: 'beginner',
      thumbnail_url: 'https://img.youtube.com/vi/sVKQn2I4HDM/hqdefault.jpg',
      lessons: [
        {
          id: 1001,
          key: 'budget',
          title: 'Budgeting Basics',
          description: 'A short video lesson about planning income, fixed costs and flexible spending.',
          content_type: 'video',
          provider: 'YouTube',
          source_channel: 'Personal finance education',
          source_url: 'https://www.youtube.com/watch?v=sVKQn2I4HDM',
          youtube_video_id: 'sVKQn2I4HDM',
          duration_minutes: 13,
          summary: 'Budgeting gives money a job before it is spent and makes trade-offs visible.',
        },
        {
          id: 1002,
          key: 'literacyCourse',
          title: 'Financial Literacy Course',
          description: 'A free structured course for the core concepts of personal finance.',
          content_type: 'course',
          provider: 'Khan Academy',
          source_channel: 'Khan Academy',
          source_url: 'https://www.khanacademy.org/college-careers-more/financial-literacy',
          duration_minutes: 20,
          summary: 'A structured course helps connect budgeting, saving, debt and long-term planning.',
        },
        {
          id: 1003,
          key: 'planetMoney',
          title: 'Planet Money Podcast',
          description: 'Short economics stories that build intuition about money, incentives and markets.',
          content_type: 'audio',
          provider: 'NPR Podcast',
          source_channel: 'Planet Money',
          source_url: 'https://www.npr.org/podcasts/510289/planet-money',
          duration_minutes: 25,
          summary: 'Podcast learning works well for context: listen for principles, not direct financial advice.',
        },
      ],
    },
    {
      id: 102,
      title: 'Investing Foundations',
      slug: 'investing-foundations',
      description: 'Free English resources about ETFs, diversification and long-term investing.',
      category: 'investing',
      level: 'beginner',
      thumbnail_url: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=900&q=80',
      lessons: [
        {
          id: 1004,
          key: 'etf',
          title: 'ETF Basics',
          description: 'A text lesson about ETF structure, diversification and costs.',
          content_type: 'article',
          provider: 'Investopedia',
          source_channel: 'Investopedia',
          source_url: 'https://www.investopedia.com/terms/e/etf.asp',
          duration_minutes: 12,
          summary: 'ETFs can offer diversified exposure, but fees, risk and fit with your goal still matter.',
        },
      ],
    },
    {
      id: 103,
      title: 'Crypto and Forex Risk',
      slug: 'crypto-forex-risk',
      description: 'English video lessons for high-volatility markets and risk-first thinking.',
      category: 'crypto',
      level: 'beginner',
      thumbnail_url: 'https://img.youtube.com/vi/Gc2en3nHxA4/hqdefault.jpg',
      lessons: [
        {
          id: 1005,
          key: 'bitcoin',
          title: 'What is Bitcoin?',
          description: 'A short video explanation of Bitcoin as a decentralized digital asset.',
          content_type: 'video',
          provider: 'YouTube',
          source_channel: 'WeUseCoins',
          source_url: 'https://www.youtube.com/watch?v=Gc2en3nHxA4',
          youtube_video_id: 'Gc2en3nHxA4',
          duration_minutes: 12,
          summary: 'Bitcoin is introduced as a peer-to-peer monetary network with public records and limited supply.',
        },
        {
          id: 1006,
          key: 'forexRisk',
          title: 'Forex Risk Basics',
          description: 'A video lesson about leverage, currency pairs and position risk.',
          content_type: 'video',
          provider: 'YouTube',
          source_channel: 'Forex education',
          source_url: 'https://www.youtube.com/watch?v=YGUyI6K3eWY',
          youtube_video_id: 'YGUyI6K3eWY',
          duration_minutes: 15,
          summary: 'Forex education should start with mechanics and risk before any trading strategy.',
        },
      ],
    },
  ],
  pl: [
    {
      id: 201,
      title: 'Finanse osobiste po polsku',
      slug: 'finanse-osobiste-po-polsku',
      description: 'Polskie materiały wideo i audio o budżecie, bezpieczeństwie i lepszych decyzjach.',
      category: 'personal-finance',
      level: 'beginner',
      thumbnail_url: 'https://img.youtube.com/vi/FfhSj9hXykw/hqdefault.jpg',
      lessons: [
        {
          id: 2001,
          key: 'budget',
          title: 'Sprawdzone sposoby bogacenia się',
          description: 'Rozmowa o kontroli wydatków, poduszce bezpieczeństwa i inwestowaniu nadwyżek.',
          content_type: 'video',
          provider: 'YouTube',
          source_channel: 'Duży w Maluchu / Marcin Iwuć',
          source_url: 'https://www.youtube.com/watch?v=FfhSj9hXykw',
          youtube_video_id: 'FfhSj9hXykw',
          duration_minutes: 55,
          summary: 'Materiał porządkuje trzy filary: kontrolę wydatków, zwiększanie dochodów i inwestowanie nadwyżek.',
        },
        {
          id: 2002,
          key: 'restart',
          title: '40 lat i kasy brak',
          description: 'Lekcja o finansowym restarcie, priorytetach i unikaniu kosztownych błędów.',
          content_type: 'video',
          provider: 'YouTube',
          source_channel: 'Marcin Iwuć',
          source_url: 'https://www.youtube.com/watch?v=w6ovkxeXaOg',
          youtube_video_id: 'w6ovkxeXaOg',
          duration_minutes: 24,
          summary: 'Plan finansowy można zacząć później, ale wymaga jasnych priorytetów i konsekwencji.',
        },
        {
          id: 2003,
          key: 'podcast',
          title: 'Finanse Bardzo Osobiste Podcast',
          description: 'Podcast do regularnej nauki o pieniądzach, rodzinnych finansach i decyzjach.',
          content_type: 'audio',
          provider: 'Podcast',
          source_channel: 'Marcin Iwuć',
          source_url: 'https://marciniwuc.com/podcast/',
          duration_minutes: 30,
          summary: 'Audio dobrze działa jako nawyk: po odcinku warto zapisać jedną rzecz do wdrożenia.',
        },
      ],
    },
    {
      id: 202,
      title: 'Inwestowanie i ETF-y',
      slug: 'inwestowanie-i-etfy',
      description: 'Polskie teksty i podcasty o ETF-ach, kosztach i spokojnym inwestowaniu.',
      category: 'investing',
      level: 'intermediate',
      thumbnail_url: 'https://images.unsplash.com/photo-1642543492481-44e81e3914a7?auto=format&fit=crop&w=900&q=80',
      lessons: [
        {
          id: 2004,
          key: 'etf',
          title: 'ETF-y i inwestowanie pasywne',
          description: 'Tekstowy zasób o ekspozycji rynkowej, kosztach i dywersyfikacji.',
          content_type: 'article',
          provider: 'Inwestomat',
          source_channel: 'Inwestomat',
          source_url: 'https://inwestomat.eu/',
          duration_minutes: 14,
          summary: 'ETF-y mogą ułatwić dywersyfikację, ale strategia musi pasować do celu, ryzyka i horyzontu.',
        },
        {
          id: 2005,
          key: 'podcast',
          title: 'Inwestomat Podcast',
          description: 'Podcast o inwestowaniu, ETF-ach, podatkach i długoterminowym podejściu.',
          content_type: 'audio',
          provider: 'Podcast',
          source_channel: 'Inwestomat',
          source_url: 'https://inwestomat.eu/podcast/',
          duration_minutes: 35,
          summary: 'Podcast pomaga osłuchać się z inwestowaniem bez robienia szybkich, impulsywnych ruchów.',
        },
      ],
    },
    {
      id: 203,
      title: 'Krypto i ekonomia bez pośpiechu',
      slug: 'krypto-ekonomia-bez-pospiechu',
      description: 'Polskie zasoby tekstowe o ryzyku, inflacji i podstawach decyzji finansowych.',
      category: 'economics',
      level: 'beginner',
      thumbnail_url: 'https://images.unsplash.com/photo-1621504450181-5d356f61d307?auto=format&fit=crop&w=900&q=80',
      lessons: [
        {
          id: 2006,
          key: 'cryptoSafety',
          title: 'Bezpieczeństwo i ryzyko w krypto',
          description: 'Krótka ścieżka tekstowa o ostrożnym podejściu do kryptowalut.',
          content_type: 'article',
          provider: 'Curated reading',
          source_channel: 'FinanU',
          source_url: 'https://inwestomat.eu/',
          duration_minutes: 10,
          summary: 'Najpierw trzeba rozumieć custody, zmienność i oszustwa, a dopiero potem podejmować decyzje.',
        },
        {
          id: 2007,
          key: 'economy',
          title: 'Inflacja i stopy procentowe',
          description: 'Tekstowy wstęp do tego, jak makroekonomia wpływa na budżet i inwestycje.',
          content_type: 'article',
          provider: 'Curated reading',
          source_channel: 'FinanU',
          source_url: 'https://www.nbp.pl/',
          duration_minutes: 12,
          summary: 'Inflacja i stopy procentowe wpływają na siłę nabywczą, kredyt, oszczędzanie i wyceny aktywów.',
        },
      ],
    },
  ],
};

export function getLearningCategories(language) {
  const labels = categoryCopy[language] || categoryCopy.en;

  return labels.map(([name, description], index) => ({
    id: index + 1,
    name,
    slug: ['personal-finance', 'investing', 'crypto', 'forex', 'economics'][index],
    description,
    icon: ['account_balance_wallet', 'trending_up', 'currency_bitcoin', 'candlestick_chart', 'account_balance'][index],
    order: index + 1,
    is_active: true,
  }));
}

export function getCourseTypes(language) {
  const names = typeCopy[language] || typeCopy.en;

  return names.map((name, index) => ({
    id: index + 1,
    name,
    slug: ['video', 'audio', 'article', 'course'][index],
    order: index + 1,
    is_active: true,
  }));
}

export function getLearningLevels(language) {
  const names = levelCopy[language] || levelCopy.en;

  return [
    { id: 1, name: names[0], slug: 'beginner', order: 1, is_active: true },
    { id: 2, name: names[1], slug: 'intermediate', order: 2, is_active: true },
    { id: 3, name: names[2], slug: 'advanced', order: 3, is_active: true },
  ];
}

function buildQuiz(lessonId, rows) {
  const questions = rows.map(([question, options, correctIndex], questionIndex) => ({
    id: `${lessonId}-${questionIndex + 1}`,
    question,
    explanation: 'Review the key idea in the lesson, then continue.',
    options: options.map((text, optionIndex) => ({
      id: `${lessonId}-${questionIndex + 1}-${optionIndex + 1}`,
      text,
      is_correct: optionIndex === correctIndex,
      order: optionIndex + 1,
    })),
  }));

  return {
    question: questions[0].question,
    explanation: questions[0].explanation,
    options: questions[0].options,
    questions,
  };
}

function hydrateCourse(course, language, categories, levels, order) {
  const quizSource = exams[language] || exams.en;
  const lessons = course.lessons.map((lesson, index) => ({
    ...lesson,
    slug: lesson.key.replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`),
    content_language: language,
    order: index + 1,
    is_active: true,
    quiz: buildQuiz(lesson.id, quizSource[lesson.key]),
  }));
  const primaryContentType = lessons[0]?.content_type || 'article';

  return {
    id: course.id,
    title: course.title,
    slug: course.slug,
    description: course.description,
    category: categories.find((category) => category.slug === course.category) || categories[0],
    course_type: { id: 1, name: primaryContentType, slug: primaryContentType, order: 1, is_active: true },
    level: levels.find((level) => level.slug === course.level) || levels[0],
    thumbnail_url: course.thumbnail_url,
    primary_content_type: primaryContentType,
    estimated_duration_minutes: lessons.reduce((total, lesson) => total + lesson.duration_minutes, 0),
    order,
    is_active: true,
    lessons,
  };
}

export function getCourses(language) {
  const resolvedLanguage = resources[language] ? language : 'en';
  const categories = getLearningCategories(resolvedLanguage);
  const levels = getLearningLevels(resolvedLanguage);

  return resources[resolvedLanguage].map((course, index) =>
    hydrateCourse(course, resolvedLanguage, categories, levels, index + 1)
  );
}
