import json
import logging
import os
import re
from pathlib import Path
from time import perf_counter

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from marketdata.services import import_market_data_from_gemini_payload

logger = logging.getLogger(__name__)

DEFAULT_MARKET_MODEL = "gemini-3.5-flash"
GOOGLE_SEARCH_FREE_REQUESTS_PER_MONTH = 5_000
GOOGLE_SEARCH_USD_PER_1000_REQUESTS = 14
GOOGLE_SEARCH_REQUESTS_PER_REFRESH = 1
EXPECTED_COLS = ["s", "v", "pv", "t", "pt", "src", "url", "q"]
REQUIRED_PAYLOAD_KEYS = {"ts", "st", "cols", "rows", "er"}
DEFAULT_PROMPT = """Return only valid minified JSON. No markdown. No explanations.

Fetch latest reliable data for:
BTC,ETH,BNB,SOL,XRP,DOGE,ADA,WIG20,WIG,SP500,NASDAQ100,MSCI_WORLD,MSCI_EM,STOXX600,EUROSTOXX50,EURUSD,USDPLN,EURPLN,GBPUSD,USDJPY,GOLD,BRENT,PL_CPI,PL_NBP_RATE,PL_GDP,PL_UNEMPLOYMENT,PL_HPI,PL_10Y_BOND,PL_DE_RISK_PREMIUM,EZ_CPI,FED_RATE,ECB_RATE

Rules:

* No invented data. Use null only if unavailable after checking reliable alternatives.
* Decimal point numbers.
* Market assets: compare with previous close, 24h or nearest comparable value.
* Macro data: compare with previous comparable month, quarter or central bank meeting.
* Market assets include crypto, stock indexes, ETF/index proxies, forex pairs, gold, oil, bond yields and risk premium/spreads.
* For market assets, prefer timestamp with timezone when the source clearly provides it, but do not sacrifice data completeness or source quality just to include a time. If only a reliable date is available, use the date.
* For macro data, use the official period/date, e.g. "2026-04", "2026-Q1", "2026-05-06".
* Never invent times.
* If previous_value is provided, previous_reference_at must also be provided whenever possible.
* For highly liquid market assets like BTC, ETH, BNB, SOL, XRP, DOGE, ADA, major indexes, forex, gold and Brent, never return a fully null row unless no reliable source is available after checking alternatives.
* Prefer official/financial sources: ECB, NBP, GUS, Eurostat, FRED, GPW, MSCI, STOXX, Trading Economics, Investing.com, Yahoo Finance, MarketWatch, Stooq, CoinMarketCap, exchanges/providers.
* Avoid blogs, newspapers, forums or unrelated sites if better sources exist.
* For forex pairs, prefer ECB, Trading Economics, Stooq, Investing.com, Yahoo Finance or official/recognized market data sources over broker blog pages.
* PL_DE_RISK_PREMIUM must be in basis points, e.g. 273 not 2.73.
* PL_HPI must be a housing price index value; use null if only growth % is found.
* For url, use the original public source URL if available. Do not use Google grounding redirect URLs. If only a Google grounding redirect URL is available, return null.
* Set status to PARTIAL_SUCCESS if any row has null current_value or null effective_at.

Schema:
{"ts":"ISO_DATE","st":"SUCCESS|PARTIAL_SUCCESS|FAILED","cols":["s","v","pv","t","pt","src","url","q"],"rows":[["BTC",null,null,null,null,null,null,null]],"er":[]}"""


def usage_value(usage, *names):
    if not usage:
        return 0

    for name in names:
        if isinstance(usage, dict) and usage.get(name) is not None:
            return int(usage.get(name) or 0)
        if hasattr(usage, name):
            return int(getattr(usage, name) or 0)

    return 0


