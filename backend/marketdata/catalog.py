"""Shared product identities and comparable series for seeding and Gemini searches."""

PRODUCTS = [
    ("BTC", "Bitcoin", "Bitcoin", "CRYPTO", "COIN", "USD"),
    ("ETH", "Ethereum", "Ethereum", "CRYPTO", "COIN", "USD"),
    ("BNB", "BNB", "BNB", "CRYPTO", "COIN", "USD"),
    ("SOL", "Solana", "Solana", "CRYPTO", "COIN", "USD"),
    ("XRP", "XRP", "XRP", "CRYPTO", "COIN", "USD"),
    ("DOGE", "Dogecoin", "Dogecoin", "CRYPTO", "COIN", "USD"),
    ("ADA", "Cardano", "Cardano", "CRYPTO", "COIN", "USD"),
    ("WIG20", "WIG20", "WIG20", "INDEX", "STOCK_INDEX", "points"),
    ("WIG", "WIG", "WIG", "INDEX", "STOCK_INDEX", "points"),
    ("SP500", "S&P 500", "S&P 500", "INDEX", "STOCK_INDEX", "points"),
    ("NASDAQ100", "Nasdaq 100", "Nasdaq 100", "INDEX", "STOCK_INDEX", "points"),
    ("MSCI_WORLD", "MSCI World", "MSCI World", "INDEX", "STOCK_INDEX", "points"),
    ("MSCI_EM", "MSCI Emerging Markets", "MSCI Emerging Markets", "INDEX", "STOCK_INDEX", "points"),
    ("STOXX600", "STOXX Europe 600", "STOXX Europe 600", "INDEX", "STOCK_INDEX", "points"),
    ("EUROSTOXX50", "EURO STOXX 50", "EURO STOXX 50", "INDEX", "STOCK_INDEX", "points"),
    ("EURUSD", "EUR/USD", "EUR/USD", "FOREX", "FX_PAIR", "USD"),
    ("USDPLN", "USD/PLN", "USD/PLN", "FOREX", "FX_PAIR", "PLN"),
    ("EURPLN", "EUR/PLN", "EUR/PLN", "FOREX", "FX_PAIR", "PLN"),
    ("GBPUSD", "GBP/USD", "GBP/USD", "FOREX", "FX_PAIR", "USD"),
    ("USDJPY", "USD/JPY", "USD/JPY", "FOREX", "FX_PAIR", "JPY"),
    ("GOLD", "Gold", "Złoto", "FOREX", "METAL", "USD/oz"),
    ("BRENT", "Brent Oil", "Ropa Brent", "FOREX", "COMMODITY", "USD/bbl"),
    ("PL_CPI", "Poland CPI Inflation (YoY)", "Inflacja CPI w Polsce (r/r)", "GENERAL", "INFLATION", "%"),
    ("PL_NBP_RATE", "NBP Reference Rate", "Stopa referencyjna NBP", "GENERAL", "RATE", "%"),
    ("PL_GDP", "Poland Real GDP Growth (YoY)", "Realny wzrost PKB Polski (r/r)", "GENERAL", "GDP", "%"),
    ("PL_UNEMPLOYMENT", "Poland Registered Unemployment", "Stopa bezrobocia rejestrowanego w Polsce", "GENERAL", "UNEMPLOYMENT", "%"),
    ("PL_HPI", "Poland Housing Price Index", "Indeks cen mieszkań w Polsce", "GENERAL", "HOUSING", "points"),
    ("PL_10Y_BOND", "Poland 10Y Bond Yield", "Rentowność 10-letnich obligacji Polski", "GENERAL", "BOND", "%"),
    ("PL_DE_RISK_PREMIUM", "Poland vs Germany 10Y Yield Spread", "Spread rentowności obligacji 10-letnich Polski i Niemiec", "GENERAL", "RISK_PREMIUM", "bps"),
    ("EZ_CPI", "Eurozone HICP Inflation (YoY)", "Inflacja HICP w strefie euro (r/r)", "GENERAL", "INFLATION", "%"),
    ("FED_RATE", "Fed Target Rate (Upper Bound)", "Górna granica przedziału stopy Fed", "GENERAL", "RATE", "%"),
    ("ECB_RATE", "ECB Main Refinancing Rate", "Stopa podstawowych operacji refinansujących EBC", "GENERAL", "RATE", "%"),
]

