import argparse
import hashlib
import json
import os
import re
import sys
import warnings
import xml.etree.ElementTree as ET
from datetime import datetime, date
from email.utils import parsedate_to_datetime
from pathlib import Path
import time  
from typing import Literal

import django
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from django.utils import timezone
from requests import get
from rss_parser import RSSParser
from urllib.parse import urlparse, urlunparse
from pydantic import BaseModel, Field

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finanu_backend.settings")
django.setup()

from django.db.models import Q  # noqa: E402
from content.models import NewsArticle  # noqa: E402


DEFAULT_XML_PATH = Path(__file__).with_name("rss_output.xml")
DEFAULT_MIN_PUBLISHED_AT = date.today().replace(day=1).strftime("%Y-%m-%d")
RSS_URLS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss",
    "https://cointelegraph.com/rss",
    "https://www.actionforex.com/feed/",
    "https://www.forexcrunch.com/feed/",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://feeds.content.dowjones.io/public/rss/mw_marketpulse",
    "https://finance.yahoo.com/news/rssindex",
    "https://www.pb.pl/rss/najnowsze.xml",
]
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    )
}
TEXT_LIMITS = {
    "headline": 140,
    "subtitle": 240,
    "short_summary": 700,
    "beginner_summary": 1400,
    "advanced_summary": 1700,
}
ALLOWED_DIFFICULTIES = set(NewsArticle.Difficulty.values)
ALLOWED_NEWS_TYPES = set(NewsArticle.NewsType.values)
GEMINI_FLASH_LITE_INPUT_USD_PER_1M = 0.25
GEMINI_FLASH_LITE_OUTPUT_USD_PER_1M = 1.5


class TranslationOutput(BaseModel):
    headline: str = Field(description="Frontend-ready headline.")
    subtitle: str = Field(description="Brief subtitle.")
    short_summary: str = Field(description="Short summary.")
    beginner_summary: str = Field(description="Simple beginner explanation.")
    advanced_summary: str = Field(description="More technical explanation.")


class NewsTranslationsOutput(BaseModel):
    en: TranslationOutput
    pl: TranslationOutput


class NewsLLMOutput(BaseModel):
    translations: NewsTranslationsOutput
    difficulty: Literal["beginner", "intermediate", "advanced"]
    news_type: Literal["crypto", "stock_market", "forex", "investing_basics"]
    importance_score: int = Field(ge=0, le=100)
    original_language: Literal["en", "pl", "unknown"]
    tags: list[str]
    mentioned_assets: list[str]

LLM_PROMPT = """
You are a financial editor for an educational app called FinanU.
You will receive one RSS news item with its title, source, URL, publication date, and HTML-cleaned content.

Return ONLY valid JSON with this exact shape:
{{
  "translations": {{
    "en": {{
      "headline": "clear headline in English",
      "subtitle": "brief subtitle in English",
      "short_summary": "1-2 sentence summary in English",
      "beginner_summary": "simple explanation in English for finance beginners",
      "advanced_summary": "more technical explanation in English"
    }},
    "pl": {{
      "headline": "jasny naglowek po polsku",
      "subtitle": "krotki podtytul po polsku",
      "short_summary": "streszczenie w 1-2 zdaniach po polsku",
      "beginner_summary": "proste wyjasnienie po polsku dla osob poczatkujacych",
      "advanced_summary": "bardziej techniczne wyjasnienie po polsku"
    }}
  }},
  "difficulty": "beginner|intermediate|advanced",
  "news_type": "crypto|stock_market|forex|investing_basics",
  "importance_score": 0,
  "original_language": "en|pl|unknown",
  "tags": ["tag1", "tag2"],
  "mentioned_assets": ["BTC", "EUR/USD", "AAPL"]
}}

Rules:
- Use "crypto" for Bitcoin, Ethereum, blockchain, exchanges, stablecoins, or crypto assets.
- Use "forex" for currencies, FX pairs, central banks, or interest-rate news with direct currency impact.
- Use "stock_market" for equities, indexes, listed companies, commodities, broad markets, or macro market news.
- Use "investing_basics" only for general educational investing content.
- importance_score must reflect potential market or educational impact: 0 means irrelevant, 100 means extremely important.
- Do not invent facts that are not present in the RSS item.
- Generate natural, frontend-ready text in both English and Polish.
- Keep tickers, company names, FX pairs, numbers, dates, and quoted figures unchanged.
- Do not include personalized investment advice or calls to buy/sell.
- If the RSS item has limited context, summarize only what is verifiable and briefly acknowledge uncertainty.
- Avoid sensational language. Keep the tone clear, educational, and sober.
- Use short, scannable sentences suitable for mobile UI.
- Stay close to these ranges, but prioritize clarity and factual accuracy over exact word counts:
  - headline: 8-14 words.
  - subtitle: 12-24 words.
  - short_summary: 35-60 words.
  - beginner_summary: 80-130 words.
  - advanced_summary: 90-150 words.
- For importance_score:
  - 0-30: minor, educational, or low-impact item.
  - 31-60: normal market move or relevant sector news.
  - 61-80: clear impact on a major asset, index, currency, or sector.
  - 81-100: macro, regulatory, crisis, market shock, or exceptional event.
- tags must contain 3-8 short, useful labels.
- mentioned_assets must contain only explicitly mentioned assets, tickers, indexes, FX pairs, or crypto assets.

News item:
Source: {source_name}
URL: {source_url}
Original title: {headline}
Published at: {published_at}
Content:
{content}
"""


