from django.core.management.base import BaseCommand
from django.utils.text import slugify

from marketdata.models import FinancialProduct


PRODUCTS = [
    ("BTC", "Bitcoin", "Bitcoin", "CRYPTO", "COIN", "USD"),
    ("ETH", "Ethereum", "Ethereum", "CRYPTO", "COIN", "USD"),
    ("BNB", "BNB", "BNB", "CRYPTO", "COIN", "USD"),
    ("SOL", "Solana", "Solana", "CRYPTO", "COIN", "USD"),
    ("XRP", "XRP", "XRP", "CRYPTO", "COIN", "USD"),
    ("DOGE", "Dogecoin", "Dogecoin", "CRYPTO", "COIN", "USD"),
    ("ADA", "Cardano", "Cardano", "CRYPTO", "COIN", "USD"),
    ("WIG20", "WIG20", "WIG20", "INDEX", "STOCK_INDEX", "PLN"),
    ("WIG", "WIG", "WIG", "INDEX", "STOCK_INDEX", "PLN"),
    ("SP500", "S&P 500", "S&P 500", "INDEX", "STOCK_INDEX", "USD"),
    ("NASDAQ100", "Nasdaq 100", "Nasdaq 100", "INDEX", "STOCK_INDEX", "USD"),
    ("MSCI_WORLD", "MSCI World", "MSCI World", "INDEX", "ETF", "USD"),
    ("MSCI_EM", "MSCI Emerging Markets", "MSCI Emerging Markets", "INDEX", "ETF", "USD"),
    ("STOXX600", "STOXX Europe 600", "STOXX Europe 600", "INDEX", "STOCK_INDEX", "EUR"),
    ("EUROSTOXX50", "EURO STOXX 50", "EURO STOXX 50", "INDEX", "STOCK_INDEX", "EUR"),
    ("EURUSD", "EUR/USD", "EUR/USD", "FOREX", "FX_PAIR", "Ratio"),
    ("USDPLN", "USD/PLN", "USD/PLN", "FOREX", "FX_PAIR", "PLN"),
    ("EURPLN", "EUR/PLN", "EUR/PLN", "FOREX", "FX_PAIR", "PLN"),
    ("GBPUSD", "GBP/USD", "GBP/USD", "FOREX", "FX_PAIR", "Ratio"),
    ("USDJPY", "USD/JPY", "USD/JPY", "FOREX", "FX_PAIR", "JPY"),
    ("GOLD", "Gold", "Złoto", "FOREX", "METAL", "USD/oz"),
    ("BRENT", "Brent Oil", "Ropa Brent", "FOREX", "COMMODITY", "USD/bbl"),
    ("PL_CPI", "Poland CPI Inflation", "Inflacja CPI w Polsce", "GENERAL", "INFLATION", "%"),
    ("PL_NBP_RATE", "Poland NBP Interest Rate", "Stopa procentowa NBP", "GENERAL", "RATE", "%"),
    ("PL_GDP", "Poland Real GDP Growth", "Realny wzrost PKB Polski", "GENERAL", "GDP", "%"),
    ("PL_UNEMPLOYMENT", "Poland Unemployment Rate", "Stopa bezrobocia w Polsce", "GENERAL", "UNEMPLOYMENT", "%"),
    ("PL_HPI", "Poland Housing Price Index", "Indeks cen mieszkań w Polsce", "GENERAL", "HOUSING", "%"),
    ("PL_10Y_BOND", "Poland 10Y Bond Yield", "Rentowność 10-letnich obligacji Polski", "GENERAL", "BOND", "%"),
    ("PL_DE_RISK_PREMIUM", "Poland vs Germany Risk Premium", "Premia za ryzyko Polski wobec Niemiec", "GENERAL", "RISK_PREMIUM", "bps"),
    ("EZ_CPI", "Eurozone Inflation", "Inflacja w strefie euro", "GENERAL", "INFLATION", "%"),
    ("FED_RATE", "Fed Funds Rate", "Stopa procentowa Fed", "GENERAL", "RATE", "%"),
    ("ECB_RATE", "ECB Interest Rate", "Stopa procentowa EBC", "GENERAL", "RATE", "%"),
]


def defaults_for(category, subcategory):
    if category == FinancialProduct.Category.GENERAL:
        if subcategory in {
            FinancialProduct.Subcategory.INFLATION,
            FinancialProduct.Subcategory.UNEMPLOYMENT,
            FinancialProduct.Subcategory.HOUSING,
        }:
            return {
                "default_detail_en": "vs previous month",
                "default_detail_pl": "względem poprzedniego miesiąca",
                "update_frequency": FinancialProduct.UpdateFrequency.MONTHLY,
                "data_granularity": FinancialProduct.DataGranularity.MONTHLY,
            }
        if subcategory == FinancialProduct.Subcategory.GDP:
            return {
                "default_detail_en": "vs previous quarter",
                "default_detail_pl": "względem poprzedniego kwartału",
                "update_frequency": FinancialProduct.UpdateFrequency.QUARTERLY,
                "data_granularity": FinancialProduct.DataGranularity.QUARTERLY,
            }
        return {
            "default_detail_en": "vs previous reading",
            "default_detail_pl": "względem poprzedniego odczytu",
            "update_frequency": FinancialProduct.UpdateFrequency.EVENT_BASED,
            "data_granularity": FinancialProduct.DataGranularity.EVENT,
        }

    return {
        "default_detail_en": "vs previous close",
        "default_detail_pl": "względem poprzedniego zamknięcia",
        "update_frequency": FinancialProduct.UpdateFrequency.DAILY,
        "data_granularity": FinancialProduct.DataGranularity.DAILY_CLOSE,
    }


class Command(BaseCommand):
    help = "Create or update the fixed FinancU financial product allowlist."

    def handle(self, *args, **options):
        created = 0
        updated = 0

        for display_order, (symbol, name_en, name_pl, category, subcategory, unit) in enumerate(PRODUCTS, start=1):
            defaults = {
                "name_en": name_en,
                "name_pl": name_pl,
                "slug": slugify(symbol.replace("_", "-")),
                "category": category,
                "subcategory": subcategory,
                "unit": unit,
                "display_order": display_order,
                "is_active": True,
                "is_featured": False,
                **defaults_for(category, subcategory),
            }
            _, was_created = FinancialProduct.objects.update_or_create(
                symbol=symbol,
                defaults=defaults,
            )
            created += int(was_created)
            updated += int(not was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded financial products. Created: {created}. Updated: {updated}. Total: {len(PRODUCTS)}."
            )
        )
