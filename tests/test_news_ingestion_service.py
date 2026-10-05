from datetime import datetime, timezone

from backend.app.providers.news import NewsItem
from backend.app.services.news_ingestion_service import (
    NewsIngestionService,
)


class FakeProvider:
    def __init__(self, items):
        self.items = items

    def get_news(self, symbol=None, limit=20):
        return self.items[:limit]


def test_ingestion_matches_company_name():
    now = datetime.now(timezone.utc)

    provider = FakeProvider(
        [
            NewsItem(
                symbol=None,
                title="Bank Central Asia mencatat kinerja positif",
                source="CNBC-Indonesia",
                published_at=now,
                detected_at=now,
                url="https://example.com/bbca",
            )
        ]
    )

    stocks = [
        (1, "BBCA", "Bank Central Asia Tbk"),
        (2, "BBRI", "Bank Rakyat Indonesia (Persero) Tbk"),
    ]

    service = NewsIngestionService(
        provider=provider,
        stocks=stocks,
    )

    result = service.ingest()

    assert result == 1


def test_ingestion_merges_same_event_from_two_sources():
    now = datetime.now(timezone.utc)

    provider = FakeProvider(
        [
            NewsItem(
                symbol=None,
                title="BBCA mencatat kinerja positif",
                source="CNBC-Indonesia",
                published_at=now,
                detected_at=now,
                url="https://example.com/cnbc-bbca",
            ),
            NewsItem(
                symbol=None,
                title="BBCA mencatat kinerja positif",
                source="Reuters",
                published_at=now,
                detected_at=now,
                url="https://example.com/reuters-bbca",
            ),
        ]
    )

    stocks = [
        (1, "BBCA", "Bank Central Asia Tbk"),
    ]

    service = NewsIngestionService(
        provider=provider,
        stocks=stocks,
    )

    result = service.ingest()

    assert result == 1