def tag_text(value):
    if value is None:
        return ""
    return str(getattr(value, "content", value))


def download_unified_rss(output_path):
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = "Unified Finance RSS"
    ET.SubElement(channel, "link").text = "https://example.com"
    ET.SubElement(channel, "description").text = "Unified RSS feed from multiple finance sources."

    downloaded_sources = 0
    imported_items = 0

    for rss_url in RSS_URLS:
        try:
            response = get(rss_url, headers=REQUEST_HEADERS, timeout=15)
            response.raise_for_status()
        except Exception as error:
            print(f"Could not download {rss_url}: {error}")
            continue

        try:
            rss = RSSParser.parse(response.text)
        except Exception as error:
            print(f"Could not parse {rss_url}: {error}")
            continue

        source_title = tag_text(rss.channel.title) or rss_url
        print(f"Source: {source_title}")

        try:
            feed_root = ET.fromstring(response.content)
        except Exception as error:
            print(f"Could not read XML from {rss_url}: {error}")
            continue

        feed_channel = feed_root.find("channel")
        if feed_channel is None:
            print(f"No channel found in {rss_url}")
            continue

        downloaded_sources += 1
        for item in feed_channel.findall("item"):
            source = item.find("source")
            if source is None:
                source = ET.SubElement(item, "source", url=rss_url)
                source.text = source_title

            channel.append(item)
            imported_items += 1

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"Unified RSS saved at {output_path}")
    print(f"Downloaded sources: {downloaded_sources}. RSS items: {imported_items}.")


def clean_text(value):
    if not value:
        return ""

    soup = BeautifulSoup(value, "html.parser")
    text = soup.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def child_text(item, tag_name):
    child = item.find(tag_name)
    return clean_text(child.text if child is not None else "")

def clean_url(url):
    if not url:
        return ""
    parsed = urlparse(url)
    # Reconstruye la URL sin query parameters (?...) ni fragmentos (#...)
    # Además, elimina la barra inclinada del final si existe y pasa todo a minúsculas
    path = parsed.path.rstrip('/')
    cleaned = urlunparse((parsed.scheme, parsed.netloc, path, '', '', ''))
    return cleaned.lower()

def parse_date(value):
    if not value:
        return timezone.now()

    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return timezone.now()

    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())

    return parsed


def parse_min_published_at(value):
    date_value = datetime.fromisoformat(value).date()
    return timezone.make_aware(
        datetime.combine(date_value, datetime.min.time()),
        timezone.get_current_timezone(),
    )


def first_image_url(item):
    enclosure = item.find("enclosure")
    if enclosure is not None and enclosure.attrib.get("type", "").startswith("image/"):
        return enclosure.attrib.get("url", "")

    for child in item:
        tag = child.tag.split("}", 1)[-1]
        if tag in {"content", "thumbnail"} and "url" in child.attrib:
            return child.attrib["url"]

    return ""


def item_source(item):
    source = item.find("source")
    if source is None:
        return "", ""

    return clean_text(source.text), source.attrib.get("url", "")


def content_hash(source_url, external_id, headline):
    raw = "|".join([source_url or "", external_id or "", headline or ""])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def default_translation(headline, content):
    return {
        "headline": headline,
        "subtitle": content[:220],
        "short_summary": content[:500] or headline,
        "beginner_summary": content[:900] or headline,
        "advanced_summary": content[:1200] or headline,
    }


