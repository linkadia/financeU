import io
import json
import sys
from contextlib import contextmanager
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.db import transaction
from django.test import TestCase
from django.utils import timezone

from .management.commands.refresh_market_data_llm import Command, DEFAULT_SYMBOLS, EXPECTED_COLS
from .models import FinancialDataRun, FinancialProduct, FinancialProductSnapshot
from .services import import_market_data_from_gemini_payload


def market_payload(symbols=DEFAULT_SYMBOLS):
    return {
        "ts": "2026-10-23T06:00:00Z", "st": "SUCCESS", "cols": EXPECTED_COLS,
        "rows": [
            [symbol, 100, 90, "2026-10-23", "2026-10-22", "Source", "https://example.com/market", True]
            for symbol in symbols
        ],
        "er": [],
    }


class RefreshReliabilityTests(TestCase):
    def setUp(self):
        call_command("seed_financial_products", stdout=io.StringIO())

    @contextmanager
    def mock_llm(self, responses, on_invoke=None):
        queue = list(responses)

        class FakeLLM:
            prompts = []
            kwargs = None

            def __init__(self, **kwargs):
                FakeLLM.kwargs = kwargs

            def bind(self, **kwargs):
                return self

            def invoke(self, prompt):
                FakeLLM.prompts.append(prompt)
                if on_invoke:
                    on_invoke()
                if not queue:
                    raise AssertionError("Unexpected extra Gemini request")
                response = queue.pop(0)
                if isinstance(response, Exception):
                    raise response
                return SimpleNamespace(
                    content=response if isinstance(response, str) else json.dumps(response),
                    usage_metadata={"input_tokens": 100, "output_tokens": 50},
                )

        module = ModuleType("langchain_google_genai")
        module.ChatGoogleGenerativeAI = FakeLLM
        with patch.dict(sys.modules, {"langchain_google_genai": module}), patch.dict(
            "os.environ", {
                "GOOGLE_API_KEY": "mock-key", "MARKET_LLM_MAX_ATTEMPTS": "3",
                "MARKET_LLM_MISSING_RETRIES": "1", "MARKET_LLM_GOOGLE_SEARCH_USED_THIS_MONTH": "5000",
                "MARKET_LLM_INPUT_USD_PER_1M": "1.5", "MARKET_LLM_OUTPUT_USD_PER_1M": "9",
            },
        ):
            yield FakeLLM

    def refresh(self, *args):
        return call_command(
            "refresh_market_data_llm", "--model", "mock-market-model", *args,
            stdout=io.StringIO(), stderr=io.StringIO(),
        )

    def test_run_is_pending_before_gemini_and_reused_for_import(self):
        def check_audit():
            self.assertEqual(FinancialDataRun.objects.count(), 1)
            self.assertEqual(FinancialDataRun.objects.get().status, "PENDING")

        with self.mock_llm([market_payload()], check_audit):
            self.refresh()
        run = FinancialDataRun.objects.get()
        self.assertEqual(run.status, "SUCCESS")
        self.assertEqual(run.items_imported, 32)
        self.assertEqual(run.snapshots.count(), 32)

    def test_log_json_errors_are_retried_and_all_attempts_are_accounted_for(self):
        malformed = [
            '{"rows":[["PL_CPI":3.4]]}',
            '{"rows":[["SP500",5853.98,5851.2,2026-10-22,2026-10-21]]}',
        ]
        with self.mock_llm([*malformed, market_payload()]) as llm:
            self.refresh()
        run = FinancialDataRun.objects.get()
        self.assertEqual(run.status, "SUCCESS")
        self.assertEqual(len(llm.prompts), 3)
        meta = run.raw_response["_meta"]["llm"]
        self.assertEqual(meta["input_tokens"], 300)
        self.assertEqual(meta["output_tokens"], 150)
        self.assertEqual(meta["google_search_requests"], 3)
        self.assertEqual(meta["google_search_cost_usd"], 0.042)
        self.assertEqual([attempt["status"] for attempt in meta["attempts"]], ["FAILED", "FAILED", "VALID"])
        self.assertEqual(meta["attempts"][0]["raw_response"], malformed[0])

    def test_exhausted_invalid_json_remains_visible_as_failed(self):
        with self.mock_llm(["{broken"] * 3) as llm:
            with self.assertRaisesRegex(CommandError, "after 3 attempts"):
                self.refresh()
        run = FinancialDataRun.objects.get()
        self.assertEqual(run.status, "FAILED")
        self.assertIsNotNone(run.finished_at)
        self.assertIn("after 3 attempts", run.error_message)
        self.assertEqual(len(llm.prompts), 3)
        self.assertEqual(len(run.raw_response["_meta"]["llm"]["attempts"]), 3)
        self.assertEqual(FinancialProductSnapshot.objects.count(), 0)

    def test_api_error_is_retried_and_audited(self):
        with self.mock_llm([RuntimeError("503 ServiceUnavailable"), market_payload()]):
            self.refresh()
        run = FinancialDataRun.objects.get()
        self.assertEqual(run.status, "SUCCESS")
        self.assertIn("503", run.raw_response["_meta"]["llm"]["attempts"][0]["error"])

    def test_invalid_row_shape_and_duplicate_symbols_trigger_validation_retry(self):
        malformed = market_payload()
        malformed["rows"][0] = ["BTC", 100]
        duplicate = market_payload()
        duplicate["rows"][1][0] = "BTC"
        with self.mock_llm([malformed, duplicate, market_payload()]):
            self.refresh()
        self.assertEqual(FinancialDataRun.objects.get().status, "SUCCESS")
        self.assertEqual(FinancialProductSnapshot.objects.count(), 32)

    def test_missing_symbol_search_preserves_good_initial_rows(self):
        initial = market_payload()
        initial["rows"][0][1] = 123
        initial["rows"][7] = ["WIG20", None, None, None, None, None, None, False]
        with self.mock_llm([initial, market_payload(["WIG20"])]) as llm:
            self.refresh()
        run = FinancialDataRun.objects.get()
        self.assertEqual(run.status, "SUCCESS")
        self.assertEqual(run.items_failed, 0)
        self.assertEqual(FinancialProductSnapshot.objects.get(product__symbol="BTC").current_value, 123)
        self.assertIn("Only return these symbols: WIG20.", llm.prompts[1])
        self.assertNotIn(
            "BTC,ETH,BNB", llm.prompts[1],
        )

    def test_eleven_incomplete_symbols_from_run_70_are_retried_as_a_batch(self):
        missing = [
            "WIG20", "WIG", "MSCI_WORLD", "MSCI_EM", "STOXX600", "GBPUSD",
            "USDJPY", "PL_HPI", "EZ_CPI", "FED_RATE", "ECB_RATE",
        ]
        old = market_payload(["PL_HPI"])
        old["rows"][0][3] = "2026-Q2"
        import_market_data_from_gemini_payload(old)
        initial = market_payload()
        initial["rows"] = [
            [row[0], None, None, None, None, None, None, False] if row[0] in missing else row
            for row in initial["rows"]
        ]
        recovered = ["WIG20", "WIG", "GBPUSD", "USDJPY", "FED_RATE", "ECB_RATE"]
        with self.mock_llm([initial, market_payload(recovered)]) as llm:
            self.refresh()
        run = FinancialDataRun.objects.order_by("-pk").first()
        self.assertEqual(run.status, "PARTIAL_SUCCESS")
        self.assertEqual((run.items_imported, run.items_failed), (27, 5))
        self.assertEqual(run.raw_response["_meta"]["llm"]["attempts"][1]["symbols"], missing)
        self.assertTrue(FinancialProduct.objects.get(symbol="PL_HPI").is_featured)
        self.assertEqual(FinancialProductSnapshot.objects.get(product__symbol="PL_HPI").current_value, 100)
        self.assertEqual(len(llm.prompts), 2)

    def test_omitted_symbol_can_be_recovered(self):
        initial = market_payload([symbol for symbol in DEFAULT_SYMBOLS if symbol != "PL_HPI"])
        with self.mock_llm([initial, market_payload(["PL_HPI"])]):
            self.refresh()
        run = FinancialDataRun.objects.get()
        self.assertEqual((run.items_expected, run.items_received, run.items_imported), (32, 32, 32))

    def test_failed_recovery_still_imports_good_initial_rows(self):
        initial = market_payload()
        initial["rows"][26] = ["PL_HPI", None, None, None, None, None, None, None]
        with self.mock_llm([initial, "{broken", "{broken", "{broken"]):
            self.refresh()
        run = FinancialDataRun.objects.get()
        self.assertEqual(run.status, "PARTIAL_SUCCESS")
        self.assertEqual(run.items_imported, 31)
        self.assertEqual(run.items_failed, 1)
        self.assertEqual(len(run.raw_response["_meta"]["llm"]["attempts"]), 4)

    def test_unrecovered_omission_is_counted_as_failed(self):
        initial = market_payload([symbol for symbol in DEFAULT_SYMBOLS if symbol != "PL_HPI"])
        with self.mock_llm([initial]):
            self.refresh("--missing-retries", "0")
        run = FinancialDataRun.objects.get()
        self.assertEqual(run.status, "PARTIAL_SUCCESS")
        self.assertEqual((run.items_expected, run.items_received, run.items_failed), (32, 31, 1))
        self.assertIn("Missing market data row", run.errors[0]["error"])

    def test_all_null_rows_return_a_command_error_with_one_failed_run(self):
        initial = market_payload()
        initial["rows"] = [[symbol, None, None, None, None, None, None, False] for symbol in DEFAULT_SYMBOLS]
        with self.mock_llm([initial, initial]):
            with self.assertRaisesRegex(CommandError, "Market data import failed"):
                self.refresh()
        run = FinancialDataRun.objects.get()
        self.assertEqual(run.status, "FAILED")
        self.assertEqual(run.items_failed, 32)
        self.assertEqual(FinancialProductSnapshot.objects.count(), 0)

    def test_failed_import_exits_with_code_one_when_called_from_cron(self):
        empty = market_payload([])
        with self.mock_llm([empty]):
            command = Command(stdout=io.StringIO(), stderr=io.StringIO())
            with self.assertRaises(SystemExit) as result:
                command.run_from_argv([
                    "manage.py", "refresh_market_data_llm", "--max-attempts", "1", "--missing-retries", "0",
                ])
        self.assertEqual(result.exception.code, 1)
        self.assertEqual(FinancialDataRun.objects.get().status, "FAILED")

    def test_malformed_optional_metadata_cannot_prevent_failure_audit(self):
        initial = market_payload()
        initial["_meta"] = "untrusted-model-metadata"
        initial["rows"][26] = ["PL_HPI", None, None, None, None, None, None, None]
        with self.mock_llm([initial, "{broken", "{broken", "{broken"]):
            self.refresh()
        self.assertEqual(FinancialDataRun.objects.get().status, "PARTIAL_SUCCESS")

    def test_setup_failure_is_recorded_before_any_request(self):
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "", "GEMINI_API_KEY": ""}):
            with self.assertRaisesRegex(CommandError, "Missing Gemini API key"):
                self.refresh()
        run = FinancialDataRun.objects.get()
        self.assertEqual(run.status, "FAILED")
        self.assertEqual(run.raw_response["_meta"]["llm"]["attempts"], [])

    def test_import_rollback_preserves_failed_audit_record(self):
        def failed_import(*args, **kwargs):
            with transaction.atomic():
                FinancialProduct.objects.filter(symbol="BTC").update(name_en="Rolled back")
                raise RuntimeError("Import database error")

        with self.mock_llm([market_payload()]), patch(
            "marketdata.management.commands.refresh_market_data_llm.import_market_data_from_gemini_payload",
            side_effect=failed_import,
        ):
            with self.assertRaisesRegex(CommandError, "Import database error"):
                self.refresh()
        self.assertEqual(FinancialDataRun.objects.get().status, "FAILED")
        self.assertEqual(FinancialProduct.objects.get(symbol="BTC").name_en, "Bitcoin")

    def test_dry_run_never_creates_audit_or_snapshot_records(self):
        with self.mock_llm([market_payload()]):
            self.refresh("--dry-run")
        self.assertEqual(FinancialDataRun.objects.count(), 0)
        self.assertEqual(FinancialProductSnapshot.objects.count(), 0)

    def test_failed_dry_run_also_leaves_database_untouched(self):
        with self.mock_llm(["{broken"] * 3):
            with self.assertRaises(CommandError):
                self.refresh("--dry-run")
        self.assertEqual(FinancialDataRun.objects.count(), 0)

    def test_native_schema_and_timeout_are_passed_to_the_model(self):
        with self.mock_llm([market_payload()]) as llm:
            self.refresh()
        schema = llm.kwargs["response_schema"]
        fields = schema["properties"]["rows"]["items"]["prefixItems"]
        self.assertEqual(fields[1]["type"], ["number", "null"])
        self.assertEqual(fields[3]["type"], ["string", "null"])
        self.assertEqual(llm.kwargs["max_retries"], 0)
        self.assertGreater(llm.kwargs["timeout"], 0)


