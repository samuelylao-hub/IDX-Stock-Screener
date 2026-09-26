import re

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol


@dataclass
class NewsSource:
    name: str
    source_type: str
    source_tier: int
    country: str
    url: str | None = None
    published_at: datetime | None = None
    detected_at: datetime | None = None
    is_primary: bool = False

    source_role: str | None = None
    derived_from: str | None = None
    relationship_note: str | None = None


@dataclass
class NewsItem:
    symbol: str | None
    title: str
    source: str
    published_at: datetime
    detected_at: datetime
    url: str | None = None
    category: str | None = None
    importance: str | None = None
    source_tier: int | None = None
    validation_status: str | None = None


@dataclass
class NewsEvent:
    symbol: str | None
    canonical_title: str
    first_published_at: datetime
    first_detected_at: datetime
    importance: str | None = None
    validation_status: str | None = None
    source_count: int = 0
    sources: list[NewsSource] | None = None


def normalize_news_title(title: str) -> str:
    normalized = title.casefold()
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def classify_news_source(source_name: str) -> NewsSource:
    name = source_name.casefold().strip()

    if name in {
        "idx",
        "bei",
        "bursa efek indonesia",
        "ojk",
        "otoritas jasa keuangan",
        "ksei",
        "kustodian sentral efek indonesia",
    }:
        return NewsSource(
            name=source_name,
            source_type="REGULATOR",
            source_tier=1,
            country="ID",
            is_primary=True,
        )

    if name in {
        "company",
        "company ir",
        "investor relations",
        "official company",
    }:
        return NewsSource(
            name=source_name,
            source_type="COMPANY",
            source_tier=1,
            country="ID",
            is_primary=True,
        )

    if name in {
        "reuters",
        "bloomberg",
        "financial times",
        "wall street journal",
        "wsj",
    }:
        return NewsSource(
            name=source_name,
            source_type="GLOBAL_MEDIA",
            source_tier=3,
            country="GLOBAL",
            is_primary=False,
        )

    if name in {
        "kontan",
        "bisnis indonesia",
        "cnbc indonesia",
        "bloomberg technoz",
    }:
        return NewsSource(
            name=source_name,
            source_type="INDONESIA_MEDIA",
            source_tier=3,
            country="ID",
            is_primary=False,
        )

    return NewsSource(
        name=source_name,
        source_type="UNKNOWN",
        source_tier=5,
        country="UNKNOWN",
        is_primary=False,
    )


def is_duplicate_news(
    news_item: NewsItem,
    existing_event: NewsEvent,
    window_hours: int = 24,
) -> bool:
    if news_item.symbol != existing_event.symbol:
        return False

    normalized_news_title = normalize_news_title(
        news_item.title
    )

    normalized_event_title = normalize_news_title(
        existing_event.canonical_title
    )

    if normalized_news_title != normalized_event_title:
        return False

    time_difference = abs(
        news_item.published_at
        - existing_event.first_published_at
    )

    return time_difference <= timedelta(hours=window_hours)


def create_news_event(news_item: NewsItem) -> NewsEvent:
    source = classify_news_source(news_item.source)

    source.url = news_item.url
    source.published_at = news_item.published_at
    source.detected_at = news_item.detected_at

    return NewsEvent(
        symbol=news_item.symbol,
        canonical_title=news_item.title,
        first_published_at=news_item.published_at,
        first_detected_at=news_item.detected_at,
        importance=news_item.importance,
        validation_status=news_item.validation_status,
        source_count=1,
        sources=[source],
    )


def merge_news_into_event(
    news_item: NewsItem,
    existing_event: NewsEvent,
) -> NewsEvent:
    if not is_duplicate_news(news_item, existing_event):
        raise ValueError(
            "News item bukan duplicate dari event yang diberikan."
        )

    if existing_event.sources is None:
        existing_event.sources = []

    source = classify_news_source(news_item.source)

    source.url = news_item.url
    source.published_at = news_item.published_at
    source.detected_at = news_item.detected_at

    existing_event.sources.append(source)
    existing_event.source_count = len(existing_event.sources)

    return existing_event


class NewsProvider(Protocol):
    @property
    def name(self) -> str:
        ...

    def is_available(self) -> bool:
        ...

    def get_news(
        self,
        symbol: str | None = None,
        limit: int = 20,
    ) -> list[NewsItem]:
        ...