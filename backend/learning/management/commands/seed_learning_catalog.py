import re

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils.text import slugify

from learning.models import (
    Course,
    CourseType,
    LearningCategory,
    LearningLevel,
    Lesson,
    LessonQuiz,
    LessonQuizOption,
    LessonQuizQuestion,
)


EN_DISCLAIMER = "This content is for educational purposes only and does not constitute financial advice."
PL_DISCLAIMER = "Tresc ma charakter edukacyjny i nie stanowi porady finansowej."

RISK_CATEGORIES = {"crypto", "forex", "investing"}
COMMERCIAL_PROVIDERS = {"Binance Academy", "Coinbase Learn", "Binance Academy PL"}

INACTIVE_RESOURCE_URLS = {
    # Generic crypto library pages are less useful than structured tracks/courses.
    "https://www.binance.com/en/academy",
    "https://www.coinbase.com/en-es/learn",
    "https://www.binance.com/pl/academy",
    # Channel/feed URLs should be replaced with specific lessons before activation.
    "https://www.youtube.com/@NBPpl",
    "https://www.youtube.com/channel/UCe8VykA_qDCBmg_08eIA8iQ",
    "https://jakoszczedzacpieniadze.pl/feed/podcast",
    # Trading-oriented source; keep inactive until curated to strictly educational videos.
    "https://www.youtube.com/user/forexclubpl",
}

RESOURCE_ORDER_OVERRIDES = {
    # English path: personal finance -> economics -> investing -> advanced -> crypto/forex.
    "https://www.open.edu/openlearn/money-management/free-courses": 2,
    "https://www.khanacademy.org/economics-finance-domain": 3,
    "https://www.khanacademy.org/economics-finance-domain/core-finance": 4,
    "https://www.investopedia.com/terms/e/etf.asp": 5,
    "https://www.open.edu/openlearn/money-business/managing-my-investments": 6,
    "https://www.binance.com/en/academy/courses": 7,
    "https://www.coinbase.com/learn/tips-and-tutorials": 8,
    "https://www.babypips.com/learn/forex": 9,
    "https://www.investopedia.com/the-investopedia-express-podcast-5215636": 10,
    "https://online.yale.edu/courses/financial-markets": 11,
    "https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/": 12,
    # Polish path: personal finance -> consumer safety -> economics -> investing -> crypto.
    "https://marciniwuc.com/": 2,
    "https://podcasts.apple.com/pl/podcast/finanse-bardzo-osobiste-oszcz%C4%99dzanie-inwestowanie-pieni%C4%85dze/id946719109": 3,
    "https://finanse.uokik.gov.pl/category/kredyty-konsumenckie/": 4,
    "https://www.knf.gov.pl/edukacja_finansowa": 5,
    "https://www.knf.gov.pl/co_robimy/publikacje_edukacyjne": 6,
    "https://nbp.pl/edukacja/": 7,
    "https://nbp.pl/edukacja/zasoby-edukacyjne/": 8,
    "https://www.gpw.pl/szkola-gieldowa": 9,
    "https://www.gpw.pl/fundacja-gpw-platforma-edukacyjna": 10,
    "https://kursnagielde.pl/filmy-edukacyjne/": 12,
    "https://www.knf.gov.pl/co_robimy/edukacja_finansowa/seminaria_cedur": 13,
    "https://www.obserwatorfinansowy.pl/": 14,
    "https://open.spotify.com/show/2nXC3fQO7P09vD1gUkqSYe": 15,
    "https://www.binance.com/pl/academy/start-here": 16,
    "https://www.binance.com/pl/academy/track/beginner-track": 17,
}

CATEGORY_IMAGE_URLS = {
    "personal-finance": "/learning/course-money-habits.png",
    "investing": "/learning/course-investing-foundations.png",
    "economics": "/learning/lesson-economics-podcast.png",
    "crypto": "/learning/course-crypto-forex-risk.png",
    "forex": "/learning/course-crypto-forex-risk.png",
}


