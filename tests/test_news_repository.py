from datetime import datetime, timezone

from backend.app.database import get_connection
from backend.app.providers.news import (
    NewsItem,
    create_news_event,
)
from backend.app.providers.news_event_enrichment import (
    attach_evidence_summary,
)
from backend.app.providers.news_repository import save_news_event


now = datetime.now(timezone.utc)

item = NewsItem(
    symbol="BBCA",
    title="Test News Event Repository",
    source="Reuters",
    published_at=now,
    detected_at=now,
    importance="MEDIUM",
)

event = create_news_event(item)

attach_evidence_summary(event)

connection = get_connection()

try:
    event_id = save_news_event(
        connection,
        event,
    )

    print("NEWS EVENT SAVED")
    print("ID =>", event_id)
    print("EVENT KEY =>", event.event_key)
    print("STATUS =>", event.validation_status)
    print(
        "EVIDENCE =>",
        event.evidence_summary.evidence_strength,
    )
finally:
    connection.close()