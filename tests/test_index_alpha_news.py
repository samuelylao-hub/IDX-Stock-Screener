from datetime import datetime, timezone

from backend.app.providers.index_alpha_news import (
    IndexAlphaNewsProvider,
)


def test_index_alpha_news_provider_parses_response(monkeypatch):
    payload = {
        "success": True,
        "data": {
            "CNBC-Indonesia": [
                {
                    "source": "CNBC-Indonesia",
                    "title": "BBCA Catat Kinerja Positif",
                    "link": "https://example.com/bbca",
                    "published_date": "2026-10-05T11:30:17Z",
                },
            ]
        },
    }

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return payload

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "backend.app.providers.index_alpha_news.requests.get",
        fake_get,
    )

    provider = IndexAlphaNewsProvider(
        api_key="test-key"
    )

    items = provider.get_news(limit=10)

    assert len(items) == 1
    assert items[0].source == "CNBC-Indonesia"
    assert items[0].title == "BBCA Catat Kinerja Positif"
    assert items[0].url == "https://example.com/bbca"
    assert items[0].published_at == datetime(
        2026,
        10,
        5,
        11,
        30,
        17,
        tzinfo=timezone.utc,
    )


def test_index_alpha_news_provider_filters_symbol(
    monkeypatch,
):
    payload = {
        "success": True,
        "data": {
            "CNBC-Indonesia": [
                {
                    "source": "CNBC-Indonesia",
                    "title": "BBCA Catat Kinerja Positif",
                    "link": "https://example.com/bbca",
                    "published_date": "2026-10-05T11:30:17Z",
                },
                {
                    "source": "CNBC-Indonesia",
                    "title": "BBRI Terus Menguat",
                    "link": "https://example.com/bbri",
                    "published_date": "2026-10-05T11:20:17Z",
                },
            ]
        },
    }

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return payload

    monkeypatch.setattr(
        "backend.app.providers.index_alpha_news.requests.get",
        lambda *args, **kwargs: FakeResponse(),
    )

    provider = IndexAlphaNewsProvider(
        api_key="test-key"
    )

    items = provider.get_news(
        symbol="BBCA",
        limit=10,
    )

    assert len(items) == 1
    assert items[0].title == "BBCA Catat Kinerja Positif"


def test_index_alpha_news_provider_uses_cache(
    monkeypatch,
):
    payload = {
        "success": True,
        "data": {
            "CNBC-Indonesia": [
                {
                    "source": "CNBC-Indonesia",
                    "title": "BBCA News",
                    "link": "https://example.com/bbca",
                    "published_date": "2026-10-05T11:30:17Z",
                },
            ]
        },
    }

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return payload

    calls = {"count": 0}

    def fake_get(*args, **kwargs):
        calls["count"] += 1
        return FakeResponse()

    monkeypatch.setattr(
        "backend.app.providers.index_alpha_news.requests.get",
        fake_get,
    )

    provider = IndexAlphaNewsProvider(
        api_key="test-key"
    )

    provider.get_news()
    provider.get_news()
    provider.get_news(symbol="BBCA")

    assert calls["count"] == 1