def clamp_text(value, max_length):
    text = clean_text(str(value or ""))
    if len(text) <= max_length:
        return text

    return text[: max_length - 1].rstrip() + "..."


def clean_list(value, limit=8):
    if not isinstance(value, list):
        return []

    cleaned = []
    for item in value:
        text = clean_text(str(item)).strip("#")
        if text and text not in cleaned:
            cleaned.append(text[:40])

    return cleaned[:limit]


def detect_original_language(source_name, source_url, headline, content):
    text = f"{source_name} {source_url}".lower()
    polish_markers = ["puls biznesu", "pb.pl"]

    if any(marker in text for marker in polish_markers):
        return "pl"

    if re.search(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]", f"{headline} {content}"):
        return "pl"

    return "en"


def normalize_translations(value, headline, content):
    fallback = default_translation(headline, content)
    translations = value if isinstance(value, dict) else {}

    normalized = {}
    for locale in ("en", "pl"):
        locale_data = translations.get(locale) if isinstance(translations.get(locale), dict) else {}
        normalized[locale] = {
            "headline": clamp_text(locale_data.get("headline") or fallback["headline"], TEXT_LIMITS["headline"]),
            "subtitle": clamp_text(locale_data.get("subtitle") or fallback["subtitle"], TEXT_LIMITS["subtitle"]),
            "short_summary": clamp_text(locale_data.get("short_summary") or fallback["short_summary"], TEXT_LIMITS["short_summary"]),
            "beginner_summary": clamp_text(locale_data.get("beginner_summary") or fallback["beginner_summary"], TEXT_LIMITS["beginner_summary"]),
            "advanced_summary": clamp_text(locale_data.get("advanced_summary") or fallback["advanced_summary"], TEXT_LIMITS["advanced_summary"]),
        }

    return normalized


def original_only_translations(language, headline, content):
    return {
        language: default_translation(headline, content),
    }


def heuristic_classification(headline, content, source_name, source_url):
    text = f"{headline} {content} {source_name}".lower()

    crypto_terms = ["bitcoin", "btc", "ethereum", "eth", "crypto", "blockchain", "stablecoin"]
    forex_terms = ["forex", "eur/usd", "gbp", "usd/jpy", "currency", "dollar", "euro", "yen"]
    basics_terms = ["how to", "guide", "learn", "beginners", "education", "personal finance"]

    if any(term in text for term in crypto_terms):
        news_type = NewsArticle.NewsType.CRYPTO
    elif any(term in text for term in forex_terms):
        news_type = NewsArticle.NewsType.FOREX
    elif any(term in text for term in basics_terms):
        news_type = NewsArticle.NewsType.INVESTING_BASICS
    else:
        news_type = NewsArticle.NewsType.STOCK_MARKET

    difficulty = NewsArticle.Difficulty.INTERMEDIATE
    if any(term in text for term in basics_terms):
        difficulty = NewsArticle.Difficulty.BEGINNER
    elif any(term in text for term in ["derivatives", "options", "yield curve", "fomc", "basis points"]):
        difficulty = NewsArticle.Difficulty.ADVANCED

    tags = sorted({word.upper() for word in re.findall(r"\b[A-Z]{2,5}\b", f"{headline} {content}")})[:8]

    return {
        "translations": original_only_translations(
            detect_original_language(source_name, source_url, headline, content),
            headline,
            content,
        ),
        "difficulty": difficulty,
        "news_type": news_type,
        "importance_score": 50,
        "original_language": detect_original_language(source_name, source_url, headline, content),
        "tags": tags,
        "mentioned_assets": tags,
    }


def build_llm():
    model = os.getenv("NEWS_LLM_MODEL", "")

    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(model=model or "gemini-3.1-flash-lite", temperature=0)
    return llm.with_structured_output(
        NewsLLMOutput,
        method="json_schema",
        include_raw=True,
    )


