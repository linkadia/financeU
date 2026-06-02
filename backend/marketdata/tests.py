from decimal import Decimal
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import ModuleType
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import TestCase

from .models import FinancialDataRun, FinancialProduct, FinancialProductSnapshot
from .serializers import ProductMarketSerializer
from .services import import_market_data_from_gemini_payload
from .management.commands.refresh_market_data_llm import parse_llm_json_payload


class MarketDataSeedCommandTests(TestCase):
    def test_seed_command_creates_32_products(self):
        call_command("seed_financial_products")

        self.assertEqual(FinancialProduct.objects.count(), 32)
        self.assertFalse(FinancialProduct.objects.get(symbol="BTC").is_featured)
        self.assertFalse(FinancialProduct.objects.get(symbol="BNB").is_featured)


class MarketDataImportServiceTests(TestCase):
    def setUp(self):
        call_command("seed_financial_products")

    def payload(self, rows):
        return {
            "ts": "2026-06-02T10:00:27Z",
            "st": "SUCCESS",
            "cols": ["s", "v", "pv", "t", "pt", "src", "url", "q"],
            "rows": rows,
            "er": [],
        }

    def test_imports_valid_payload_and_calculates_change_percent(self):
        run = import_market_data_from_gemini_payload(
            self.payload([
                ["BTC", 70800.0, 71100.0, "2026-06-01", "2026-05-31", "Robinhood", None, "0.8"],
            ])
        )

        snapshot = FinancialProductSnapshot.objects.get(product__symbol="BTC")
        self.assertEqual(run.status, FinancialDataRun.Status.SUCCESS)
        self.assertEqual(run.items_imported, 1)
        self.assertEqual(snapshot.current_value, Decimal("70800.0"))
        self.assertEqual(snapshot.change_absolute, Decimal("-300.0"))
        self.assertEqual(snapshot.change_percent.quantize(Decimal("0.00000001")), Decimal("-0.42194093"))
        self.assertEqual(snapshot.confidence_score, Decimal("0.8"))

    def test_unknown_symbol_is_skipped(self):
        run = import_market_data_from_gemini_payload(
            self.payload([
                ["NOPE", 10, 9, "2026-06-01", "2026-05-31", "Example", None, None],
            ])
        )

        self.assertEqual(run.status, FinancialDataRun.Status.FAILED)
        self.assertEqual(run.items_skipped, 1)
        self.assertEqual(FinancialProductSnapshot.objects.count(), 0)

    def test_null_values_do_not_crash_import(self):
        run = import_market_data_from_gemini_payload(
            self.payload([
                ["ETH", None, 2007.37, "2026-06-01", "2026-05-31", "MetaMask", None, "note"],
            ])
        )

        snapshot = FinancialProductSnapshot.objects.get(product__symbol="ETH")
        self.assertEqual(run.status, FinancialDataRun.Status.PARTIAL_SUCCESS)
        self.assertEqual(run.items_imported, 1)
        self.assertIsNone(snapshot.current_value)
        self.assertEqual(snapshot.validation_status, FinancialProductSnapshot.ValidationStatus.PARTIAL)
        self.assertIsNone(snapshot.quality_note)

    def test_monthly_and_quarterly_dates_are_parsed(self):
        import_market_data_from_gemini_payload(
            self.payload([
                ["PL_CPI", 3.2, 3.0, "2026-04", "2026-03", "GUS", None, "yoy"],
                ["PL_GDP", 1.1, 0.8, "2026-Q1", "2025-Q4", "GUS", None, None],
            ])
        )

        cpi = FinancialProductSnapshot.objects.get(product__symbol="PL_CPI")
        gdp = FinancialProductSnapshot.objects.get(product__symbol="PL_GDP")
        self.assertEqual(cpi.effective_date.isoformat(), "2026-04-01")
        self.assertIsNone(cpi.effective_datetime)
        self.assertEqual(gdp.effective_date.isoformat(), "2026-01-01")
        self.assertIsNone(gdp.effective_datetime)

    def test_importing_same_payload_twice_updates_without_duplicate_snapshots(self):
        payload = self.payload([
            ["BTC", 70800.0, 71100.0, "2026-06-01", "2026-05-31", "Robinhood", None, "0.8"],
        ])

        first_run = import_market_data_from_gemini_payload(payload)
        second_run = import_market_data_from_gemini_payload(payload)

        self.assertEqual(FinancialProductSnapshot.objects.filter(product__symbol="BTC").count(), 1)
        self.assertEqual(first_run.items_imported, 1)
        self.assertEqual(first_run.items_updated, 0)
        self.assertEqual(second_run.items_imported, 0)
        self.assertEqual(second_run.items_updated, 1)

    def test_same_product_with_different_effective_at_raw_creates_historical_snapshot(self):
        import_market_data_from_gemini_payload(
            self.payload([
                ["BTC", 70800.0, 71100.0, "2026-06-01", "2026-05-31", "Robinhood", None, None],
            ])
        )
        run = import_market_data_from_gemini_payload(
            self.payload([
                ["BTC", 70900.0, 70800.0, "2026-06-02", "2026-06-01", "Robinhood", None, None],
            ])
        )

        self.assertEqual(FinancialProductSnapshot.objects.filter(product__symbol="BTC").count(), 2)
        self.assertEqual(run.items_imported, 1)
        self.assertEqual(run.items_updated, 0)

    def test_same_product_and_effective_at_raw_with_new_value_updates_snapshot(self):
        import_market_data_from_gemini_payload(
            self.payload([
                ["BTC", 70800.0, 71100.0, "2026-06-01", "2026-05-31", "Robinhood", None, None],
            ])
        )
        run = import_market_data_from_gemini_payload(
            self.payload([
                ["BTC", 71000.0, 70800.0, "2026-06-01", "2026-05-31", "Updated Source", None, None],
            ])
        )

        snapshot = FinancialProductSnapshot.objects.get(product__symbol="BTC", effective_at_raw="2026-06-01")
        self.assertEqual(FinancialProductSnapshot.objects.filter(product__symbol="BTC").count(), 1)
        self.assertEqual(snapshot.current_value, Decimal("71000.0"))
        self.assertEqual(snapshot.source_name, "Updated Source")
        self.assertEqual(snapshot.run, run)
        self.assertEqual(run.items_imported, 0)
        self.assertEqual(run.items_updated, 1)

    def test_import_marks_products_with_latest_market_data_as_featured(self):
        FinancialProduct.objects.update(is_featured=False)

        import_market_data_from_gemini_payload(
            self.payload([
                ["XRP", 0.62, 0.60, "2026-06-01", "2026-05-31", "Example", None, None],
            ])
        )

        self.assertTrue(FinancialProduct.objects.get(symbol="XRP").is_featured)

    def test_import_unfeatures_product_when_latest_snapshot_has_no_market_value(self):
        import_market_data_from_gemini_payload(
            self.payload([
                ["XRP", 0.62, 0.60, "2026-06-01", "2026-05-31", "Example", None, None],
            ])
        )

        import_market_data_from_gemini_payload(
            self.payload([
                ["XRP", None, 0.62, "2026-06-02", "2026-06-01", "Example", None, None],
            ])
        )

        self.assertFalse(FinancialProduct.objects.get(symbol="XRP").is_featured)


