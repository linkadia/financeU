from datetime import datetime, timedelta, timezone as dt_timezone
import xml.etree.ElementTree as ET

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from scripts.import_rss_news import build_candidate_from_item
from .models import NewsArticle


def create_article(headline, published_at):
    return NewsArticle.objects.create(
        source_name="FinanU",
        headline=headline,
        short_summary="Short summary",
        advanced_summary="Advanced summary",
        beginner_summary="Beginner summary",
        translations={
            "en": {
                "headline": headline,
                "subtitle": "",
                "short_summary": "Short summary",
                "advanced_summary": "Advanced summary",
                "beginner_summary": "Beginner summary",
            },
            "pl": {
                "headline": headline,
                "subtitle": "",
                "short_summary": "Short summary",
                "advanced_summary": "Advanced summary",
                "beginner_summary": "Beginner summary",
            },
        },
        difficulty=NewsArticle.Difficulty.BEGINNER,
        news_type=NewsArticle.NewsType.CRYPTO,
        importance_score=50,
        published_at=published_at,
        processed_at=timezone.now(),
        original_language="en",
        status=NewsArticle.Status.PUBLISHED,
        content_hash=headline.lower().replace(" ", "-"),
    )


class NewsArticleViewSetTests(APITestCase):
    def test_news_defaults_to_last_24_hours(self):
        create_article("Fresh story", timezone.now() - timedelta(hours=2))
        create_article("Older story", timezone.now() - timedelta(days=2))

        response = self.client.get("/api/content/news/")

        self.assertEqual(response.status_code, 200)
        headlines = [item["headline"] for item in response.data]
        self.assertEqual(headlines, ["Fresh story"])

    def test_news_can_include_all_dates(self):
        create_article("Fresh story", timezone.now() - timedelta(hours=2))
        create_article("Older story", timezone.now() - timedelta(days=2))

        response = self.client.get("/api/content/news/", {"date_range": "all"})

        self.assertEqual(response.status_code, 200)
        headlines = [item["headline"] for item in response.data]
        self.assertEqual(headlines, ["Fresh story", "Older story"])


class RssDuplicateDetectionTests(TestCase):
    def rss_item(self, headline, source_name, published_at, url, guid=None):
        item = ET.Element("item")
        ET.SubElement(item, "title").text = headline
        ET.SubElement(item, "link").text = url
        ET.SubElement(item, "description").text = "Market summary"
        ET.SubElement(item, "pubDate").text = published_at
        source = ET.SubElement(item, "source", url="https://example.com/feed")
        source.text = source_name
        if guid:
            ET.SubElement(item, "guid").text = guid
        return item

    def create_existing_article(self, **overrides):
        published_at = datetime(2025, 2, 7, 20, 26, tzinfo=dt_timezone.utc)
        defaults = {
            "source_name": "MarketWatch.com - MarketPulse",
            "headline": "Consumer credit growth soars in December",
            "short_summary": "Short summary",
            "advanced_summary": "Advanced summary",
            "beginner_summary": "Beginner summary",
            "translations": {},
            "difficulty": NewsArticle.Difficulty.INTERMEDIATE,
            "news_type": NewsArticle.NewsType.STOCK_MARKET,
            "importance_score": 50,
            "published_at": published_at,
            "processed_at": timezone.now(),
            "original_language": "en",
            "status": NewsArticle.Status.PUBLISHED,
            "content_hash": "existing-hash",
            "source_url": "https://www.marketwatch.com/story/consumer-credit-growth-soars-in-december-d405d18e?mod=mw_rss_marketpulse",
            "external_id": "WP-MKTW-0003973830",
        }
        defaults.update(overrides)
        return NewsArticle.objects.create(**defaults)

    def test_duplicate_in_xml_uses_title_source_and_publication_date(self):
        seen_hashes = set()
        seen_identity_keys = set()
        published_at = "Fri, 07 Feb 2025 20:26:00 GMT"
        first = self.rss_item(
            "Consumer credit growth soars in December",
            "MarketWatch.com - MarketPulse",
            published_at,
            "https://www.marketwatch.com/story/consumer-credit-growth-soars-in-december-d405d18e",
            guid="wp-mktw-0003973830",
        )
        second = self.rss_item(
            "  Consumer   credit growth soars in December  ",
            "marketwatch.com - marketpulse",
            published_at,
            "https://www.marketwatch.com/story/consumer-credit-growth-soars-in-december-d405d18e-copy",
            guid="wp-mktw-0003973830-copy",
        )

        candidate, status = build_candidate_from_item(first, None, seen_hashes, seen_identity_keys)
        duplicate, duplicate_status = build_candidate_from_item(second, None, seen_hashes, seen_identity_keys)

        self.assertIsNotNone(candidate)
        self.assertEqual(status, "candidate")
        self.assertIsNone(duplicate)
        self.assertEqual(duplicate_status, "duplicate_in_xml")

    def test_existing_duplicate_matches_external_id_case_insensitively(self):
        self.create_existing_article()
        item = self.rss_item(
            "Different rendered headline",
            "MarketWatch.com - MarketPulse",
            "Fri, 07 Feb 2025 20:26:00 GMT",
            "https://www.marketwatch.com/story/consumer-credit-growth-soars-in-december-d405d18e",
            guid="wp-mktw-0003973830",
        )

        candidate, status = build_candidate_from_item(item, None, set(), set())

        self.assertIsNone(candidate)
        self.assertEqual(status, "existing")