def llm_classification(llm, data):
    prompt = LLM_PROMPT.format(**data)
    response = llm.invoke(prompt)
    #  EXTRACTOR DE TOKENS (Soporta OpenAI y Gemini dinámicamente)
    input_tokens = 0
    output_tokens = 0
    
    # Intentar formato estándar moderno de LangChain
    usage = getattr(response, "usage_metadata", None)
    if usage:
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
    else:
        # Fallback manual inspeccionando los metadatos crudos de la respuesta
        meta = getattr(response, "response_metadata", {})
        
        # Estructura típica de OpenAI
        token_usage = meta.get("token_usage", {})
        input_tokens = token_usage.get("prompt_tokens", 0)
        output_tokens = token_usage.get("completion_tokens", 0)
        
        # Estructura típica de Gemini si OpenAI devolvió vacío
        if not input_tokens and not output_tokens:
            gemini_usage = meta.get("usage_metadata", {})
            input_tokens = gemini_usage.get("prompt_token_count", 0)
            output_tokens = gemini_usage.get("candidates_token_count", 0)
            
    print(
        f"[Tokens] '{data['headline'][:35]}...' -> "
        f"Entrada: {input_tokens} | Salida: {output_tokens} | Total: {input_tokens + output_tokens}"
    )
    content = getattr(response, "content", response)

    if isinstance(content, list):
        content = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)

    content = str(content).strip()
    content = re.sub(r"^```(?:json)?|```$", "", content, flags=re.IGNORECASE | re.MULTILINE).strip()
    parsed = json.loads(content)

    parsed["translations"] = normalize_translations(
        parsed.get("translations"),
        data["headline"],
        data["content"],
    )
    if parsed.get("difficulty") not in ALLOWED_DIFFICULTIES:
        parsed["difficulty"] = NewsArticle.Difficulty.INTERMEDIATE

    if parsed.get("news_type") not in ALLOWED_NEWS_TYPES:
        parsed["news_type"] = NewsArticle.NewsType.STOCK_MARKET

    parsed["importance_score"] = max(0, min(100, int(parsed.get("importance_score", 50))))
    parsed["tags"] = clean_list(parsed.get("tags"), limit=8)
    parsed["mentioned_assets"] = clean_list(parsed.get("mentioned_assets"), limit=10)
    parsed["original_language"] = clamp_text(parsed.get("original_language", "unknown"), 10)
    return parsed


def llm_classification(llm, data):
    prompt = LLM_PROMPT.format(**data)
    response = llm.invoke(prompt)
    raw_response = response.get("raw") if isinstance(response, dict) else response
    parsed_response = response.get("parsed") if isinstance(response, dict) else None
    parsing_error = response.get("parsing_error") if isinstance(response, dict) else None

    if parsing_error:
        raise parsing_error

    input_tokens = 0
    output_tokens = 0

    usage = getattr(raw_response, "usage_metadata", None)
    if usage:
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
    else:
        meta = getattr(raw_response, "response_metadata", {})
        token_usage = meta.get("token_usage", {})
        input_tokens = token_usage.get("prompt_tokens", 0)
        output_tokens = token_usage.get("completion_tokens", 0)

        if not input_tokens and not output_tokens:
            gemini_usage = meta.get("usage_metadata", {})
            input_tokens = gemini_usage.get("prompt_token_count", 0)
            output_tokens = gemini_usage.get("candidates_token_count", 0)

    print(
        f"[TOKENS] '{data['headline'][:35]}...' -> "
        f"input={input_tokens} output={output_tokens} total={input_tokens + output_tokens}"
    )

    if parsed_response is not None:
        parsed = parsed_response.model_dump()
    else:
        content = getattr(raw_response, "content", raw_response)

        if isinstance(content, list):
            content = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)

        content = str(content).strip()
        content = re.sub(r"^```(?:json)?|```$", "", content, flags=re.IGNORECASE | re.MULTILINE).strip()
        parsed = json.loads(content)

    parsed["translations"] = normalize_translations(
        parsed.get("translations"),
        data["headline"],
        data["content"],
    )
    if parsed.get("difficulty") not in ALLOWED_DIFFICULTIES:
        parsed["difficulty"] = NewsArticle.Difficulty.INTERMEDIATE

    if parsed.get("news_type") not in ALLOWED_NEWS_TYPES:
        parsed["news_type"] = NewsArticle.NewsType.STOCK_MARKET

    parsed["importance_score"] = max(0, min(100, int(parsed.get("importance_score", 50))))
    parsed["tags"] = clean_list(parsed.get("tags"), limit=8)
    parsed["mentioned_assets"] = clean_list(parsed.get("mentioned_assets"), limit=10)
    parsed["original_language"] = clamp_text(parsed.get("original_language", "unknown"), 10)
    parsed["_token_usage"] = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }
    return parsed


