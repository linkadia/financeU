from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from marketdata.catalog import PRODUCTS
from marketdata.models import FinancialProduct


def defaults_for(category, subcategory):
    if category == FinancialProduct.Category.CRYPTO:
        return {
            "default_detail_en": "vs 24 hours earlier",
            "default_detail_pl": "względem wartości sprzed 24 godzin",
            "update_frequency": FinancialProduct.UpdateFrequency.DAILY,
            "data_granularity": FinancialProduct.DataGranularity.REALTIME,
        }
    if category == FinancialProduct.Category.GENERAL:
        if subcategory in {
            FinancialProduct.Subcategory.INFLATION,
            FinancialProduct.Subcategory.UNEMPLOYMENT,
        }:
            return {
                "default_detail_en": "vs previous month",
                "default_detail_pl": "względem poprzedniego miesiąca",
                "update_frequency": FinancialProduct.UpdateFrequency.MONTHLY,
                "data_granularity": FinancialProduct.DataGranularity.MONTHLY,
            }
        if subcategory in {FinancialProduct.Subcategory.GDP, FinancialProduct.Subcategory.HOUSING}:
            return {
                "default_detail_en": "vs previous quarter",
                "default_detail_pl": "względem poprzedniego kwartału",
                "update_frequency": FinancialProduct.UpdateFrequency.QUARTERLY,
                "data_granularity": FinancialProduct.DataGranularity.QUARTERLY,
            }
        if subcategory not in {FinancialProduct.Subcategory.BOND, FinancialProduct.Subcategory.RISK_PREMIUM}:
            return {
                "default_detail_en": "vs previous policy setting",
                "default_detail_pl": "względem poprzedniej obowiązującej stopy",
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

    @transaction.atomic
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
                "unit_label_en": "points" if unit == "points" else "",
                "unit_label_pl": "pkt" if unit == "points" else "",
                "display_order": display_order,
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