def extract_token_usage(response):
    usage = getattr(response, "usage_metadata", None)
    input_tokens = usage_value(usage, "input_tokens", "prompt_token_count")
    output_tokens = usage_value(usage, "output_tokens", "candidates_token_count")

    if input_tokens or output_tokens:
        return input_tokens, output_tokens

    metadata = getattr(response, "response_metadata", {}) or {}
    token_usage = metadata.get("token_usage", {})
    input_tokens = usage_value(token_usage, "prompt_tokens", "input_tokens")
    output_tokens = usage_value(token_usage, "completion_tokens", "output_tokens")

    if input_tokens or output_tokens:
        return input_tokens, output_tokens

    gemini_usage = metadata.get("usage_metadata", {})
    return (
        usage_value(gemini_usage, "prompt_token_count", "input_tokens"),
        usage_value(gemini_usage, "candidates_token_count", "output_tokens"),
    )


def content_text(response):
    content = getattr(response, "content", response)

    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )

    text = str(content).strip()
    return re.sub(r"^```(?:json)?|```$", "", text, flags=re.IGNORECASE | re.MULTILINE).strip()


def json_preview(payload, max_chars=1200):
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def parse_llm_json_payload(raw_text):
    try:
        return json.loads(raw_text), ""
    except json.JSONDecodeError as first_error:
        stripped = raw_text.lstrip()
        if not stripped.startswith("{"):
            raise first_error

        decoder = json.JSONDecoder()
        payload, end_index = decoder.raw_decode(stripped)
        trailing_text = stripped[end_index:].strip()
        if not trailing_text:
            raise first_error

        return payload, trailing_text


def env_int(name, default=0):
    try:
        return max(0, int(os.getenv(name, default)))
    except (TypeError, ValueError):
        return default


def env_float(name, default=0):
    try:
        return max(0, float(os.getenv(name, default)))
    except (TypeError, ValueError):
        return default


def estimated_token_cost(input_tokens, output_tokens):
    input_rate = env_float("MARKET_LLM_INPUT_USD_PER_1M", 0)
    output_rate = env_float("MARKET_LLM_OUTPUT_USD_PER_1M", 0)

    return (
        (input_tokens / 1_000_000) * input_rate
        + (output_tokens / 1_000_000) * output_rate
    )


def estimated_google_search_cost(search_requests=GOOGLE_SEARCH_REQUESTS_PER_REFRESH):
    used_before = env_int("MARKET_LLM_GOOGLE_SEARCH_USED_THIS_MONTH", 0)
    free_remaining = max(0, GOOGLE_SEARCH_FREE_REQUESTS_PER_MONTH - used_before)
    paid_requests = max(0, search_requests - free_remaining)
    cost = (paid_requests / 1_000) * GOOGLE_SEARCH_USD_PER_1000_REQUESTS

    return {
        "requests": search_requests,
        "monthly_free_requests": GOOGLE_SEARCH_FREE_REQUESTS_PER_MONTH,
        "monthly_used_before": used_before,
        "monthly_free_remaining_before": free_remaining,
        "paid_requests": paid_requests,
        "cost_usd": cost,
    }


def market_api_key():
    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")


def is_thinking_level_config_error(error):
    if isinstance(error, TypeError):
        return True

    return error.__class__.__name__ == "ValidationError"


def build_market_llm(chat_model_class, model_name, api_key, stdout):
    kwargs = {
        "model": model_name,
        "temperature": 0,
        "response_mime_type": "application/json",
        "google_api_key": api_key,
    }

    try:
        return chat_model_class(**kwargs, thinking_level="low"), True
    except Exception as error:
        if not is_thinking_level_config_error(error):
            raise

        stdout.write(
            "Warning: thinking_level='low' is not supported by this "
            "langchain-google-genai/model combination. Retrying without thinking_level."
        )
        return chat_model_class(**kwargs), False


def validate_market_payload(payload):
    if not isinstance(payload, dict):
        raise CommandError("LLM market data payload must be a JSON object.")

    missing_keys = sorted(REQUIRED_PAYLOAD_KEYS - set(payload.keys()))
    if missing_keys:
        raise CommandError(f"LLM market data payload is missing required keys: {', '.join(missing_keys)}")

    if payload.get("cols") != EXPECTED_COLS:
        raise CommandError(f"LLM market data payload cols must equal {EXPECTED_COLS}.")

    if not isinstance(payload.get("rows"), list):
        raise CommandError("LLM market data payload rows must be a list.")

    if not isinstance(payload.get("er"), list):
        raise CommandError("LLM market data payload er must be a list.")