def build_candidate_from_item(item, min_published_at, seen_hashes):
    headline = child_text(item, "title")
    raw_source_url = child_text(item, "link")
    source_url = clean_url(raw_source_url)[:500]
    description = child_text(item, "description")
    raw_guid = child_text(item, "guid")
    external_id = (clean_url(raw_guid) if raw_guid else source_url)[:255]
    source_name, rss_source_url = item_source(item)
    source_name = source_name or rss_source_url or "Unknown source"
    published_at = parse_date(child_text(item, "pubDate"))

    if not headline:
        return None, "invalid"

    if min_published_at and published_at < min_published_at:
        return None, "old"

    hash_basis = external_id or source_url or f"{source_name}|{headline}|{published_at.isoformat()}"
    article_hash = hashlib.sha256(hash_basis.encode("utf-8")).hexdigest()

    if article_hash in seen_hashes:
        return None, "duplicate_in_xml"

    seen_hashes.add(article_hash)

    duplicate_query = Q(content_hash=article_hash)
    if external_id:
        duplicate_query |= Q(external_id=external_id)
    if source_url:
        duplicate_query |= Q(source_url=source_url)

    if NewsArticle.objects.filter(duplicate_query).exists():
        return None, "existing"

    return {
        "article_hash": article_hash,
        "description": description,
        "external_id": external_id,
        "headline": headline,
        "item": item,
        "published_at": published_at,
        "rss_source_url": rss_source_url,
        "source_name": source_name,
        "source_url": source_url,
    }, "candidate"


