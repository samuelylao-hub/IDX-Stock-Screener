from datetime import datetime, timezone
from unittest.mock import Mock

from backend.app.providers.news import NewsItem
from backend.app.services import news_ingestion_service as module


def test_ingestion_persists_multiple_articles_without_real_database(
    monkeypatch,
):
    now = datetime(2026, 10, 21, 3, 40, tzinfo=timezone.utc)

    items = [
        NewsItem(
            symbol=None,
            title="BBCA mencatat kinerja positif",
            source="CNBC-Indonesia",
            published_at=now,
            detected_at=now,
            url="https://example.com/bbca",
            description="Bank Central Asia",
        ),
        NewsItem(
            symbol=None,
            title="BBRI mengumumkan perkembangan bisnis",
            source="Reuters",
            published_at=now,
            detected_at=now,
            url="https://example.com/bbri",
            description="Bank Rakyat Indonesia",
        ),
    ]

    stocks = [
        (1, "BBCA", "Bank Central Asia Tbk"),
        (2, "BBRI", "Bank Rakyat Indonesia (Persero) Tbk"),
    ]

    connection = object()
    saved_events = []
    saved_sources = []

    monkeypatch.setattr(
        module,
        "save_news_event",
        lambda conn, event: (
            saved_events.append((conn, event)) or len(saved_events)
        ),
    )
    monkeypatch.setattr(
        module,
        "save_news_event_source",
        lambda conn, event_id, source: saved_sources.append(
            (conn, event_id, source)
        ),
    )
    monkeypatch.setattr(
        module,
        "create_source_relationship",
        lambda **kwargs: Mock(),
    )
    monkeypatch.setattr(
        module,
        "apply_source_relationship",
        lambda source, relationship: None,
    )
    monkeypatch.setattr(
        module,
        "attach_evidence_summary",
        lambda event: None,
    )

    provider = Mock()
    provider.get_news.return_value = items

    service = module.NewsIngestionService(
        provider=provider,
        stocks=stocks,
        connection=connection,
    )

    result = service.ingest(limit=100)

    assert result == 2
    assert len(saved_events) == 2
    assert all(conn is connection for conn, _ in saved_events)
    assert len(saved_sources) >= 2
    provider.get_news.assert_called_once_with(limit=100)
