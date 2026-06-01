export function getDashboardData(t) {
  return {
    featuredArticle: {
      category: t('dashboard.featuredCategory'),
      title: t('dashboard.marketPulse'),
      changeText: '+12.4%',
      changeLabel: t('dashboard.globalAgg'),
    },
    dailyFeed: [
      {
        id: 1,
        type: t('dashboard.cryptoAlert'),
        isNew: true,
        title: t('dashboard.solanaTitle'),
        description: t('dashboard.solanaDescription'),
        image:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuCfIbzTrIN9YOcxY76T6HZvV5wi0NDCbb9tZ__kf80hr-JnafQGVhl5SxowgPVStRgOrVdh605jz-SVenSooO6VArMDi3XsXGGUJisuDxcmID4Rfesd28w6jbuRYCYv2S8WrZWauZFXBXHrTIznK5foXk7s6KYHNKC2HECcRGTuAxxbgbh1JsRe5SaTO98P3raX8PvommhaJGrQcL9v1CqubW7_SJh0ytdWlboL5xDOigkTOtaNS-xRz-tqv228cqmeBCqGbRthkw59',
        icon: 'arrow_upward',
        iconBgClass: 'bg-primary/20',
        iconColorClass: 'text-primary',
        iconBorderClass: 'border-primary/40',
      },
      {
        id: 2,
        type: t('dashboard.forexAlert'),
        isNew: false,
        title: t('dashboard.eurUsdTitle'),
        description: t('dashboard.eurUsdDescription'),
        image:
          'https://lh3.googleusercontent.com/aida-public/AB6AXuByM9s5hTQSBip_Q_CXCzLw176JmcDXdPxnrVfA-T9YW91wAHJ5nzbFpoPP4cIVAsPn2AGnMOmlLmecf4NMX9RYW5cgwqMVhLjt54OBdneazpENj6lP7Yq2Q-_eMAWJJSuH4JdMT0THyzfkmNo2ytbJtc6R0TkkFe49lulWx1QKMhGSo0KTrIKn9Mc4myS0COKQPSkKvYKX2jbCC2ab7_lGpO8lQAHY42yBPuzrLn6vNXSj7ktEXTE_TLGGL5qDMiRu2TUmu2aXn0GS',
        icon: 'arrow_downward',
        iconBgClass: 'bg-error-container/20',
        iconColorClass: 'text-error',
        iconBorderClass: 'border-error-container/40',
      },
    ],
    microcourse: {
      title: t('dashboard.microcourseTitle'),
      duration: '< 10 min',
      progress: 0,
    },
  };
}