class SnapshotPreservationTests(TestCase):
    def setUp(self):
        call_command("seed_financial_products", stdout=io.StringIO())
        self.good_run = import_market_data_from_gemini_payload(market_payload(["BTC"]))

    def test_null_same_date_cannot_overwrite_a_valid_snapshot(self):
        payload = market_payload(["BTC"])
        payload["rows"][0][1] = None
        run = import_market_data_from_gemini_payload(payload)
        snapshot = FinancialProductSnapshot.objects.get(product__symbol="BTC")
        self.assertEqual(snapshot.current_value, 100)
        self.assertEqual(snapshot.run_id, self.good_run.pk)
        self.assertEqual(run.status, "FAILED")
        self.assertTrue(FinancialProduct.objects.get(symbol="BTC").is_featured)

    def test_invalid_dates_and_non_finite_prices_are_rejected_without_writes(self):
        for value, effective_at in [(100, "2026"), ("NaN", "2026-10-23"), ("Infinity", "2026-10-23"), (True, "2026-10-23")]:
            with self.subTest(value=value, effective_at=effective_at):
                payload = market_payload(["BTC"])
                payload["rows"][0][1] = value
                payload["rows"][0][3] = effective_at
                run = import_market_data_from_gemini_payload(payload)
                self.assertEqual(run.status, "FAILED")
                self.assertEqual(FinancialProductSnapshot.objects.get(product__symbol="BTC").current_value, 100)

    def test_legacy_incomplete_snapshot_does_not_hide_last_usable_value(self):
        FinancialProductSnapshot.objects.create(
            product=FinancialProduct.objects.get(symbol="BTC"), effective_at_raw="2026-10-24",
            effective_date=timezone.now().date(), current_value=None, validation_status="PARTIAL",
        )
        import_market_data_from_gemini_payload(market_payload(["ETH"]))
        self.assertTrue(FinancialProduct.objects.get(symbol="BTC").is_featured)
