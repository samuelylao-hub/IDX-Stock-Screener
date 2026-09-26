from datetime import datetime, timezone

from backend.app.providers.news import NewsEvent, NewsSource
from backend.app.providers.news_relationship import (
    apply_source_relationship,
    create_source_relationship,
)
from backend.app.providers.news_validation import validate_news_event


now = datetime.now(timezone.utc)


def make_source(
    name,
    source_type,
    country,
    is_primary=False,
    derived_from=None,
):
    source = NewsSource(
        name=name,
        source_type=source_type,
        source_tier=3,
        country=country,
        is_primary=is_primary,
    )

    relationship = create_source_relationship(
        source_name=name,
        source_type=source_type,
        is_primary=is_primary,
        derived_from=derived_from,
    )

    apply_source_relationship(
        source,
        relationship,
    )

    return source


def make_event(sources):
    return NewsEvent(
        symbol="BBCA",
        canonical_title="Test Event",
        first_published_at=now,
        first_detected_at=now,
        sources=sources,
        source_count=len(sources),
    )


def run_test(name, sources):
    event = make_event(sources)

    result = validate_news_event(event)

    print(
        name,
        "=>",
        result.status,
        "| independent=",
        result.independent_source_count,
        "| official=",
        result.official_source_count,
        "|",
        result.reason,
    )


if __name__ == "__main__":

    run_test(
        "ONE_REUTERS",
        [
            make_source(
                "Reuters",
                "GLOBAL_MEDIA",
                "GLOBAL",
            )
        ],
    )

    run_test(
        "REUTERS_PLUS_KONTAN_DERIVED",
        [
            make_source(
                "Reuters",
                "GLOBAL_MEDIA",
                "GLOBAL",
            ),
            make_source(
                "Kontan",
                "INDONESIA_MEDIA",
                "ID",
                derived_from="Reuters",
            ),
        ],
    )

    run_test(
        "REUTERS_PLUS_INDEPENDENT",
        [
            make_source(
                "Reuters",
                "GLOBAL_MEDIA",
                "GLOBAL",
            ),
            make_source(
                "Bloomberg",
                "GLOBAL_MEDIA",
                "GLOBAL",
            ),
        ],
    )

    run_test(
        "IDX_PLUS_REUTERS",
        [
            make_source(
                "IDX",
                "REGULATOR",
                "ID",
                is_primary=True,
            ),
            make_source(
                "Reuters",
                "GLOBAL_MEDIA",
                "GLOBAL",
            ),
        ],
    )