def course_cover_path(language, order, title):
    raw = f"{language}-{order:02d}-{title.lower()}"
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")[:96]
    return f"/learning/course-covers/{slug}.svg"


def lesson_cover_path(language, course_order, course_id, lesson_order, title):
    raw = f"{language}-{course_order:02d}-{course_id}-{lesson_order:02d}-{title.lower()}"
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")[:110]
    return f"/learning/lesson-covers/{slug}.svg"

TAXONOMY = {
    "categories": [
        ("personal-finance", "Personal Finance", "Budgeting, saving, debt and everyday money habits.", "account_balance_wallet"),
        ("investing", "Investing", "ETFs, diversification, risk and long-term compounding.", "trending_up"),
        ("crypto", "Crypto", "Bitcoin, wallets, security and volatility risk.", "currency_bitcoin"),
        ("forex", "Forex", "Currency pairs, leverage, pips and risk management.", "candlestick_chart"),
        ("economics", "Economics", "Inflation, interest rates and central-bank decisions.", "account_balance"),
    ],
    "levels": [
        ("beginner", "Basic"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ],
    "types": [
        ("video", "Video"),
        ("audio", "Audio"),
        ("article", "Article"),
        ("course", "Course"),
        ("podcast", "Podcast"),
        ("tool", "Tool"),
        ("glossary", "Glossary"),
    ],
}

RESOURCES = [
    {
        "language": "en",
        "title": "Khan Academy Finance and Capital Markets",
        "provider": "Khan Academy",
        "source_type": "institutional",
        "url": "https://www.khanacademy.org/economics-finance-domain/core-finance",
        "format": "course",
        "level": "beginner",
        "category": "investing",
        "duration": 45,
        "description": "Free structured lessons on interest, debt, bonds, stocks, cash flow and capital markets.",
    },
    {
        "language": "en",
        "title": "Khan Academy Economics",
        "provider": "Khan Academy",
        "source_type": "institutional",
        "url": "https://www.khanacademy.org/economics-finance-domain",
        "format": "course",
        "level": "beginner",
        "category": "economics",
        "duration": 45,
        "description": "Free lessons for microeconomics, macroeconomics, inflation, unemployment and central banks.",
    },
    {
        "language": "en",
        "title": "Yale Financial Markets",
        "provider": "Yale Online",
        "source_type": "university",
        "url": "https://online.yale.edu/courses/financial-markets",
        "format": "course",
        "level": "intermediate",
        "category": "investing",
        "duration": 60,
        "description": "University course by Robert Shiller on financial markets, risk and behavioral finance.",
    },
    {
        "language": "en",
        "title": "MIT Finance Theory I",
        "provider": "MIT OpenCourseWare",
        "source_type": "university",
        "url": "https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/",
        "format": "course",
        "level": "advanced",
        "category": "investing",
        "duration": 75,
        "description": "Advanced open course on asset valuation, fixed income, equities, diversification and derivatives.",
    },
    {
        "language": "en",
        "title": "OpenLearn Managing My Investments",
        "provider": "OpenLearn",
        "source_type": "institutional",
        "url": "https://www.open.edu/openlearn/money-business/managing-my-investments",
        "format": "course",
        "level": "beginner",
        "category": "investing",
        "duration": 40,
        "description": "Practical free course on investment products, risk, historical returns and behavior.",
    },
    {
        "language": "en",
        "title": "OpenLearn Money and Business Free Courses",
        "provider": "OpenLearn",
        "source_type": "institutional",
        "url": "https://www.open.edu/openlearn/money-management/free-courses",
        "format": "course",
        "level": "beginner",
        "category": "personal-finance",
        "duration": 35,
        "description": "Free courses on saving, retirement, financial planning and financial wellbeing.",
    },
    {
        "language": "en",
        "title": "Binance Academy",
        "provider": "Binance Academy",
        "source_type": "commercial_platform",
        "url": "https://www.binance.com/en/academy",
        "format": "article",
        "level": "beginner",
        "category": "crypto",
        "duration": 25,
        "description": "Educational crypto library covering blockchain, Bitcoin, Ethereum, DeFi, Web3 and security.",
    },
    {
        "language": "en",
        "title": "Binance Academy Courses",
        "provider": "Binance Academy",
        "source_type": "commercial_platform",
        "url": "https://www.binance.com/en/academy/courses",
        "format": "course",
        "level": "beginner",
        "category": "crypto",
        "duration": 35,
        "description": "Structured crypto courses on blockchain, DeFi, NFTs and Web3 concepts.",
    },
    {
        "language": "en",
        "title": "Coinbase Learn",
        "provider": "Coinbase Learn",
        "source_type": "commercial_platform",
        "url": "https://www.coinbase.com/en-es/learn",
        "format": "article",
        "level": "beginner",
        "category": "crypto",
        "duration": 20,
        "description": "Beginner-friendly articles about Bitcoin, Ethereum, wallets, ETFs, security and market basics.",
    },
    {
        "language": "en",
        "title": "Coinbase Learn Tips and Tutorials",
        "provider": "Coinbase Learn",
        "source_type": "commercial_platform",
        "url": "https://www.coinbase.com/learn/tips-and-tutorials",
        "format": "article",
        "level": "beginner",
        "category": "crypto",
        "duration": 20,
        "description": "Practical tutorials on wallets, sending crypto, candlesticks, ROI and market concepts.",
    },
    {
        "language": "en",
        "title": "BabyPips School of Pipsology",
        "provider": "BabyPips",
        "source_type": "independent_creator",
        "url": "https://www.babypips.com/learn/forex",
        "format": "course",
        "level": "beginner",
        "category": "forex",
        "duration": 45,
        "description": "Free and well-known Forex school with lessons and quizzes for beginners.",
    },
    {
        "language": "en",
        "title": "Investopedia Express",
        "provider": "Investopedia",
        "source_type": "media",
        "url": "https://www.investopedia.com/the-investopedia-express-podcast-5215636",
        "format": "podcast",
        "level": "intermediate",
        "category": "economics",
        "duration": 25,
        "description": "Podcast for understanding market context, economics and investing ideas.",
    },
    {
        "language": "pl",
        "title": "NBP Edukacja",
        "provider": "Narodowy Bank Polski",
        "source_type": "institutional",
        "url": "https://nbp.pl/edukacja/",
        "format": "article",
        "level": "beginner",
        "category": "economics",
        "duration": 25,
        "description": "Oficjalny portal edukacyjny banku centralnego o ekonomii, inflacji i finansach.",
    },
    {
        "language": "pl",
        "title": "NBP Otwarte zasoby edukacyjne",
        "provider": "Narodowy Bank Polski",
        "source_type": "institutional",
        "url": "https://nbp.pl/edukacja/zasoby-edukacyjne/",
        "format": "tool",
        "level": "beginner",
        "category": "economics",
        "duration": 20,
        "description": "Otwarte materialy, animacje i gry edukacyjne o ekonomii oraz finansach.",
    },
    {
        "language": "pl",
        "title": "Narodowy Bank Polski YouTube",
        "provider": "Narodowy Bank Polski",
        "source_type": "institutional",
        "url": "https://www.youtube.com/@NBPpl",
        "format": "video",
        "level": "beginner",
        "category": "economics",
        "duration": 20,
        "description": "Oficjalny kanal banku centralnego z materialami edukacyjnymi i instytucjonalnymi.",
    },
    {
        "language": "pl",
        "title": "GPW Szkola Gieldowa",
        "provider": "GPW",
        "source_type": "institutional",
        "url": "https://www.gpw.pl/szkola-gieldowa",
        "format": "course",
        "level": "beginner",
        "category": "investing",
        "duration": 35,
        "description": "Program edukacji gieldowej Warszawskiej Gieldy Papierow Wartosciowych.",
    },
    {
        "language": "pl",
        "title": "GPW Kurs na gielde",
        "provider": "Fundacja GPW",
        "source_type": "institutional",
        "url": "https://www.gpw.pl/fundacja-gpw-platforma-edukacyjna",
        "format": "course",
        "level": "beginner",
        "category": "investing",
        "duration": 35,
        "description": "Platforma edukacyjna z kursami, testami i tresciami o akcjach, ETF-ach oraz obligacjach.",
    },
    {
        "language": "pl",
        "title": "Fundacja GPW Filmy edukacyjne",
        "provider": "Fundacja GPW",
        "source_type": "institutional",
        "url": "https://kursnagielde.pl/filmy-edukacyjne/",
        "format": "video",
        "level": "intermediate",
        "category": "investing",
        "duration": 25,
        "description": "Filmy i podcasty o akcjach, obligacjach, ETF-ach, portfelu i psychologii inwestowania.",
    },
    {
        "language": "pl",
        "title": "KNF Edukacja finansowa CEDUR",
        "provider": "KNF",
        "source_type": "institutional",
        "url": "https://www.knf.gov.pl/edukacja_finansowa",
        "format": "article",
        "level": "beginner",
        "category": "personal-finance",
        "duration": 25,
        "description": "Instytucjonalne zasoby o bezpieczenstwie finansowym, regulacji i ochronie konsumenta.",
    },
    {
        "language": "pl",
        "title": "KNF Publikacje edukacyjne",
        "provider": "KNF",
        "source_type": "institutional",
        "url": "https://www.knf.gov.pl/co_robimy/publikacje_edukacyjne",
        "format": "article",
        "level": "beginner",
        "category": "personal-finance",
        "duration": 25,
        "description": "Publikacje o oszustwach, ryzykach, ochronie uzytkownika i rynkach finansowych.",
    },
    {
        "language": "pl",
        "title": "KNF Seminaria CEDUR",
        "provider": "KNF",
        "source_type": "institutional",
        "url": "https://www.knf.gov.pl/co_robimy/edukacja_finansowa/seminaria_cedur",
        "format": "course",
        "level": "intermediate",
        "category": "economics",
        "duration": 30,
        "description": "Bezpłatne seminaria online o rynku finansowym, regulacji i ochronie konsumentow.",
    },
    {
        "language": "pl",
        "title": "UOKiK Finanse",
        "provider": "UOKiK",
        "source_type": "institutional",
        "url": "https://finanse.uokik.gov.pl/category/kredyty-konsumenckie/",
        "format": "tool",
        "level": "beginner",
        "category": "personal-finance",
        "duration": 20,
        "description": "Zasoby o kredycie konsumenckim, hipotekach, prawach konsumenta i codziennych finansach.",
    },
    {
        "language": "pl",
        "title": "Obserwator Finansowy",
        "provider": "Obserwator Finansowy",
        "source_type": "media",
        "url": "https://www.obserwatorfinansowy.pl/",
        "format": "article",
        "level": "intermediate",
        "category": "economics",
        "duration": 25,
        "description": "Analizy ekonomiczne i finansowe o Polsce, Europie, bankach i makroekonomii.",
    },
    {
        "language": "pl",
        "title": "Obserwator Finansowy Podcast",
        "provider": "Obserwator Finansowy",
        "source_type": "media",
        "url": "https://open.spotify.com/show/2nXC3fQO7P09vD1gUkqSYe",
        "format": "podcast",
        "level": "intermediate",
        "category": "economics",
        "duration": 25,
        "description": "Podcast o ekonomii, bankowosci, Unii Europejskiej, systemie finansowym i analizie makro.",
    },
    {
        "language": "pl",
        "title": "Binance Academy PL",
        "provider": "Binance Academy PL",
        "source_type": "commercial_platform",
        "url": "https://www.binance.com/pl/academy",
        "format": "article",
        "level": "beginner",
        "category": "crypto",
        "duration": 25,
        "description": "Polska biblioteka edukacyjna o blockchainie, Bitcoinie, Ethereum, DeFi i Web3.",
    },
    {
        "language": "pl",
        "title": "Binance Academy PL Start Here",
        "provider": "Binance Academy PL",
        "source_type": "commercial_platform",
        "url": "https://www.binance.com/pl/academy/start-here",
        "format": "course",
        "level": "beginner",
        "category": "crypto",
        "duration": 25,
        "description": "Sciezka startowa dla osob zaczynajacych edukacje o kryptowalutach od podstaw.",
    },
    {
        "language": "pl",
        "title": "Binance Academy PL Beginner Track",
        "provider": "Binance Academy PL",
        "source_type": "commercial_platform",
        "url": "https://www.binance.com/pl/academy/track/beginner-track",
        "format": "course",
        "level": "beginner",
        "category": "crypto",
        "duration": 35,
        "description": "Kurs dla poczatkujacych o blockchainie, kryptowalutach, DeFi i Web3.",
    },
    {
        "language": "pl",
        "title": "Marcin Iwuc Finanse Bardzo Osobiste",
        "provider": "Marcin Iwuc",
        "source_type": "independent_creator",
        "url": "https://marciniwuc.com/",
        "format": "article",
        "level": "beginner",
        "category": "personal-finance",
        "duration": 25,
        "description": "Niezalezny blog i podcast o finansach osobistych, oszczedzaniu oraz inwestowaniu.",
    },
    {
        "language": "pl",
        "title": "Marcin Iwuc YouTube",
        "provider": "Marcin Iwuc",
        "source_type": "independent_creator",
        "url": "https://www.youtube.com/channel/UCe8VykA_qDCBmg_08eIA8iQ",
        "format": "video",
        "level": "beginner",
        "category": "personal-finance",
        "duration": 25,
        "description": "Kanal o oszczedzaniu, inwestowaniu, podatkach i planowaniu finansowym.",
    },
    {
        "language": "pl",
        "title": "Finanse Bardzo Osobiste Apple Podcasts",
        "provider": "Marcin Iwuc",
        "source_type": "independent_creator",
        "url": "https://podcasts.apple.com/pl/podcast/finanse-bardzo-osobiste-oszcz%C4%99dzanie-inwestowanie-pieni%C4%85dze/id946719109",
        "format": "podcast",
        "level": "beginner",
        "category": "personal-finance",
        "duration": 25,
        "description": "Podcast o oszczedzaniu, inwestowaniu, pieniadzach i nawykach finansowych.",
    },
    {
        "language": "pl",
        "title": "WNOP Wiecej niz oszczedzanie pieniedzy",
        "provider": "WNOP",
        "source_type": "independent_creator",
        "url": "https://jakoszczedzacpieniadze.pl/feed/podcast",
        "format": "podcast",
        "level": "beginner",
        "category": "personal-finance",
        "duration": 25,
        "description": "Klasyczny polski podcast o oszczedzaniu, zarzadzaniu pieniedzmi i finansach osobistych.",
    },
    {
        "language": "pl",
        "title": "Forex Club PL YouTube",
        "provider": "Forex Club PL",
        "source_type": "independent_creator",
        "url": "https://www.youtube.com/user/forexclubpl",
        "format": "video",
        "level": "intermediate",
        "category": "forex",
        "duration": 25,
        "description": "Kanal o Forex, tradingu i rynkach; uzywany w FinanU wylacznie edukacyjnie.",
    },
]


QUIZ_TEMPLATES = {
    "en": {
        "personal-finance": [
            ("What is the best way to use a personal finance lesson?", ["Apply one idea to your own plan.", "Treat it as a guaranteed result.", "Ignore your current budget."], 0),
            ("Why compare costs, risks and goals?", ["They shape better financial decisions.", "They remove all uncertainty.", "They make advice unnecessary."], 0),
            ("What should a learner do before acting?", ["Check context and personal fit.", "Copy every example immediately.", "Borrow more to move faster."], 0),
        ],
        "investing": [
            ("What should guide an investing decision?", ["Goal, risk and time horizon.", "A single headline.", "A guaranteed profit claim."], 0),
            ("Why does diversification matter?", ["It spreads exposure across assets.", "It removes every possible loss.", "It predicts tomorrow's price."], 0),
            ("How should investing content be treated?", ["As education, not personal advice.", "As a trading signal.", "As a promise of returns."], 0),
        ],
        "crypto": [
            ("What is a safe first step in crypto learning?", ["Understand risks and custody.", "Share your seed phrase.", "Assume prices only rise."], 0),
            ("Why are commercial crypto sources flagged?", ["They may have business incentives.", "They are always wrong.", "They replace independent judgement."], 0),
            ("What should crypto education avoid?", ["Investment recommendations or signals.", "Security basics.", "Risk explanations."], 0),
        ],
        "forex": [
            ("Why is leverage important in Forex education?", ["It can magnify gains and losses.", "It guarantees profits.", "It removes market risk."], 0),
            ("What is a responsible Forex learning goal?", ["Understand mechanics and risk first.", "Win every trade.", "Copy signals blindly."], 0),
            ("How should trading content be framed?", ["As education, not advice.", "As a guaranteed strategy.", "As a shortcut around risk."], 0),
        ],
        "economics": [
            ("Why learn economics in a finance app?", ["It improves context for decisions.", "It predicts every market move.", "It removes budgeting needs."], 0),
            ("What do inflation and rates affect?", ["Purchasing power, credit and saving.", "Only professional traders.", "Nothing in daily life."], 0),
            ("What is a good learning habit?", ["Connect concepts to real decisions.", "Memorize terms without context.", "Ignore uncertainty."], 0),
        ],
    },
    "pl": {
        "personal-finance": [
            ("Jak najlepiej wykorzystac lekcje o finansach osobistych?", ["Wdrozyc jedna rzecz we wlasnym planie.", "Traktowac ja jako gwarancje wyniku.", "Zignorowac domowy budzet."], 0),
            ("Dlaczego warto porownywac koszty, ryzyko i cele?", ["Pomaga to podejmowac lepsze decyzje.", "Usuwa cala niepewnosc.", "Zastepuje samodzielne myslenie."], 0),
            ("Co zrobic przed decyzja finansowa?", ["Sprawdzic kontekst i dopasowanie.", "Kopiowac kazdy przyklad.", "Pozyczyc wiecej pieniedzy."], 0),
        ],
        "investing": [
            ("Co powinno kierowac decyzja inwestycyjna?", ["Cel, ryzyko i horyzont.", "Pojedynczy naglowek.", "Obietnica zysku."], 0),
            ("Po co dywersyfikacja?", ["Rozklada ekspozycje na rozne aktywa.", "Usuwa kazda strate.", "Przewiduje jutrzejsza cene."], 0),
            ("Jak traktowac tresci inwestycyjne?", ["Jako edukacje, nie porade osobista.", "Jako sygnal tradingowy.", "Jako gwarancje zwrotu."], 0),
        ],
        "crypto": [
            ("Jaki jest bezpieczny pierwszy krok w krypto?", ["Zrozumiec ryzyka i przechowywanie kluczy.", "Udostepnic seed phrase.", "Zakladac tylko wzrosty cen."], 0),
            ("Dlaczego oznaczamy komercyjne zrodla krypto?", ["Moga miec interes biznesowy.", "Zawsze sa bledne.", "Zastepuja ocene uzytkownika."], 0),
            ("Czego powinna unikac edukacja krypto?", ["Rekomendacji inwestycyjnych i sygnalow.", "Podstaw bezpieczenstwa.", "Wyjasniania ryzyka."], 0),
        ],
        "forex": [
            ("Dlaczego dzwignia jest wazna w Forex?", ["Moze zwiekszac zyski i straty.", "Gwarantuje zyski.", "Usuwa ryzyko rynku."], 0),
            ("Jaki jest odpowiedzialny cel nauki Forex?", ["Najpierw zrozumiec mechanike i ryzyko.", "Wygrywac kazda transakcje.", "Kopiowac sygnaly bez analizy."], 0),
            ("Jak traktowac tresci tradingowe?", ["Jako edukacje, nie porade.", "Jako gwarantowana strategie.", "Jako skrot bez ryzyka."], 0),
        ],
        "economics": [
            ("Po co uczyc sie ekonomii w aplikacji finansowej?", ["Daje kontekst do decyzji.", "Przewiduje kazdy ruch rynku.", "Usuwa potrzebe budzetu."], 0),
            ("Na co wplywaja inflacja i stopy?", ["Sile nabywcza, kredyt i oszczedzanie.", "Tylko zawodowych traderow.", "Na nic w codziennym zyciu."], 0),
            ("Jaki jest dobry nawyk nauki?", ["Laczyc pojecia z decyzjami.", "Zapamietywac terminy bez kontekstu.", "Ignorowac niepewnosc."], 0),
        ],
    },
}


def stable_slug(*parts):
    return slugify(" ".join(part for part in parts if part))[:190]


def get_disclaimer(resource):
    if resource["category"] in RISK_CATEGORIES or resource["provider"] in COMMERCIAL_PROVIDERS:
        return PL_DISCLAIMER if resource["language"] == "pl" else EN_DISCLAIMER
    return ""


def lesson_title(resource):
    return "Start here" if resource["language"] == "en" else "Zacznij tutaj"


def quiz_for(resource):
    return QUIZ_TEMPLATES[resource["language"]][resource["category"]]


class Command(BaseCommand):
    help = "Seeds the external learning catalog without deleting existing content or user progress."

    def handle(self, *args, **options):
        with transaction.atomic():
            categories = self.seed_categories()
            levels = self.seed_levels()
            types = self.seed_types()
            course_count, lesson_count = self.seed_resources(categories, levels, types)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded learning catalog: {course_count} courses, {lesson_count} lessons."
            )
        )

    def seed_categories(self):
        categories = {}
        for order, (slug, name, description, icon) in enumerate(TAXONOMY["categories"], start=1):
            category, _ = LearningCategory.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": description,
                    "icon": icon,
                    "order": order,
                    "is_active": True,
                },
            )
            categories[slug] = category
        return categories

    def seed_levels(self):
        levels = {}
        for order, (slug, name) in enumerate(TAXONOMY["levels"], start=1):
            level, _ = LearningLevel.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "order": order, "is_active": True},
            )
            levels[slug] = level
        return levels

    def seed_types(self):
        types = {}
        for order, (slug, name) in enumerate(TAXONOMY["types"], start=1):
            course_type, _ = CourseType.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": f"{name} learning resource.",
                    "order": order,
                    "is_active": True,
                },
            )
            types[slug] = course_type
        return types

    def seed_resources(self, categories, levels, types):
        course_count = 0
        lesson_count = 0

        for order, resource in enumerate(RESOURCES, start=1):
            category = categories[resource["category"]]
            level = levels[resource["level"]]
            course_type = types[resource["format"]]
            disclaimer = get_disclaimer(resource)
            course_slug = stable_slug(resource["language"], resource["provider"], resource["title"])
            course_order = RESOURCE_ORDER_OVERRIDES.get(resource["url"], order)
            course_image_url = course_cover_path(
                resource["language"],
                course_order,
                resource["title"],
            )

            course = self.find_course(resource, course_slug)
            if not course:
                course = Course(slug=course_slug)

            course.title = resource["title"]
            course.description = resource["description"]
            course.provider = resource["provider"]
            course.source_type = resource["source_type"]
            course.external_url = resource["url"]
            course.language = resource["language"]
            course.category = category
            course.course_type = course_type
            course.level = level
            course.thumbnail_url = course_image_url
            course.cover_image_url = course_image_url
            course.estimated_duration_minutes = resource["duration"]
            course.order = course_order
            course.is_required = True
            course.is_active = resource["url"] not in INACTIVE_RESOURCE_URLS
            course.save()
            course_count += 1

            lesson_slug = stable_slug("intro", resource["provider"], resource["title"])
            lesson = self.find_lesson(course, resource, lesson_slug)
            if not lesson:
                lesson = Lesson(course=course, slug=lesson_slug)
            lesson_image_url = lesson_cover_path(
                resource["language"],
                course_order,
                course.id,
                1,
                lesson_title(resource),
            )

            lesson.course = course
            lesson.title = lesson_title(resource)
            lesson.description = resource["description"]
            lesson.content_type = resource["format"]
            lesson.provider = resource["provider"]
            lesson.source_channel = resource["provider"]
            lesson.source_url = resource["url"]
            lesson.external_url = resource["url"]
            lesson.image_url = lesson_image_url
            lesson.content_language = resource["language"]
            lesson.level = level
            lesson.category = category
            lesson.duration_minutes = resource["duration"]
            lesson.summary = self.summary_for(resource, disclaimer)
            lesson.embed_allowed = "manual_review"
            lesson.requires_disclaimer = bool(disclaimer)
            lesson.disclaimer = disclaimer
            lesson.order = 1
            lesson.is_active = resource["url"] not in INACTIVE_RESOURCE_URLS
            lesson.save()
            lesson_count += 1

            self.seed_quiz(lesson, resource)

        return course_count, lesson_count

    def find_course(self, resource, slug):
        return (
            Course.objects.filter(
                Q(external_url=resource["url"])
                | Q(slug=slug)
                | Q(title=resource["title"], provider=resource["provider"])
            )
            .order_by("id")
            .first()
        )

    def find_lesson(self, course, resource, slug):
        return (
            Lesson.objects.filter(
                Q(source_url=resource["url"])
                | Q(external_url=resource["url"])
                | Q(course=course, slug=slug)
                | Q(course=course, title=lesson_title(resource), provider=resource["provider"])
            )
            .order_by("id")
            .first()
        )

    def summary_for(self, resource, disclaimer):
        if resource["language"] == "pl":
            summary = (
                f"Material startowy: {resource['description']} "
                "Przejrzyj zrodlo, zanotuj glowne pojecia i odpowiedz na quiz."
            )
        else:
            summary = (
                f"Starter lesson: {resource['description']} "
                "Open the external source, note the core concepts and complete the quiz."
            )
        return f"{summary} {disclaimer}".strip()

    def seed_quiz(self, lesson, resource):
        questions = quiz_for(resource)
        quiz, _ = LessonQuiz.objects.update_or_create(
            lesson=lesson,
            defaults={
                "title": f"Quiz: {lesson.title}",
                "description": "Required knowledge check for this external lesson.",
                "question": questions[0][0],
                "explanation": "Review the educational resource, then continue.",
                "passing_score": 100,
                "is_required": True,
                "is_active": True,
            },
        )

        for question_order, (question_text, options, correct_index) in enumerate(questions, start=1):
            question, _ = LessonQuizQuestion.objects.update_or_create(
                quiz=quiz,
                order=question_order,
                defaults={
                    "question": question_text,
                    "question_type": "single_choice",
                    "explanation": "The correct answer reinforces the main educational takeaway.",
                    "is_active": True,
                },
            )

            for option_order, option_text in enumerate(options, start=1):
                LessonQuizOption.objects.update_or_create(
                    quiz=quiz,
                    question=question,
                    order=option_order,
                    defaults={
                        "text": option_text,
                        "is_correct": option_order - 1 == correct_index,
                    },
                )