DEFAULT_SYMBOLS = tuple(product[0] for product in PRODUCTS)

# Values and previous values must use the same series, unit and index base.
SERIES_DEFINITIONS = {
    symbol: f"{name}, spot price in USD per coin; compare with 24 hours earlier from the same provider."
    for symbol, name, _, category, _, _ in PRODUCTS if category == "CRYPTO"
}
SERIES_DEFINITIONS.update({
    symbol: f"{name}, {unit} per 1 {symbol[:3]}; compare with the previous daily close from the same provider."
    for symbol, name, _, _, subcategory, unit in PRODUCTS if subcategory == "FX_PAIR"
})
SERIES_DEFINITIONS.update({
    "WIG20": "GPW WIG20 index level in points, PLN variant; compare with previous trading close.",
    "WIG": "GPW WIG index level in points; compare with previous trading close.",
    "SP500": "S&P 500 price index level in points, USD variant; compare with previous trading close.",
    "NASDAQ100": "Nasdaq-100 price index (NDX) level in points, USD variant; compare with previous trading close.",
    "MSCI_WORLD": "MSCI World price index level in points, USD variant; compare with previous trading close. Not an ETF, net-return or gross-return index.",
    "MSCI_EM": "MSCI Emerging Markets price index level in points, USD variant; compare with previous trading close. Not an ETF, net-return or gross-return index.",
    "STOXX600": "STOXX Europe 600 price index level in points, EUR variant; compare with previous trading close.",
    "EUROSTOXX50": "EURO STOXX 50 price index level in points, EUR variant; compare with previous trading close.",
    "GOLD": "Gold spot price in USD per troy ounce; compare with previous daily close from the same provider.",
    "BRENT": "Brent crude price in USD per barrel; compare with previous daily close for the same benchmark and contract. Identify the benchmark/contract in src.",
    "PL_CPI": "GUS/Statistics Poland national all-items CPI annual inflation rate in percent (YoY), not HICP or monthly growth; t is the reference month, pv is the preceding month's YoY rate.",
    "PL_NBP_RATE": "NBP reference interest rate in percent, not deposit or lombard rate; t is the date the rate took effect, pv is the preceding policy setting with its effective date.",
    "PL_GDP": "GUS/Statistics Poland real GDP annual growth in percent (YoY, unadjusted), not nominal or quarter-on-quarter growth; t is the reference quarter, pv is the preceding quarter's YoY rate.",
    "PL_UNEMPLOYMENT": "GUS/Statistics Poland registered unemployment rate in percent, not the ILO/LFS/Eurostat harmonised rate; t is the reference month, pv is the preceding month's rate.",
    "PL_HPI": "GUS/Statistics Poland or Eurostat quarterly house price index for Poland, all dwellings, fixed base 2015=100. Use the index LEVEL and quarter, not growth percentages or an index with previous quarter/year=100. Eurostat prc_hpi_q: geo=PL, purchase=TOTAL, unit=I15. Do not mix with the rebased 2025=100 series; return null if 2015=100 cannot be verified. pv is the preceding quarter on the same base.",
    "PL_10Y_BOND": "Poland benchmark 10-year government bond yield in percent; compare with previous trading close, not bond price or a monthly average.",
    "PL_DE_RISK_PREMIUM": "Poland minus Germany 10-year government bond yield spread in basis points. Compute (PL yield percent minus DE yield percent)*100 only from verified yields for the same date and comparable benchmarks; compare with the preceding trading day's spread. Not CDS or a percentage value.",
    "EZ_CPI": "Eurostat euro-area all-items HICP annual inflation in percent (YoY), not the index level or monthly growth; t is the reference month, pv is the preceding month's YoY rate.",
    "FED_RATE": "Federal Reserve federal funds TARGET RANGE UPPER LIMIT in percent (FRED DFEDTARU, https://fred.stlouisfed.org/series/DFEDTARU), not the effective rate, midpoint or lower limit. Use the effective date of the policy setting; pv is the preceding policy setting and its effective date.",
    "ECB_RATE": "ECB main refinancing operations fixed tender rate (MRO) in percent (https://www.ecb.europa.eu/stats/policy_and_exchange_rates/key_ecb_interest_rates/html/index.en.html), not the deposit facility or marginal lending rate. Use the effective date; pv is the preceding policy setting and its effective date.",
})
