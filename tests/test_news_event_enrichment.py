from datetime import datetime, timezone

from backend.app.providers.news import NewsEvent, NewsSource
from backend.app.providers.news_event_enrichment import (
    attach_evidence_summary,
)
from backend.app.providers.news_relationship import (
    apply_source_relationship,
    create_source_relationship,
)


now = datetime.now(timezone.utc)


def make_source(name):
    source = NewsSource(
        name=name,
        source_type="GLOBAL_MEDIA",
        source_tier=3,
        country="GLOBAL",
    )

    relationship = create_source_relationship(
        source_name=name,
        source_type="GLOBAL_MEDIA",
    )

    apply_source_relationship(
        source,
        relationship,
    )

    return source


event = NewsEvent(
    symbol="BBCA",
    canonical_title="Test Event",
    first_published_at=now,
    first_detected_at=now,
    sources=[
        make_source("Reuters"),
        make_source("Bloomberg"),
    ],
    source_count=2,
)


attach_evidence_summary(event)


print(
    "STATUS =>",
    event.validation_status,
)

print(
    "EVIDENCE STATUS =>",
    event.evidence_summary.status,
)

print(
    "EVIDENCE STRENGTH =>",
    event.evidence_summary.evidence_strength,
)

print(
    "INDEPENDENT =>",
    event.evidence_summary.independent_source_count,
)

print(
    "OFFICIAL =>",
    event.evidence_summary.official_source_count,
)

print(
    "CONTRADICTING =>",
    event.evidence_summary.contradicting_source_count,
)
