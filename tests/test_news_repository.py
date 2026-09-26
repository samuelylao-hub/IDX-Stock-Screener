from datetime import datetime, timezone

from backend.app.database import get_connection
from backend.app.providers.news import NewsEvent, NewsSource
from backend.app.providers.news_event_enrichment import attach_evidence_summary
from backend.app.providers.news_repository import save_news_event


now = datetime.now(timezone.utc)

event = NewsEvent(
    symbol="BBCA",
    canonical_title="Test News Event Repository",
    first_published_at=now,
    first_detected_at=now,
    importance="MEDIUM",
    sources=[
        NewsSource(
            name="Reuters",
            source_type="GLOBAL_MEDIA",
            source_tier=3,
            country="GLOBAL",
        ),
        NewsSource(
            name="Bloomberg",
            source_type="GLOBAL_MEDIA",
            source_tier=3,
            country="GLOBAL",
        ),
    ],
    source_count=2,
)

attach_evidence_summary(event)

connection = get_connection()

try:
    event_id = save_news_event(
        connection,
        event,
    )

    print("NEWS EVENT SAVED")
    print("ID =>", event_id)
    print("STATUS =>", event.validation_status)
    print(
        "EVIDENCE =>",
        event.evidence_summary.evidence_strength,
    )
finally:
    connection.close()