def failed_or_null_row_summaries(payload):
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    summaries = []

    for raw_row in rows:
        if not isinstance(raw_row, list):
            summaries.append(
                {
                    "symbol": "<invalid-row>",
                    "missing_value": True,
                    "missing_effective_at": True,
                    "source": None,
                }
            )
            continue

        symbol = raw_row[0] if len(raw_row) > 0 else "<missing-symbol>"
        value = raw_row[1] if len(raw_row) > 1 else None
        effective_at = raw_row[3] if len(raw_row) > 3 else None
        source = raw_row[5] if len(raw_row) > 5 else None
        missing_value = value is None
        missing_effective_at = effective_at is None

        if missing_value or missing_effective_at:
            summaries.append(
                {
                    "symbol": symbol or "<missing-symbol>",
                    "missing_value": missing_value,
                    "missing_effective_at": missing_effective_at,
                    "source": source,
                }
            )

    return summaries


class Command(BaseCommand):
    help = "Fetch daily market carousel data with Gemini/LangChain and import it into marketdata snapshots."

    def add_arguments(self, parser):
        parser.add_argument(
            "--prompt-file",
            help="Optional path to a custom prompt. Defaults to the built-in market data prompt.",
        )
        parser.add_argument(
            "--output",
            help="Optional path where the minified LLM JSON payload will be written.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Call the LLM and validate JSON, but do not import into the database.",
        )
        parser.add_argument(
            "--model",
            default=os.getenv("MARKET_LLM_MODEL", DEFAULT_MARKET_MODEL),
            help="Gemini model. Defaults to MARKET_LLM_MODEL or gemini-3.5-flash.",
        )

    def handle(self, *args, **options):
        prompt = DEFAULT_PROMPT
        prompt_file = options.get("prompt_file")
        if prompt_file:
            path = Path(prompt_file)
            if not path.exists() or not path.is_file():
                raise CommandError(f"Prompt file does not exist: {path}")
            prompt = path.read_text(encoding="utf-8")

        model_name = options["model"] or DEFAULT_MARKET_MODEL
        api_key = market_api_key()
        if not api_key:
            raise CommandError(
                "Missing Gemini API key. Set GOOGLE_API_KEY or GEMINI_API_KEY in backend/.env "
                "before running refresh_market_data_llm."
            )

        self.stdout.write(f"Starting market data LLM refresh. model={model_name}")

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as error:
            raise CommandError("langchain-google-genai is required to refresh market data with Gemini.") from error

        llm, thinking_level_enabled = build_market_llm(ChatGoogleGenerativeAI, model_name, api_key, self.stdout)
        self.stdout.write(
            "LLM config: "
            "temperature=0 "
            f"thinking_level={'low' if thinking_level_enabled else 'disabled'} "
            "google_search=enabled "
            "response_mime_type=application/json"
        )

        started = perf_counter()
        try:
            llm_with_search = llm.bind(tools=[{"google_search": {}}])
            response = llm_with_search.invoke(prompt)
        except Exception as error:
            logger.exception("Market data LLM request failed.")
            raise CommandError(f"Market data LLM request failed: {error}") from error

        duration_seconds = perf_counter() - started
        input_tokens, output_tokens = extract_token_usage(response)
        total_tokens = input_tokens + output_tokens
        token_cost = estimated_token_cost(input_tokens, output_tokens)
        search_cost = estimated_google_search_cost()
        total_cost = token_cost + search_cost["cost_usd"]

        self.stdout.write(
            "LLM request complete. "
            f"duration_seconds={duration_seconds:.2f} "
            f"input_tokens={input_tokens} output_tokens={output_tokens} total_tokens={total_tokens}"
        )
        self.stdout.write(f"Estimated token cost from env rates: ${token_cost:.6f}")
        self.stdout.write(
            "Estimated Google Search grounding cost, not billing truth. "
            f"requests={search_cost['requests']} "
            f"monthly_used_before={search_cost['monthly_used_before']} "
            f"free_remaining_before={search_cost['monthly_free_remaining_before']} "
            f"paid_requests={search_cost['paid_requests']} "
            f"cost=${search_cost['cost_usd']:.6f}"
        )
        self.stdout.write(f"Estimated total LLM cost, not billing truth: ${total_cost:.6f}")

        raw_text = content_text(response)
        try:
            payload, trailing_text = parse_llm_json_payload(raw_text)
        except json.JSONDecodeError as error:
            logger.error("Invalid market data JSON received: %s", raw_text[:2000])
            raise CommandError(f"LLM returned invalid JSON: {error}") from error

        validate_market_payload(payload)

        if trailing_text:
            logger.warning("Market data LLM returned trailing text after JSON: %s", trailing_text[:1000])
            self.stdout.write(
                "LLM returned trailing text after the first JSON object; "
                f"using parsed JSON and ignoring {len(trailing_text)} trailing characters."
            )

        if not isinstance(payload.get("_meta"), dict):
            payload["_meta"] = {}
        payload["_meta"]["llm"] = {
            "model": model_name,
            "temperature": 0,
            "thinking_level": "low" if thinking_level_enabled else None,
            "google_search": True,
            "response_mime_type": "application/json",
            "generated_at": timezone.now().isoformat(),
            "duration_seconds": round(duration_seconds, 3),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "input_usd_per_1m": env_float("MARKET_LLM_INPUT_USD_PER_1M", 0),
            "output_usd_per_1m": env_float("MARKET_LLM_OUTPUT_USD_PER_1M", 0),
            "estimated_token_cost_usd": round(token_cost, 8),
            "google_search_requests": search_cost["requests"],
            "google_search_monthly_free_requests": search_cost["monthly_free_requests"],
            "google_search_monthly_used_before": search_cost["monthly_used_before"],
            "google_search_monthly_free_remaining_before": search_cost["monthly_free_remaining_before"],
            "google_search_paid_requests": search_cost["paid_requests"],
            "google_search_cost_usd": round(search_cost["cost_usd"], 8),
            "estimated_cost_usd": round(total_cost, 8),
            "ignored_trailing_text_chars": len(trailing_text),
        }

        row_count = len(payload.get("rows") or []) if isinstance(payload.get("rows"), list) else 0
        null_rows = sum(
            1
            for row in payload.get("rows", [])
            if isinstance(row, list) and (len(row) < 4 or row[1] is None or row[3] is None)
        )
        self.stdout.write(
            "Payload parsed. "
            f"status={payload.get('st')} rows={row_count} rows_with_null_value_or_time={null_rows}"
        )
        row_summaries = failed_or_null_row_summaries(payload)
        if row_summaries:
            self.stdout.write("Rows with null/failed market fields before import:")
            for row_summary in row_summaries:
                self.stdout.write(
                    "  "
                    f"symbol={row_summary['symbol']} "
                    f"missing_value={row_summary['missing_value']} "
                    f"missing_effective_at={row_summary['missing_effective_at']} "
                    f"source={row_summary['source'] or ''}"
                )
        else:
            self.stdout.write("Rows with null/failed market fields before import: none")
        self.stdout.write(f"Payload preview: {json_preview(payload)}")

        output = options.get("output")
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
            self.stdout.write(f"Payload written to {output_path}")

        if options["dry_run"]:
            self.stdout.write("Dry run complete. Database import skipped.")
            return

        run = import_market_data_from_gemini_payload(payload)
        self.stdout.write("Market data import complete.")
        self.stdout.write(f"Run id: {run.id}")
        self.stdout.write(f"Status: {run.status}")
        self.stdout.write(f"Items received: {run.items_received}")
        self.stdout.write(f"Items imported: {run.items_imported}")
        self.stdout.write(f"Items updated: {run.items_updated}")
        self.stdout.write(f"Items skipped: {run.items_skipped}")
        self.stdout.write(f"Items failed: {run.items_failed}")