class MarketDataSerializerTests(TestCase):
    def test_product_serializer_localizes_static_labels_from_product(self):
        call_command("seed_financial_products")
        product = FinancialProduct.objects.get(symbol="PL_CPI")

        serializer = ProductMarketSerializer(product, context={"lang": "pl"})

        self.assertEqual(serializer.data["name"], product.name_pl)
        self.assertEqual(serializer.data["default_detail"], product.default_detail_pl)
        self.assertEqual(serializer.data["unit_label"], product.unit)


class MarketDataJsonImportCommandTests(TestCase):
    def setUp(self):
        call_command("seed_financial_products")

    def test_import_market_data_json_command_uses_service(self):
        payload = {
            "ts": "2026-06-02T10:00:27Z",
            "st": "SUCCESS",
            "cols": ["s", "v", "pv", "t", "pt", "src", "url", "q"],
            "rows": [["BTC", "100", "80", "2026-06-01", "2026-05-31", "Example", None, None]],
            "er": [],
        }

        with TemporaryDirectory() as directory:
            path = Path(directory) / "market.json"
            path.write_text(json.dumps(payload), encoding="utf-8")

            call_command("import_market_data_json", str(path))

        self.assertEqual(FinancialProductSnapshot.objects.count(), 1)
        snapshot = FinancialProductSnapshot.objects.get(product__symbol="BTC")
        self.assertEqual(snapshot.current_value, Decimal("100"))

    def test_import_market_data_json_missing_file_raises_command_error(self):
        with self.assertRaises(CommandError):
            call_command("import_market_data_json", "missing-market-data.json")

    def test_import_market_data_json_invalid_json_raises_command_error(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "broken.json"
            path.write_text("{not-json", encoding="utf-8")

            with self.assertRaises(CommandError):
                call_command("import_market_data_json", str(path))


class FakeMarketLLMResponse:
    content = json.dumps(
        {
            "ts": "2026-06-02",
            "st": "SUCCESS",
            "cols": ["s", "v", "pv", "t", "pt", "src", "url", "q"],
            "rows": [["BTC", 100, 90, "2026-06-02", "2026-06-01", "Example", None, "0.9"]],
            "er": [],
        },
        separators=(",", ":"),
    )
    usage_metadata = {
        "input_tokens": 1000,
        "output_tokens": 500,
    }


class FakeMarketLLM:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.bound_kwargs = None
        self.invocations = []
        FakeMarketLLM.instances.append(self)

    def bind(self, **kwargs):
        self.bound_kwargs = kwargs
        return self

    def invoke(self, prompt):
        self.invocations.append({"prompt": prompt})
        return FakeMarketLLMResponse()


class FakeMarketLLMWithoutThinking(FakeMarketLLM):
    def __init__(self, **kwargs):
        if "thinking_level" in kwargs:
            raise TypeError("thinking_level is not supported")
        super().__init__(**kwargs)


class RefreshMarketDataLLMCommandTests(TestCase):
    def setUp(self):
        call_command("seed_financial_products")
        FakeMarketLLM.instances = []

    def fake_langchain_module(self):
        module = ModuleType("langchain_google_genai")
        module.ChatGoogleGenerativeAI = FakeMarketLLM
        return module

    def fake_langchain_module_without_thinking(self):
        module = ModuleType("langchain_google_genai")
        module.ChatGoogleGenerativeAI = FakeMarketLLMWithoutThinking
        return module

    def test_refresh_market_data_llm_dry_run_uses_market_model_and_search(self):
        with TemporaryDirectory() as directory:
            output_path = Path(directory) / "market.json"
            with patch.dict(sys.modules, {"langchain_google_genai": self.fake_langchain_module()}):
                with patch.dict(
                    "os.environ",
                    {
                        "GOOGLE_API_KEY": "test-api-key",
                        "MARKET_LLM_MODEL": "test-market-model",
                        "MARKET_LLM_INPUT_USD_PER_1M": "1.5",
                        "MARKET_LLM_OUTPUT_USD_PER_1M": "9",
                        "MARKET_LLM_GOOGLE_SEARCH_USED_THIS_MONTH": "5000",
                    },
                ):
                    call_command("refresh_market_data_llm", "--dry-run", "--output", str(output_path))

            self.assertEqual(FakeMarketLLM.instances[0].kwargs["model"], "test-market-model")
            self.assertEqual(FakeMarketLLM.instances[0].kwargs["temperature"], 0)
            self.assertEqual(FakeMarketLLM.instances[0].kwargs["thinking_level"], "low")
            self.assertEqual(FakeMarketLLM.instances[0].kwargs["response_mime_type"], "application/json")
            self.assertEqual(FakeMarketLLM.instances[0].kwargs["google_api_key"], "test-api-key")
            self.assertEqual(
                FakeMarketLLM.instances[0].bound_kwargs["tools"],
                [{"google_search": {}}],
            )
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            llm_meta = payload["_meta"]["llm"]
            self.assertEqual(llm_meta["model"], "test-market-model")
            self.assertEqual(llm_meta["input_tokens"], 1000)
            self.assertEqual(llm_meta["output_tokens"], 500)
            self.assertEqual(llm_meta["google_search_requests"], 1)
            self.assertEqual(llm_meta["google_search_monthly_free_requests"], 5000)
            self.assertEqual(llm_meta["google_search_monthly_used_before"], 5000)
            self.assertEqual(llm_meta["google_search_paid_requests"], 1)
            self.assertEqual(llm_meta["google_search_cost_usd"], 0.014)
            self.assertEqual(llm_meta["estimated_token_cost_usd"], 0.006)
            self.assertEqual(llm_meta["estimated_cost_usd"], 0.02)
            self.assertEqual(FinancialProductSnapshot.objects.count(), 0)

    def test_refresh_market_data_llm_imports_payload(self):
        with patch.dict(sys.modules, {"langchain_google_genai": self.fake_langchain_module()}):
            with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-api-key"}):
                call_command("refresh_market_data_llm", "--model", "test-market-model")

        self.assertEqual(FinancialProductSnapshot.objects.count(), 1)
        snapshot = FinancialProductSnapshot.objects.get(product__symbol="BTC")
        self.assertEqual(snapshot.current_value, Decimal("100"))
        self.assertEqual(snapshot.run.raw_response["_meta"]["llm"]["model"], "test-market-model")
        self.assertEqual(snapshot.run.raw_response["_meta"]["llm"]["google_search_paid_requests"], 0)

    def test_refresh_market_data_llm_requires_api_key(self):
        with patch.dict(sys.modules, {"langchain_google_genai": self.fake_langchain_module()}):
            with patch.dict("os.environ", {"GOOGLE_API_KEY": "", "GEMINI_API_KEY": ""}):
                with self.assertRaises(CommandError):
                    call_command("refresh_market_data_llm", "--model", "test-market-model")

    def test_refresh_market_data_llm_falls_back_without_thinking_level(self):
        FakeMarketLLMWithoutThinking.instances = []
        with patch.dict(sys.modules, {"langchain_google_genai": self.fake_langchain_module_without_thinking()}):
            with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-api-key"}):
                call_command("refresh_market_data_llm", "--model", "test-market-model")

        snapshot = FinancialProductSnapshot.objects.get(product__symbol="BTC")
        self.assertIsNone(snapshot.run.raw_response["_meta"]["llm"]["thinking_level"])

    def test_parse_llm_json_payload_accepts_trailing_text_after_json(self):
        payload, trailing_text = parse_llm_json_payload('{"st":"SUCCESS","rows":[]}\n{"extra":"ignored"}')

        self.assertEqual(payload["st"], "SUCCESS")
        self.assertEqual(trailing_text, '{"extra":"ignored"}')

    def test_parse_llm_json_payload_rejects_broken_json(self):
        with self.assertRaises(json.JSONDecodeError):
            parse_llm_json_payload('{"st":"SUCCESS",')


class LatestMarketSnapshotsApiTests(TestCase):
    def setUp(self):
        call_command("seed_financial_products")

    def payload(self, rows):
        return {
            "ts": "2026-06-02T10:00:27Z",
            "st": "SUCCESS",
            "cols": ["s", "v", "pv", "t", "pt", "src", "url", "q"],
            "rows": rows,
            "er": [],
        }

    def test_latest_snapshots_returns_frontend_friendly_featured_rows(self):
        import_market_data_from_gemini_payload(
            self.payload([
                ["BTC", 100, 90, "2026-06-01", "2026-05-31", "Example", None, None],
                ["BNB", 80, 90, "2026-06-01", "2026-05-31", "Example", None, None],
                ["ETH", 50, 50, "2026-06-01", "2026-05-31", "Example", None, None],
            ])
        )

        response = self.client.get("/api/market/snapshots/latest/", {"featured": "true", "lang": "pl"})

        self.assertEqual(response.status_code, 200)
        symbols = [item["symbol"] for item in response.data]
        btc = FinancialProduct.objects.get(symbol="BTC")
        self.assertEqual(symbols, ["BTC", "ETH", "BNB"])
        self.assertEqual(response.data[0]["name"], "Bitcoin")
        self.assertEqual(response.data[0]["default_detail"], btc.default_detail_pl)
        self.assertEqual(response.data[0]["direction"], "UP")
        self.assertEqual(response.data[1]["direction"], "FLAT")
        self.assertNotIn("raw_row", response.data[0])

    def test_latest_snapshots_filters_category_and_excludes_unusable_snapshots(self):
        import_market_data_from_gemini_payload(
            self.payload([
                ["BTC", 100, 90, "2026-06-01", "2026-05-31", "Example", None, None],
                ["WIG20", 3000, 3100, "2026-06-01", "2026-05-31", "Example", None, None],
                ["ETH", None, 50, "2026-06-01", "2026-05-31", "Example", None, None],
            ])
        )

        response = self.client.get("/api/market/snapshots/latest/", {"category": "CRYPTO"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["symbol"] for item in response.data], ["BTC"])
        self.assertEqual(response.data[0]["direction"], "UP")

    def test_latest_snapshots_uses_newest_usable_snapshot_per_product(self):
        import_market_data_from_gemini_payload(
            self.payload([
                ["BTC", 100, 90, "2026-06-01", "2026-05-31", "Old Source", None, None],
                ["BTC", 95, 100, "2026-06-02", "2026-06-01", "New Source", None, None],
            ])
        )

        response = self.client.get("/api/market/snapshots/latest/", {"featured": "true"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["symbol"], "BTC")
        self.assertEqual(response.data[0]["current_value"], "95.00000000")
        self.assertEqual(response.data[0]["effective_at_raw"], "2026-06-02")
        self.assertEqual(response.data[0]["source_name"], "New Source")
        self.assertEqual(response.data[0]["direction"], "DOWN")