def import_items(xml_path, use_llm=False, limit=None, min_published_at=None):
    tree = ET.parse(xml_path)
    items = tree.getroot().find("channel").findall("item")
    llm = build_llm() if use_llm else None
    if use_llm and llm is None:
        raise RuntimeError("Gemini LLM could not be initialized when using --llm.")
    if use_llm and llm is None:
        raise RuntimeError("NEWS_LLM_PROVIDER must be 'openai' or 'gemini' when using --llm.")

    created = 0
    existing = 0
    skipped = 0
    old_items = 0
    duplicate_in_xml = 0
    llm_candidates = 0
    llm_succeeded_count = 0
    llm_fallback_count = 0
    total_input_tokens = 0
    total_output_tokens = 0
    seen_hashes = set()
    candidates = []

    for item in items[:limit]:
        candidate, status = build_candidate_from_item(item, min_published_at, seen_hashes)

        if status == "invalid":
            skipped += 1
            continue
        if status == "old":
            old_items += 1
            continue
        if status == "duplicate_in_xml":
            duplicate_in_xml += 1
            continue
        if status == "existing":
            existing += 1
            continue

        candidates.append(candidate)

    scanned_items = len(items[:limit]) if limit else len(items)
    print(
        "Pre-LLM filtering summary. "
        f"RSS items scanned: {scanned_items}. "
        f"Existing skipped: {existing}. Old items skipped: {old_items}. "
        f"XML duplicates skipped: {duplicate_in_xml}. Invalid skipped: {skipped}. "
        f"New items to analyze/save: {len(candidates)}."
    )

    if use_llm and candidates:
        print(f"Starting Gemini analysis for {len(candidates)} new items.")

    for candidate in candidates:
        article_hash = candidate["article_hash"]
        description = candidate["description"]
        external_id = candidate["external_id"]
        headline = candidate["headline"]
        item = candidate["item"]
        published_at = candidate["published_at"]
        rss_source_url = candidate["rss_source_url"]
        source_name = candidate["source_name"]
        source_url = candidate["source_url"]

        base_data = {
            "source_name": source_name,
            "source_url": source_url,
            "headline": headline,
            "published_at": published_at.isoformat(),
            "content": description,
        }

        classification = heuristic_classification(headline, description, source_name, source_url)
        llm_succeeded = False
        llm_error = ""

        if llm is not None:
            llm_candidates += 1
            try:
                classification.update(llm_classification(llm, base_data))
                token_usage = classification.pop("_token_usage", {})
                total_input_tokens += token_usage.get("input_tokens", 0)
                total_output_tokens += token_usage.get("output_tokens", 0)
                llm_succeeded_count += 1
                llm_succeeded = True
            except Exception as error:
                llm_error = str(error)
                llm_fallback_count += 1
                print(f"LLM failed for '{headline}': {error}. Using heuristic fallback.")
            time.sleep(4.5)

        translations = (
            normalize_translations(classification.get("translations"), headline, description)
            if llm_succeeded
            else classification.get("translations", {})
        )
        default_locale = translations.get("en") or translations.get("pl") or default_translation(headline, description)

        NewsArticle.objects.create(
            content_hash=article_hash,
            source_url=source_url,
            source_name=source_name[:120],
            headline=default_locale["headline"][:255],
            subtitle=default_locale["subtitle"],
            image_url=first_image_url(item) or None,
            image_alt=default_locale["headline"][:255],
            image_source=source_name[:255],
            short_summary=default_locale["short_summary"],
            advanced_summary=default_locale["advanced_summary"],
            beginner_summary=default_locale["beginner_summary"],
            translations=translations,
            difficulty=classification["difficulty"],
            news_type=classification["news_type"],
            importance_score=classification["importance_score"],
            published_at=published_at,
            processed_at=timezone.now(),
            original_language=classification.get("original_language", "unknown")[:10],
            original_content=description,
            tags=classification.get("tags", []),
            mentioned_assets=classification.get("mentioned_assets", []),
            status=NewsArticle.Status.PUBLISHED,
            external_id=external_id[:255],
            ai_metadata={
                "rss_source_url": rss_source_url,
                "llm_provider": "gemini" if llm_succeeded else "",
                "llm_model": os.getenv("NEWS_LLM_MODEL", "gemini-3.1-flash-lite") if llm_succeeded else "",
                "llm_fallback": bool(llm is not None and not llm_succeeded),
                "llm_error": clamp_text(llm_error, 500) if llm_error else "",
                "translation_locales": list(translations.keys()),
            },
        )
        created += 1

    estimated_cost = (
        (total_input_tokens / 1_000_000) * GEMINI_FLASH_LITE_INPUT_USD_PER_1M
        + (total_output_tokens / 1_000_000) * GEMINI_FLASH_LITE_OUTPUT_USD_PER_1M
    )

    print(
        "Import finished. "
        f"Created: {created}. Existing skipped: {existing}. "
        f"Old items skipped: {old_items}. XML duplicates skipped: {duplicate_in_xml}. "
        f"Invalid skipped: {skipped}. "
        f"LLM calls attempted: {llm_candidates}. "
        f"LLM succeeded: {llm_succeeded_count}. LLM fallbacks: {llm_fallback_count}."
    )
    print(
        "LLM usage summary. "
        f"Input tokens: {total_input_tokens}. Output tokens: {total_output_tokens}. "
        f"Total tokens: {total_input_tokens + total_output_tokens}. "
        f"Estimated Gemini Flash-Lite cost: ${estimated_cost:.6f}."
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Downloads finance RSS feeds, builds a temporary unified XML, "
            "and imports only new items into content.NewsArticle."
        )
    )
    parser.add_argument("--xml", default=str(DEFAULT_XML_PATH), help="Temporary unified XML path.")
    parser.add_argument("--llm", action="store_true", help="Use Gemini to enrich new RSS items.")
    parser.add_argument("--limit", type=int, default=None, help="Limita el numero de noticias a importar.")
    parser.add_argument(
        "--min-published-at",
        default=os.getenv("NEWS_MIN_PUBLISHED_AT", DEFAULT_MIN_PUBLISHED_AT),
        help="Skip RSS items published before this YYYY-MM-DD date.",
    )
    parser.add_argument(
        "--from-existing-xml",
        action="store_true",
        help="Skip RSS download and import the XML already present at --xml.",
    )
    parser.add_argument(
        "--keep-xml",
        action="store_true",
        help="Do not delete the temporary XML after a successful import.",
    )
    args = parser.parse_args()

    xml_path = Path(args.xml)

    if not args.from_existing_xml:
        download_unified_rss(xml_path)

    min_published_at = parse_min_published_at(args.min_published_at)
    print(f"Minimum publication date: {args.min_published_at}")

    import_items(
        xml_path,
        use_llm=args.llm,
        limit=args.limit,
        min_published_at=min_published_at,
    )

    if not args.keep_xml and xml_path.exists():
        xml_path.unlink()
        print(f"Temporary XML deleted: {xml_path}")


if __name__ == "__main__":
    main()
