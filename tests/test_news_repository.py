from datetime import datetime, timezone

from backend.app.database import get_connection
from backend.app.providers.news import (
    NewsItem,
    create_news_event,
)
from backend.app.providers.news_event_enrichment import (
    attach_evidence_summary,
)
from backend.app.providers.news_relationship import (
    apply_source_relationship,
    create_source_relationship,
)
from backend.app.providers.news_repository import (
    save_news_event,
    save_news_event_source,
)


now = datetime.now(timezone.utc)

item = NewsItem(
    symbol="BBCA",
    title="Test News Event Source Audit",
    source="Reuters",
    published_at=now,
    detected_at=now,
    url="https://example.com/test-news-event-source-audit",
    importance="MEDIUM",
)

event = create_news_event(item)

source = event.sources[0]

relationship = create_source_relationship(
    source_name=source.name,
    source_type=source.source_type,
    is_primary=source.is_primary,
    derived_from=source.derived_from,
)

apply_source_relationship(
    source,
    relationship,
)

attach_evidence_summary(event)

connection = get_connection()

try:
    event_id = save_news_event(
        connection,
        event,
    )

    source_id = save_news_event_source(
        connection,
        event_id,
        source,
    )

    print("NEWS EVENT SAVED")
    print("EVENT ID =>", event_id)
    print("EVENT KEY =>", event.event_key)

    print("NEWS SOURCE SAVED")
    print("SOURCE ID =>", source_id)
    print("SOURCE =>", source.name)
    print("URL =>", source.url)
    print("ROLE =>", source.source_role)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                news_event_id,
                source_name,
                source_type,
                source_tier,
                country,
                url,
                source_role,
                derived_from
            FROM news_event_sources
            WHERE id = %s
            """,
            (source_id,),
        )

        row = cursor.fetchone()

    print("SOURCE DB ROW =>", row)

finally:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM news_events
            WHERE event_key = %s
            """,
            (event.event_key,),
        )

    connection.commit()
    connection.close()

    print("TEST DATA CLEANED")